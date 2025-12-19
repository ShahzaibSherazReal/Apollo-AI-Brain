import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import time
import requests
import os
import random
import numpy as np
from streamlit_lottie import st_lottie
from utils.ai_brain import predict_disease

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Leaf Disease Detection", page_icon="🌿", layout="wide")

# --- 2. SESSION STATE & THEME INITIALIZATION ---
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True  # Default to Dark Mode
if 'page' not in st.session_state: 
    st.session_state.page = 'home'
if 'selected_crop' not in st.session_state: 
    st.session_state.selected_crop = None

# Set Dynamic Colors based on Toggle
if st.session_state.dark_mode:
    app_bg = "#000000"
    sidebar_bg = "#000000"
    card_bg = "#121212"
    text_col = "#E0E0E0"
    border_col = "#333333"
    btn_bg = "#2b2b2b"
else:
    app_bg = "#FFFFFF"
    sidebar_bg = "#F8F9FA"
    card_bg = "#F0F2F6"
    text_col = "#000000"
    border_col = "#DDDDDD"
    btn_bg = "#E0E0E0"

# --- 3. CUSTOM CSS (DYNAMIC) ---
st.markdown(f"""
<style>
    /* MAIN THEME */
    .stApp {{ background-color: {app_bg}; }}
    section[data-testid="stSidebar"] {{ background-color: {sidebar_bg}; }}
    
    /* BUTTONS */
    .stButton>button {{
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: {btn_bg};
        color: {text_col};
        border: 1px solid #4CAF50;
        transition: all 0.3s ease;
    }}
    .stButton>button:hover {{
        background-color: #4CAF50;
        color: white;
        border-color: #45a049;
    }}

    /* CARDS */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: {card_bg};
        border: 1px solid {border_col};
        border-radius: 10px;
        padding: 10px;
    }}
    
    /* TEXT FORCE COLOR */
    h1, h2, h3, h4, h5, h6, p, div, span, li, label {{
        color: {text_col} !important;
    }}
</style>
""", unsafe_allow_html=True)

# --- 4. NAVIGATION LOGIC ---
def navigate_to(page, crop=None):
    st.session_state.page = page
    st.session_state.selected_crop = crop

# --- 5. ASSETS & DATABASE ---
lottie_brain = "https://lottie.host/60630956-e216-4298-905d-2a3543500410/3t49238088.json"

KNOWLEDGE_BASE = {
    "Apple Black Rot": { "disease_name": "Apple Black Rot", "description": "Fungal disease causing purple spots and rotting fruit.", "treatment": "Prune dead branches, use Captan or Sulfur." },
    "Apple Healthy": { "disease_name": "Healthy Apple Leaf", "description": "Vibrant green leaves, no lesions.", "treatment": "Regular water/fertilizer." },
    "Apple Scab": { "disease_name": "Apple Scab", "description": "Olive-green to black velvety spots.", "treatment": "Remove fallen leaves, apply fungicides." },
    "Corn Common Rust": { "disease_name": "Corn Common Rust", "description": "Cinnamon-brown pustules.", "treatment": "Resistant hybrids, fungicides." },
    "Corn Healthy": { "disease_name": "Healthy Corn Plant", "description": "No discoloration or pustules.", "treatment": "Proper irrigation/nitrogen." },
    "Corn Leaf Blight": { "disease_name": "Northern Corn Leaf Blight", "description": "Large, cigar-shaped grey-green lesions.", "treatment": "Crop rotation, resistant varieties." },
    "Potato Early Blight": { "disease_name": "Potato Early Blight", "description": "Target-shaped bullseye spots.", "treatment": "Improve air circulation, copper fungicides." },
    "Potato Healthy": { "disease_name": "Healthy Potato Plant", "description": "Dark green, firm leaves.", "treatment": "Keep soil moist but drained." },
    "Potato Late Blight": { "disease_name": "Potato Late Blight", "description": "Water-soaked spots turning black (Irish Famine disease).", "treatment": "Remove infected plants immediately, preventative fungicide." }
}

