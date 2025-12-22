import streamlit as st
from PIL import Image, ImageDraw
import time
import random
import datetime
import numpy as np
from gtts import gTTS
import io
import urllib.parse # [NEW] To generate Calendar Links
from utils.ai_brain import predict_disease

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Leaf Disease Detection", page_icon="🌿", layout="wide")

# --- 2. SESSION STATE & THEME ---
if 'dark_mode' not in st.session_state: st.session_state.dark_mode = True
if 'page' not in st.session_state: st.session_state.page = 'home'
if 'selected_crop' not in st.session_state: st.session_state.selected_crop = None
if 'scan_history' not in st.session_state: st.session_state.scan_history = []
if 'voice_lang' not in st.session_state: st.session_state.voice_lang = 'English'
# [NEW] Treatment Plan Memory
if 'treatment_plan' not in st.session_state: st.session_state.treatment_plan = []

# Dynamic Colors
if st.session_state.dark_mode:
    app_bg, sidebar_bg, card_bg, text_col, border_col, btn_bg = "#000000", "#000000", "#121212", "#E0E0E0", "#333333", "#2b2b2b"
else:
    app_bg, sidebar_bg, card_bg, text_col, border_col, btn_bg = "#FFFFFF", "#F8F9FA", "#F0F2F6", "#000000", "#DDDDDD", "#E0E0E0"

st.markdown(f"""
<style>
    .stApp {{ background-color: {app_bg}; }}
    section[data-testid="stSidebar"] {{ background-color: {sidebar_bg}; }}
    .stButton>button {{ width: 100%; border-radius: 5px; height: 3em; background-color: {btn_bg}; color: {text_col}; border: 1px solid #4CAF50; }}
    div[data-testid="stVerticalBlockBorderWrapper"] {{ background-color: {card_bg}; border: 1px solid {border_col}; border-radius: 10px; padding: 10px; }}
    h1, h2, h3, h4, h5, h6, p, div, span, li, label {{ color: {text_col} !important; }}
</style>
""", unsafe_allow_html=True)

# --- 3. DATA & TRANSLATIONS ---
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

DARAZ_PRODUCT_LINK = "https://www.daraz.pk/products/80-250-i161020707-s1327886846.html"

def navigate_to(page, crop=None):
    st.session_state.page = page
    st.session_state.selected_crop = crop

# --- 4. HELPER FUNCTIONS ---
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
        image_placeholder.image(frame, caption="🔍 SCANNING CELLULAR STRUCTURE...", use_container_width=True)
        with graph_placeholder.container():
            g1, g2 = st.columns(2)
            g1.line_chart([random.randint(10, 100) for _ in range(20)], height=100)
            g2.progress(min(i / height, 1.0))
        time.sleep(0.05)

def play_voice_feedback(disease_name):
    lang_code = 'ur' if st.session_state.voice_lang == 'Urdu' else 'en'
    if lang_code == 'ur':
        text_to_speak = URDU_MESSAGES.get(disease_name, "Beemari ki tashkhees ho gayi hai.")
    else:
        text_to_speak = f"Alert. {disease_name} detected."
    try:
        tts = gTTS(text=text_to_speak, lang=lang_code)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        st.audio(audio_buffer, format='audio/mp3', start_time=0)
    except Exception as e:
        st.warning("⚠️ Audio unavailable")

