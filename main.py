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
import base64
import requests
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

# --- IMAGE HELPERS ---
def img_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

def base64_to_img(base64_str):
    return Image.open(io.BytesIO(base64.b64decode(base64_str)))

users_db = load_data(USERS_FILE, {})
history_db = load_data(HISTORY_FILE, {})

# --- 3. SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = None
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
def get_weather():
    try:
        lat, lon = 24.8607, 67.0011 
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        response = requests.get(url).json()
        temp = response['current_weather']['temperature']
        wcode = response['current_weather']['weathercode']
        if wcode <= 3: condition = "Sunny/Clear ☀️"
        elif wcode <= 49: condition = "Cloudy/Foggy ☁️"
        else: condition = "Rainy/Stormy 🌧️"
        return temp, condition
    except:
        return None, None

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
    with st.sidebar:
        st.write(f"👤 **{st.session_state.user}**")
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.session_state.internal_page = 'home'
            st.rerun()
        st.divider()
        menu = st.radio("Navigation", ["🏠 Home", "📜 My History"])
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

        st.divider()
        st.subheader("⚙️ Settings")
        is_dark = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode)
        if is_dark != st.session_state.dark_mode:
            st.session_state.dark_mode = is_dark
            st.rerun()
        st.session_state.voice_lang = st.radio("Voice Language:", ["English", "Urdu"], horizontal=True)

    # --- HOME TAB ---
    if menu == "🏠 Home":
        
        if st.session_state.internal_page == 'home':
            
            # WEATHER WIDGET
            temp, cond = get_weather()
            if temp:
                st.info(f"🌤️ **Live Weather (Karachi):** {temp}°C | {cond}")
                if "Rain" in cond:
                    st.warning("⚠️ Rain Alert: Avoid spraying pesticides today!")
            else:
                st.caption("⚠️ Weather service unavailable.")

            st.title("🌿 Leaf Diagnostics")
            st.subheader("① Select Your Plant System")
            
            col1, col2, col3 = st.columns(3)
            crops = [("🍎", "Apple"), ("🌽", "Corn"), ("🥔", "Potato")]
            
            for idx, (emoji, name) in enumerate(crops):
                with [col1, col2, col3][idx]:
                    with st.container(border=True):
                        st.markdown(f"<h1 style='text-align:center;'>{emoji}</h1><h3 style='text-align:center;'>{name}</h3>", unsafe_allow_html=True)
                        if st.button(f"Select {name}", key=f"btn_{name}"):
                            go_predict(name)
                            st.rerun()

            st.markdown("---")
            
            # MAPS
            st.subheader("📍 Find Agricultural Stores Nearby")
            st.caption("Showing nearest Fertilizer & Pesticide shops")
            map_html = """
            <iframe 
                width="100%" 
                height="400" 
                frameborder="0" 
                scrolling="no" 
                marginheight="0" 
                marginwidth="0" 
                src="https://maps.google.com/maps?q=agriculture+store+near+me&output=embed">
            </iframe>
            """
            st.components.v1.html(map_html, height=400)
            
            st.markdown("---")
            st.markdown("""
                <div style='text-align: center; color: gray; padding: 20px;'>
                    <h3>🚀 More crops coming soon...</h3>
                    <p>We are currently training models for Tomato, Grape, and Wheat.</p>
                </div>
            """, unsafe_allow_html=True)

        elif st.session_state.internal_page == 'predict':
            col_back, col_title = st.columns([1, 8])
            with col_back:
                if st.button("← Back"):
                    go_home()
                    st.rerun()
            with col_title:
                st.title(f"{st.session_state.selected_crop} Diagnostics")
            
            current_crop = st.session_state.selected_crop
            
            # TABS: CAMERA vs UPLOAD
            tab_cam, tab_upload = st.tabs(["📸 Take Photo", "📂 Upload from Gallery"])
            final_image = None

            with tab_cam:
                cam_img = st.camera_input(f"Take a picture of {current_crop}")
                if cam_img: final_image = Image.open(cam_img)

            with tab_upload:
                upload_img = st.file_uploader(f"Upload {current_crop} Image", type=['jpg','png','jpeg'])
                if upload_img: final_image = Image.open(upload_img)

            if final_image:
                col_left, col_right = st.columns([1, 1])
                
                with col_left:
                    scan_img_placeholder = st.empty()
                    scan_img_placeholder.image(final_image, caption="Specimen", use_container_width=True)
                    st.write("")
                    scan_btn = st.button("INITIATE DEEP SCAN", type="primary", use_container_width=True)

                with col_right:
                    graph_placeholder = st.empty()
                    results_placeholder = st.empty()

                if scan_btn:
                    heavy_duty_scan(scan_img_placeholder, graph_placeholder, final_image)
                    scan_img_placeholder.image(final_image, caption="Specimen", use_container_width=True)
                    graph_placeholder.empty()
                    
                    result = predict_disease(final_image)
                    
                    if "error" in result:
                        results_placeholder.error(result['error'])
                    else:
                        pred_class = result['class']
                        clean_name = pred_class.replace("_", " ").lower()
                        info = next((v for k, v in KNOWLEDGE_BASE.items() if clean_name in k.lower()), None)
                        
                        # --- SAFE LOGIC (NO BLOCKING) ---
                        # We try to check confidence just to show a warning, but we do NOT stop the process.
                        try:
                            val_str = str(result['confidence']).replace('%','').strip()
                            conf_score = float(val_str)
                            # If it looks like decimal 0.98, convert to 98
                            if conf_score <= 1.0: conf_score *= 100
                        except:
                            conf_score = 100.0 # Assume high if parsing fails

                        with results_placeholder.container():
                            # Soft Warning for wrong crops (Does not block)
                            if conf_score < 40.0:
                                st.warning(f"⚠️ Low Confidence ({int(conf_score)}%). This might not be a {current_crop} leaf.")

                            if info:
                                st.success(f"Result: {info['disease_name']}")
                                st.info(f"Confidence: {result['confidence']}")
                                st.markdown(f"""
                                <div style="background-color: {card_bg}; padding: 15px; border-radius: 10px; border-left: 5px solid #4CAF50;">
                                    <h4>Diagnosis</h4>
                                    <p>{info['description']}</p>
                                    <h4>Treatment</h4>
                                    <p>{info['treatment']}</p>
                                </div>
                                """, unsafe_allow_html=True)
                                st.link_button("🛒 Buy Medicine (Daraz.pk)", DARAZ_LINK)
                                st.write("---")
                                play_audio(info['disease_name'])
                                
                                # SAVE HISTORY
                                user = st.session_state.user
                                if user not in history_db: history_db[user] = []
                                img_str = img_to_base64(final_image)
                                history_db[user].append({
                                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                                    "crop": current_crop,
                                    "disease": info['disease_name'],
                                    "treatment": info['treatment'],
                                    "image": img_str
                                })
                                save_data(HISTORY_FILE, history_db)
                            else:
                                st.warning(f"Detected {pred_class}, but no medical info found.")

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
                    c_img, c_text = st.columns([1, 4])
                    with c_img:
                        if "image" in item:
                            try:
                                recovered_img = base64_to_img(item["image"])
                                st.image(recovered_img, use_container_width=True)
                            except: st.error("Img Error")
                        else: st.caption("No Image")
                    with c_text:
                        st.subheader(item['disease'])
                        st.caption(f"📅 {item['timestamp']} | Crop: {item['crop']}")
                        st.write(f"**Cure:** {item['treatment']}")

# --- 9. MASTER CONTROL ---
if st.session_state.logged_in:
    main_app()
else:
    login_screen()