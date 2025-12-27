import streamlit as st
from PIL import Image, ImageDraw
import time
import random
import datetime
import numpy as np
from gtts import gTTS
import io
import os
import json
import hashlib
from utils.ai_brain import predict_disease

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Leaf Doctor", page_icon="🌿", layout="wide")

# --- 2. DATABASE & AUTH SYSTEM ---
USERS_FILE = "users.json"
HISTORY_FILE = "history.json"

def load_data(file, default_data):
    if os.path.exists(file):
        try:
            with open(file, "r") as f:
                return json.load(f)
        except:
            return default_data
    return default_data

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

users_db = load_data(USERS_FILE, {})
history_db = load_data(HISTORY_FILE, {})

# --- 3. SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = None
# We need an internal page state for the Home/Predict flow
if 'internal_page' not in st.session_state: st.session_state.internal_page = 'home'
if 'selected_crop' not in st.session_state: st.session_state.selected_crop = None
if 'dark_mode' not in st.session_state: st.session_state.dark_mode = True
if 'voice_lang' not in st.session_state: st.session_state.voice_lang = 'English'

# --- 4. THEME ---
if st.session_state.dark_mode:
    app_bg, sidebar_bg, card_bg, text_col, btn_bg = "#0e1117", "#262730", "#1E1E1E", "#FAFAFA", "#2b2b2b"
else:
    app_bg, sidebar_bg, card_bg, text_col, btn_bg = "#FFFFFF", "#F0F2F6", "#F9F9F9", "#000000", "#E0E0E0"

st.markdown(f"""
<style>
    .stApp {{ background-color: {app_bg}; color: {text_col}; }}
    [data-testid="stSidebar"] {{ background-color: {sidebar_bg}; }}
    .stButton>button {{ width: 100%; border-radius: 8px; height: 3em; background-color: {btn_bg}; color: {text_col}; border: 1px solid #4CAF50; }}
    div[data-testid="stVerticalBlockBorderWrapper"] {{ background-color: {card_bg}; border-radius: 10px; padding: 15px; border: 1px solid #333; }}
    h1, h2, h3, h4, h5, h6, p, label {{ color: {text_col} !important; }}
</style>
""", unsafe_allow_html=True)

# --- 5. KNOWLEDGE BASE ---
ALLOWED_CLASSES = {
    "Apple": ["apple_black_rot", "apple_healthy", "apple_scab"],
    "Corn": ["corn_common_rust", "corn_healthy", "corn_leaf_blight"],
    "Potato": ["potato_early_blight", "potato_healthy", "potato_late_blight"]
}

URDU_MESSAGES = {
    "Apple Black Rot": "Aap kay seb kay poday ko Black Rot ki beemari hai. Iska jald ilaaj karein.",
    "Apple Healthy": "Mubarak ho! Aap ka seb ka poda bilkul sehat mand hai.",
    "Apple Scab": "Khuddara tawajjo dein, aap kay poday main Scab fungus hai.",
    "Corn Common Rust": "Makayi kay poday main Rust ki beemari payi gayi hai.",
    "Corn Healthy": "Aap ki Makayi ki fasal bilkul theek hai.",
    "Corn Leaf Blight": "Ye Leaf Blight hai. Is say pattay sookh saktay hain.",
    "Potato Early Blight": "Aaloo kay poday main Early Blight kay asraat hain.",
    "Potato Healthy": "Behtareen! Aap ka Aaloo ka poda sehat mand hai.",
    "Potato Late Blight": "Ye Late Blight hai. Fasal ko bachaanay kay liye fori iqdaam karein."
}

KNOWLEDGE_BASE = {
    "Apple Black Rot": { "disease_name": "Apple Black Rot", "description": "Fungal disease causing purple spots and rotting fruit.", "treatment": "Prune dead branches, use Captan or Sulfur." },
    "Apple Healthy": { "disease_name": "Healthy Apple Leaf", "description": "Vibrant green leaves, no lesions.", "treatment": "Regular water/fertilizer." },
    "Apple Scab": { "disease_name": "Apple Scab", "description": "Olive-green to black velvety spots.", "treatment": "Remove fallen leaves, apply fungicides." },
    "Corn Common Rust": { "disease_name": "Corn Common Rust", "description": "Cinnamon-brown pustules.", "treatment": "Resistant hybrids, fungicides." },
    "Corn Healthy": { "disease_name": "Healthy Corn Plant", "description": "No discoloration or pustules.", "treatment": "Proper irrigation/nitrogen." },
    "Corn Leaf Blight": { "disease_name": "Northern Corn Leaf Blight", "description": "Large, cigar-shaped grey-green lesions.", "treatment": "Crop rotation, resistant varieties." },
    "Potato Early Blight": { "disease_name": "Potato Early Blight", "description": "Target-shaped bullseye spots.", "treatment": "Improve air circulation, copper fungicides." },
    "Potato Healthy": { "disease_name": "Healthy Potato Plant", "description": "Dark green, firm leaves.", "treatment": "Keep soil moist but drained." },
    "Potato Late Blight": { "disease_name": "Potato Late Blight", "description": "Water-soaked spots turning black.", "treatment": "Remove infected plants immediately." }
}
DARAZ_LINK = "https://www.daraz.pk/products/80-250-i161020707-s1327886846.html"

