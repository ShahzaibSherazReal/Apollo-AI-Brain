import streamlit as st
from PIL import Image, ImageDraw
import time
import random
import datetime
import numpy as np
from utils.ai_brain import predict_disease

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Leaf Disease Detection", page_icon="🌿", layout="wide")

# --- 2. SESSION STATE & THEME ---
if 'dark_mode' not in st.session_state: st.session_state.dark_mode = True
if 'page' not in st.session_state: st.session_state.page = 'home'
if 'selected_crop' not in st.session_state: st.session_state.selected_crop = None

# [NEW] Initialize History Memory
if 'scan_history' not in st.session_state: 
    st.session_state.scan_history = []

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

# --- 3. DATA & VALIDATION ---
ALLOWED_CLASSES = {
    "Apple": ["apple_black_rot", "apple_healthy", "apple_scab"],
    "Corn": ["corn_common_rust", "corn_healthy", "corn_leaf_blight"],
    "Potato": ["potato_early_blight", "potato_healthy", "potato_late_blight"]
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

def navigate_to(page, crop=None):
    st.session_state.page = page
    st.session_state.selected_crop = crop

# --- 4. ANIMATION ---
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

# --- 5. SIDEBAR ---
with st.sidebar:
    st.title("Leaf Disease Detection")
    
    if st.button("🏠 Return Home"):
        navigate_to('home')
        st.rerun()

    # [NEW] History Button
    if st.button("📜 History Log"):
        navigate_to('history')
        st.rerun()

    st.markdown("---")
    
    with st.expander("🌱 Tips for Gardening"):
        st.markdown("""
        * **Watering:** Water early in the morning to prevent evaporation.
        * **Soil:** Ensure good drainage to avoid root rot.
        * **Sunlight:** Most vegetables need at least 6 hours of direct sun.
        * **Spacing:** Don't crowd plants; air circulation prevents fungus.
        """)

    with st.expander("🎯 About Us"):
        st.write("Our goal is to bridge the gap between advanced technology and agriculture. We aim to empower farmers with instant, offline disease detection tools to save crops and increase yield.")

    with st.expander("📖 Our Story"):
        st.write("""
        We are a team of dedicated students from **Iqra University North Campus**.
        This application was built as our project to tackle real-world agricultural challenges. By combining MobileNet architecture with Flutter, we created a solution that works right in the field.
        """)
        
    st.markdown("---")
    st.subheader("Settings")
    if st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode):
        if not st.session_state.dark_mode: st.session_state.dark_mode = True; st.rerun()
    else:
        if st.session_state.dark_mode: st.session_state.dark_mode = False; st.rerun()

    st.markdown("---")
    st.success("🟢 Neural Engine Online")
    st.caption("v4.0 - History Module Active")

# --- 6. HOME PAGE ---
if st.session_state.page == 'home':
    st.title("🌿 Leaf Disease Detection (v4.0)")
    st.subheader("① Select Your Plant System")
    col1, col2, col3 = st.columns(3)
    crops = [("🍎", "Apple"), ("🌽", "Corn"), ("🥔", "Potato")]
    for idx, (emoji, name) in enumerate(crops):
        with [col1, col2, col3][idx]:
            with st.container(border=True):
                st.markdown(f"<h1 style='text-align:center;'>{emoji}</h1><h3 style='text-align:center;'>{name}</h3>", unsafe_allow_html=True)
                if st.button(f"Select {name}", key=f"btn_{name}"): navigate_to('predict', name)

# --- 7. HISTORY PAGE [NEW SECTION] ---
elif st.session_state.page == 'history':
    st.title("📜 Scan Log")
    
    # 7.1 Filter Selection
    filter_col, _ = st.columns([1, 3])
    with filter_col:
        filter_option = st.selectbox("Filter by Crop History:", ["All", "Apple", "Corn", "Potato"])

    st.markdown("---")

    # 7.2 Logic to show history
    if not st.session_state.scan_history:
        st.info("No scans recorded yet. Go to Home and perform a scan.")
    else:
        # Loop through history backwards (newest first)
        for scan in reversed(st.session_state.scan_history):
            # Apply Filter
            if filter_option == "All" or scan['crop'] == filter_option:
                with st.container(border=True):
                    c1, c2 = st.columns([1, 3])
                    with c1:
                        st.image(scan['image'], width=150, caption=scan['timestamp'])
                    with c2:
                        st.subheader(f"{scan['disease_name']}")
                        st.caption(f"Crop: {scan['crop']} | Confidence: {scan['confidence']}%")
                        st.write(f"**💊 Cure:** {scan['treatment']}")

# --- 8. PREDICTION PAGE ---
elif st.session_state.page == 'predict':
    col_back, col_title = st.columns([1, 8])
    with col_back:
        if st.button("← Back"): navigate_to('home')
    with col_title:
        st.title(f"{st.session_state.selected_crop} Diagnostics")

    uploaded_file = st.file_uploader(f"Upload {st.session_state.selected_crop} Leaf", type=["jpg", "png", "jpeg"])
    
    if uploaded_file is not None:
        col1, col2 = st.columns([1, 1])
        image = Image.open(uploaded_file)
        with col1:
            scan_placeholder = st.empty()
            scan_placeholder.image(image, caption="Original Specimen", use_container_width=True)
        with col2:
            graph_placeholder = st.empty()
            results_placeholder = st.empty()

        if st.button("INITIATE DEEP SCAN"):
            heavy_duty_scan(scan_placeholder, graph_placeholder, image)
            graph_placeholder.empty()
            
            result = predict_disease(image)
            
            if "error" in result:
                results_placeholder.error("❌ " + result["error"])
            else:
                prediction_key = result["class"]
                confidence_str = result["confidence"].replace('%', '')
                confidence_val = float(confidence_str)
                
                current_section = st.session_state.selected_crop
                valid_keys = ALLOWED_CLASSES.get(current_section, [])

                # 1. Strict Mismatch Check
                if prediction_key not in valid_keys:
                    with results_placeholder.container():
                        st.error("⚠️ WRONG LEAF DETECTED")
                        st.markdown(f"Analysis Rejected. Expected {current_section}, got {prediction_key.replace('_',' ')}.")
                
                # 2. Low Confidence Check
                elif confidence_val < 20.0:
                    with results_placeholder.container():
                        st.warning(f"⚠️ Low Confidence Alert ({confidence_val}%)")
                        st.info("Image unclear.")

                # 3. Success & SAVE TO HISTORY [UPDATED]
                else:
                    clean_name = prediction_key.replace("_", " ").lower()
                    found_info = next((v for k, v in KNOWLEDGE_BASE.items() if clean_name in k.lower()), None)
                    
                    if found_info:
                        # --- [NEW] SAVE TO HISTORY ---
                        st.session_state.scan_history.append({
                            "crop": current_section,
                            "image": image,
                            "disease_name": found_info['disease_name'],
                            "confidence": confidence_val,
                            "treatment": found_info['treatment'],
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        })
                        
                        with results_placeholder.container():
                            st.toast("Result Saved to History", icon="💾")
                            st.markdown(f"""
                            <div style="background-color: {card_bg}; padding: 20px; border-radius: 10px; border: 1px solid #4CAF50;">
                                <h2 style="color: #4CAF50 !important; margin:0;">{found_info['disease_name']}</h2>
                                <h4 style="color: {text_col} !important;">Confidence: {result['confidence']}</h4>
                                <hr style="border-color: {border_col};">
                                <p><strong>Diagnosis:</strong> {found_info['description']}</p>
                                <p><strong>Treatment:</strong> {found_info['treatment']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.warning(f"Detected: {prediction_key} (No DB Info)")