# [NEW] Generate Calendar Link
def create_calendar_link(title, details):
    base_url = "https://www.google.com/calendar/render?action=TEMPLATE"
    # Set for tomorrow at 9 AM
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    dates = f"{tomorrow.strftime('%Y%m%d')}T090000Z/{tomorrow.strftime('%Y%m%d')}T100000Z"
    
    params = {
        "text": f"🌿 Treat {title}",
        "details": f"Recommended Action: {details}\n\nGenerated by Leaf Disease App.",
        "dates": dates
    }
    return f"{base_url}&{urllib.parse.urlencode(params)}"

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("Leaf Disease Detection")
    
    if st.button("🏠 Return Home"): navigate_to('home'); st.rerun()
    if st.button("📜 History Log"): navigate_to('history'); st.rerun()
    
    # [NEW] Alerts Button
    # Shows a red bubble if there are active tasks
    task_count = len(st.session_state.treatment_plan)
    label = f"🔔 Treatment Plan ({task_count})" if task_count > 0 else "🔔 Treatment Plan"
    if st.button(label): navigate_to('alerts'); st.rerun()

    st.markdown("---")
    st.subheader("🔊 Audio Settings")
    st.session_state.voice_lang = st.radio("Voice Language:", ["English", "Urdu"], horizontal=True)

    st.markdown("---")
    with st.expander("🌱 Tips for Gardening"):
        st.markdown("* **Watering:** Early morning.\n* **Soil:** Good drainage.\n* **Sunlight:** 6+ hours.")
    with st.expander("🎯 About Us"):
        st.write("Bridging AI & Agriculture.")
    with st.expander("📖 Our Story"):
        st.write("Built by students of **Iqra University North Campus**.")
        
    st.markdown("---")
    st.subheader("Settings")
    if st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode):
        if not st.session_state.dark_mode: st.session_state.dark_mode = True; st.rerun()
    else:
        if st.session_state.dark_mode: st.session_state.dark_mode = False; st.rerun()
    st.success("🟢 Neural Engine Online"); st.caption("v6.0 - Smart Alerts")

# --- 6. HOME PAGE ---
if st.session_state.page == 'home':
    st.title("🌿 Leaf Disease Detection (v6.0)")
    st.subheader("① Select Your Plant System")
    col1, col2, col3 = st.columns(3)
    crops = [("🍎", "Apple"), ("🌽", "Corn"), ("🥔", "Potato")]
    for idx, (emoji, name) in enumerate(crops):
        with [col1, col2, col3][idx]:
            with st.container(border=True):
                st.markdown(f"<h1 style='text-align:center;'>{emoji}</h1><h3 style='text-align:center;'>{name}</h3>", unsafe_allow_html=True)
                if st.button(f"Select {name}", key=f"btn_{name}"): navigate_to('predict', name)

# --- 7. HISTORY PAGE ---
elif st.session_state.page == 'history':
    st.title("📜 Scan Log")
    col1, col2, col3 = st.columns([2,2,2])
    with col1: filter_crop = st.selectbox("Filter:", ["All", "Apple", "Corn", "Potato"])
    with col3: 
        st.write("")
        if st.button("🗑️ Clear All"): st.session_state.scan_history = []; st.rerun()

    st.markdown("---")
    if not st.session_state.scan_history: st.info("No scans yet.")
    else:
        for idx, item in reversed(list(enumerate(st.session_state.scan_history))):
            if filter_crop != "All" and item['crop'] != filter_crop: continue
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 4, 1])
                with c1: st.image(item['image'], width=100)
                with c2:
                    st.subheader(item['disease_name'])
                    st.caption(f"{item['timestamp']}")
                with c3:
                    if st.button("🗑️", key=f"hist_{idx}"):
                        st.session_state.scan_history.pop(idx); st.rerun()

# --- 8. [NEW] ALERTS / TREATMENT PLAN PAGE ---
elif st.session_state.page == 'alerts':
    st.title("🔔 Active Treatment Plan")
    st.caption("Track your plant care tasks here.")
    
    if not st.session_state.treatment_plan:
        st.info("✅ No active treatments. Your plants are happy!")
        if st.button("← Go Back"): navigate_to('home'); st.rerun()
    else:
        for idx, task in enumerate(st.session_state.treatment_plan):
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 4, 2])
                with c1: st.write("🌿")
                with c2:
                    st.subheader(task['disease'])
                    st.write(f"**Action:** {task['treatment']}")
                    st.caption(f"Added on: {task['date']}")
                with c3:
                    st.write("")
                    # Mark as Done Button
                    if st.button("✅ Mark Done", key=f"done_{idx}"):
                        st.session_state.treatment_plan.pop(idx)
                        st.toast("Task Completed!", icon="🎉")
                        time.sleep(0.5)
                        st.rerun()
                    
                    # Calendar Link Button
                    cal_url = create_calendar_link(task['disease'], task['treatment'])
                    st.link_button("📅 Add to Calendar", cal_url)