# --- 6. FUNCTIONS ---
def heavy_duty_scan(image_placeholder, graph_placeholder, original_img):
    img = original_img.copy().convert("RGBA")
    width, height = img.size
    if width > 500:
        ratio = 500 / width
        img = img.resize((500, int(height * ratio)))
        width, height = img.size
    step_size = int(height / 10) 
    for i in range(0, height + step_size, step_size):
        frame = img.copy()
        draw = ImageDraw.Draw(frame)
        scan_y = i if i < height else height - 1
        draw.line([(0, scan_y), (width, scan_y)], fill=(0, 255, 0, 200), width=5)
        image_placeholder.image(frame, caption="🔍 ANALYZING...", use_container_width=True)
        with graph_placeholder.container():
            g1, g2 = st.columns(2)
            g1.line_chart([random.randint(10, 100) for _ in range(20)], height=100)
            g2.progress(min(i / height, 1.0))
        time.sleep(0.02)

def play_audio(disease_name):
    try:
        lang = 'ur' if st.session_state.voice_lang == 'Urdu' else 'en'
        if lang == 'ur':
            text = URDU_MESSAGES.get(disease_name, "Beemari ki tashkhees ho gayi hai.")
        else:
            text = f"Alert. {disease_name} detected."
        tts = gTTS(text=text, lang=lang)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        st.audio(buf, format='audio/mp3', start_time=0)
    except: pass

def go_home():
    st.session_state.internal_page = 'home'
    st.session_state.selected_crop = None

def go_predict(crop_name):
    st.session_state.internal_page = 'predict'
    st.session_state.selected_crop = crop_name

# --- 7. LOGIN SCREEN ---
def login_screen():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🌿 Leaf Doctor")
        st.subheader("Authentication")
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        with tab1:
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("🚀 Login", type="primary"):
                enc_pass = hash_password(password)
                if username in users_db and users_db[username]['password'] == enc_pass:
                    st.session_state.logged_in = True
                    st.session_state.user = username
                    st.toast("Welcome back!", icon="✅")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")
        with tab2:
            new_user = st.text_input("Choose Username", key="new_user")
            new_pass = st.text_input("Choose Password", type="password", key="new_pass")
            if st.button("✨ Create Account"):
                if new_user in users_db:
                    st.error("User already exists!")
                elif len(new_pass) < 4:
                    st.error("Password too short.")
                else:
                    users_db[new_user] = {
                        "password": hash_password(new_pass),
                        "joined": str(datetime.date.today())
                    }
                    save_data(USERS_FILE, users_db)
                    st.success("Account Created! Please Login.")