# --- 6. ANIMATION FUNCTION ---
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
        for x_grid in range(0, width, 50):
            draw.line([(x_grid, 0), (x_grid, height)], fill=(0, 255, 0, 50), width=1)
        for y_grid in range(0, height, 50):
            draw.line([(0, y_grid), (width, y_grid)], fill=(0, 255, 0, 50), width=1)
        for _ in range(3):
            rx, ry = random.randint(20, width-20), random.randint(20, height-20)
            length = 10
            draw.line([(rx-length, ry), (rx+length, ry)], fill=(255, 0, 0, 255), width=2)
            draw.line([(rx, ry-length), (rx, ry+length)], fill=(255, 0, 0, 255), width=2)
            draw.rectangle([rx-15, ry-15, rx+15, ry+15], outline=(255, 0, 0, 150), width=1)
        image_placeholder.image(frame, caption="🔍 SCANNING CELLULAR STRUCTURE...", use_container_width=True)
        with graph_placeholder.container():
            g1, g2 = st.columns(2)
            chart_data = [random.randint(10, 100) for _ in range(20)]
            g1.line_chart(chart_data, height=100)
            g2.progress(min(i / height, 1.0))
        time.sleep(0.15)

# --- 7. PAGE 1: HOME ---
if st.session_state.page == 'home':
    st.title("🌿 Leaf Disease Detection")
    st.subheader("① Select Your Plant System")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.markdown("<h1 style='text-align: center;'>🍎</h1>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center;'>Apple</h3>", unsafe_allow_html=True)
            st.write("Detects: Scab, Rot, Healthy")
            if st.button("Select Apple Model"): navigate_to('predict', 'Apple')
    with col2:
        with st.container(border=True):
            st.markdown("<h1 style='text-align: center;'>🌽</h1>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center;'>Corn (Maize)</h3>", unsafe_allow_html=True)
            st.write("Detects: Blight, Rust, Healthy")
            if st.button("Select Corn Model"): navigate_to('predict', 'Corn')
    with col3:
        with st.container(border=True):
            st.markdown("<h1 style='text-align: center;'>🥔</h1>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center;'>Potato</h3>", unsafe_allow_html=True)
            st.write("Detects: Early/Late Blight, Healthy")
            if st.button("Select Potato Model"): navigate_to('predict', 'Potato')
    
    st.markdown("---")
    st.caption("🚀 v3.0 Update: Tomato & Cotton coming soon.")

# --- 8. PAGE 2: PREDICTION ---
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
                disease_key = result["class"]
                confidence = result["confidence"]
                clean_name = disease_key.replace("_", " ").lower()
                found_info = next((v for k, v in KNOWLEDGE_BASE.items() if clean_name in k.lower()), None)
                
                with results_placeholder.container():
                    if found_info:
                        st.toast("Scan Complete. Match Found.", icon="✅")
                        st.markdown(f"""
                        <div style="background-color: {card_bg}; padding: 20px; border-radius: 10px; border: 1px solid #4CAF50;">
                            <h2 style="color: #4CAF50 !important;">{found_info['disease_name']}</h2>
                            <h4 style="color: {text_col} !important;">Confidence: {confidence}</h4>
                            <hr style="border-color: {border_col};">
                            <p><strong>🔬 Diagnosis:</strong> {found_info['description']}</p>
                            <p><strong>💊 Recommended Action:</strong> {found_info['treatment']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.warning(f"AI Detected: {disease_key}")

# --- 9. SIDEBAR (SETTINGS & STATUS) ---
with st.sidebar:
    st.title("Leaf Disease Detection")
    st.markdown("---")
    
    # Light/Dark Toggle Logic
    st.subheader("Settings")
    toggle_label = "🌙 Dark Mode Active" if st.session_state.dark_mode else "☀️ Light Mode Active"
    if st.toggle(toggle_label, value=st.session_state.dark_mode):
        if not st.session_state.dark_mode:
            st.session_state.dark_mode = True
            st.rerun()
    else:
        if st.session_state.dark_mode:
            st.session_state.dark_mode = False
            st.rerun()

    st.markdown("---")
    st.subheader("System Status")
    st.success("🟢 Neural Engine Online")
    st.info(f"📁 Database: {len(KNOWLEDGE_BASE)} Pathogens")
    st.caption("v2.5.0 - MobileNet Architecture")