# --- 9. PREDICTION PAGE ---
elif st.session_state.page == 'predict':
    c1, c2 = st.columns([1, 8])
    with c1: 
        if st.button("← Back"): navigate_to('home')
    with c2: st.title(f"{st.session_state.selected_crop} Diagnostics")

    uploaded_file = st.file_uploader(f"Upload {st.session_state.selected_crop} Leaf", type=["jpg","png","jpeg"])
    
    if uploaded_file is not None:
        c1, c2 = st.columns([1, 1])
        image = Image.open(uploaded_file)
        with c1: st.image(image, caption="Specimen", use_container_width=True)
        with c2:
            graph_loc = st.empty()
            res_loc = st.empty()

        if st.button("INITIATE DEEP SCAN"):
            heavy_duty_scan(c1, graph_loc, image) # simplistic animation call
            graph_loc.empty()
            
            result = predict_disease(image)
            
            if "error" in result: res_loc.error("❌ " + result["error"])
            else:
                p_key = result["class"]
                conf_val = float(result["confidence"].replace('%', ''))
                curr_crop = st.session_state.selected_crop
                valid_keys = ALLOWED_CLASSES.get(curr_crop, [])

                if p_key not in valid_keys:
                    res_loc.error("⚠️ WRONG LEAF DETECTED")
                elif conf_val < 20.0:
                    res_loc.warning(f"⚠️ Low Confidence ({conf_val}%)")
                else:
                    clean_name = p_key.replace("_", " ").lower()
                    info = next((v for k, v in KNOWLEDGE_BASE.items() if clean_name in k.lower()), None)
                    
                    if info:
                        # Save History
                        st.session_state.scan_history.append({
                            "crop": curr_crop, "image": image, "disease_name": info['disease_name'],
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                        play_voice_feedback(info['disease_name'])

                        with res_loc.container():
                            st.toast("Match Found", icon="✅")
                            st.markdown(f"""
                            <div style="background-color: {card_bg}; padding: 20px; border-radius: 10px; border: 1px solid #4CAF50;">
                                <h2 style="color: #4CAF50 !important; margin:0;">{info['disease_name']}</h2>
                                <h4 style="color: {text_col} !important;">Confidence: {result['confidence']}</h4>
                                <hr style="border-color: {border_col};">
                                <p><strong>Diagnosis:</strong> {info['description']}</p>
                                <p><strong>Action:</strong> {info['treatment']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            c_btn1, c_btn2, c_btn3 = st.columns(3)
                            
                            # 1. Buy Medicine
                            with c_btn1:
                                st.write("")
                                st.link_button("🛒 Buy Cure", DARAZ_PRODUCT_LINK)
                            
                            # 2. Add to In-App Alerts [NEW]
                            with c_btn2:
                                st.write("")
                                if st.button("🔔 Monitor"):
                                    st.session_state.treatment_plan.append({
                                        "disease": info['disease_name'],
                                        "treatment": info['treatment'],
                                        "date": datetime.datetime.now().strftime("%Y-%m-%d")
                                    })
                                    st.toast("Added to Treatment Plan!", icon="🔔")
                            
                            # 3. Add to Phone Calendar [NEW]
                            with c_btn3:
                                st.write("")
                                cal_url = create_calendar_link(info['disease_name'], info['treatment'])
                                st.link_button("📅 Calendar", cal_url)

                    else:
                        res_loc.warning(f"Detected: {p_key}")