# --- 8. MAIN APPLICATION ---
def main_app():
    # SIDEBAR
    with st.sidebar:
        st.write(f"👤 **{st.session_state.user}**")
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.internal_page = 'home' # Reset on logout
            st.rerun()
        st.divider()
        
        # [RESTORED] Emojis in Navigation
        menu = st.radio("Navigation", ["🏠 Home", "📜 My History", "⚙️ Settings"])
        
        st.divider()
        with st.expander("🌱 Tips for Gardening"):
            st.markdown("""
            * **Watering:** Water early in the morning.
            * **Soil:** Ensure good drainage.
            * **Sunlight:** At least 6 hours direct sun.
            """)
        with st.expander("🎯 About Us"):
            st.write("Bridging AI & Agriculture. Empowering farmers with instant diagnostics.")
        with st.expander("📖 Our Story"):
            st.write("Built by students of **Iqra University North Campus** to tackle agricultural challenges using MobileNet & Flutter.")

        st.divider()
        st.write("📱 **Mobile App**")
        if os.path.exists("app-release.apk"):
            with open("app-release.apk", "rb") as f:
                st.download_button("📥 Download APK", f, "LeafDoctor.apk", "application/vnd.android.package-archive")

    # --- HOME TAB LOGIC ---
    if menu == "🏠 Home":
        
        # A. CROP SELECTION SCREEN (The "Big Cards" View)
        if st.session_state.internal_page == 'home':
            st.title("🌿 Leaf Diagnostics")
            st.subheader("① Select Your Plant System")
            
            col1, col2, col3 = st.columns(3)
            crops = [("🍎", "Apple"), ("🌽", "Corn"), ("🥔", "Potato")]
            
            # [RESTORED] Original Card Logic with HTML
            for idx, (emoji, name) in enumerate(crops):
                with [col1, col2, col3][idx]:
                    with st.container(border=True):
                        st.markdown(f"<h1 style='text-align:center;'>{emoji}</h1><h3 style='text-align:center;'>{name}</h3>", unsafe_allow_html=True)
                        # When clicked, update state to 'predict' so the view changes
                        if st.button(f"Select {name}", key=f"btn_{name}"):
                            go_predict(name)
                            st.rerun()

            st.markdown("---")
            st.markdown("""
                <div style='text-align: center; color: gray; padding: 20px;'>
                    <h3>🚀 More crops coming soon...</h3>
                    <p>We are currently training models for Tomato, Grape, and Wheat.</p>
                </div>
            """, unsafe_allow_html=True)

        # B. PREDICTION SCREEN (Only shown after clicking a card)
        elif st.session_state.internal_page == 'predict':
            col_back, col_title = st.columns([1, 8])
            with col_back:
                if st.button("← Back"):
                    go_home()
                    st.rerun()
            with col_title:
                st.title(f"{st.session_state.selected_crop} Diagnostics")
            
            current_crop = st.session_state.selected_crop
            uploaded_file = st.file_uploader(f"Upload {current_crop} Leaf", type=['jpg','png','jpeg'])
            
            if uploaded_file:
                c1, c2 = st.columns([1,1])
                img = Image.open(uploaded_file)
                c1.image(img, caption="Specimen", use_container_width=True)
                
                if c2.button("INITIATE DEEP SCAN", type="primary"):
                    ph1 = c2.empty()
                    ph2 = c2.empty()
                    heavy_duty_scan(ph1, ph2, img)
                    ph2.empty()
                    
                    result = predict_disease(img)
                    
                    if "error" in result:
                        c2.error(result['error'])
                    else:
                        pred_class = result['class']
                        conf = result['confidence']
                        clean_name = pred_class.replace("_", " ").lower()
                        info = next((v for k, v in KNOWLEDGE_BASE.items() if clean_name in k.lower()), None)
                        
                        if info:
                            c2.success(f"Result: {info['disease_name']}")
                            c2.info(f"Confidence: {conf}")
                            st.markdown(f"""
                            <div style="background-color: {card_bg}; padding: 15px; border-radius: 10px; border-left: 5px solid #4CAF50;">
                                <h4>Diagnosis</h4>
                                <p>{info['description']}</p>
                                <h4>Treatment</h4>
                                <p>{info['treatment']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            st.link_button("🛒 Buy Medicine (Daraz.pk)", DARAZ_LINK)
                            play_audio(info['disease_name'])
                            
                            # Save History
                            user = st.session_state.user
                            if user not in history_db: history_db[user] = []
                            history_db[user].append({
                                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "crop": current_crop,
                                "disease": info['disease_name'],
                                "treatment": info['treatment']
                            })
                            save_data(HISTORY_FILE, history_db)
                        else:
                            c2.warning(f"Detected {pred_class}, but no medical info found.")

    # --- HISTORY TAB ---
    elif menu == "📜 My History":
        st.title("📜 Scan History")
        user = st.session_state.user
        user_history = history_db.get(user, [])
        
        col_f1, col_f2 = st.columns(2)
        with col_f1: filter_crop = st.selectbox("Filter by Crop:", ["All", "Apple", "Corn", "Potato"])
        with col_f2: 
            use_date = st.toggle("Filter by Date")
            filter_date = st.date_input("Select Date", datetime.date.today()) if use_date else None

        if not user_history:
            st.info("No scans found.")
        else:
            if st.button("🗑️ Clear History"):
                history_db[user] = []
                save_data(HISTORY_FILE, history_db)
                st.rerun()
            
            display_items = []
            for item in user_history:
                if filter_crop != "All" and item['crop'] != filter_crop: continue
                if filter_date and item['timestamp'].split(" ")[0] != str(filter_date): continue
                display_items.append(item)

            for item in reversed(display_items):
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.subheader(item['disease'])
                    c1.write(f"**Cure:** {item['treatment']}")
                    c2.caption(f"{item['timestamp']}")
                    c2.caption(f"Crop: {item['crop']}")

    # --- SETTINGS TAB ---
    elif menu == "⚙️ Settings":
        st.title("⚙️ Settings")
        st.checkbox("Dark Mode", value=st.session_state.dark_mode, key="dark_mode_toggle")
        st.radio("Voice Language", ["English", "Urdu"], key="voice_lang")

# --- 9. MASTER CONTROL ---
if st.session_state.logged_in:
    main_app()
else:
    login_screen()