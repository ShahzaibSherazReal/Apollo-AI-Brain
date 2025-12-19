import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import time
import requests
import os
import random
import numpy as np
from streamlit_lottie import st_lottie
from utils.ai_brain import predict_disease

# --- CONFIGURATION ---
st.set_page_config(page_title="Leaf Disease Detection", page_icon="🌿", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    /* MAIN THEME */
    .stApp { background-color: #000000; }
    section[data-testid="stSidebar"] { background-color: #000000; }
    
    /* BUTTONS */
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #2b2b2b;
        color: white;
        border: 1px solid #4CAF50;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #4CAF50;
        color: white;
        border-color: #45a049;
    }

    /* CARDS */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #121212;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 10px;
    }
    
    /* TEXT */
    h1, h2, h3, h4, h5, h6, p, div, span, li, label {
        color: #E0E0E0 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'page' not in st.session_state: st.session_state.page = 'home'
if 'selected_crop' not in st.session_state: st.session_state.selected_crop = None

def navigate_to(page, crop=None):
    st.session_state.page = page
    st.session_state.selected_crop = crop

# --- ASSETS ---
lottie_brain = "https://lottie.host/60630956-e216-4298-905d-2a3543500410/3t49238088.json"

# --- DATABASE ---
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

# --- 🛰️ SCI-FI SCANNING ANIMATION FUNCTION ---
def heavy_duty_scan(image_placeholder, graph_placeholder, original_img):
    """
    Creates a visual effect of scanning the leaf with lasers, grids, and metrics.
    """
    # 1. Setup Image
    img = original_img.copy().convert("RGBA")
    width, height = img.size
    
    # Resize for performance if too huge
    if width > 500:
        ratio = 500 / width
        img = img.resize((500, int(height * ratio)))
        width, height = img.size

    step_size = int(height / 10) # 10 frames of scanning
    
    # 2. The Animation Loop
    for i in range(0, height + step_size, step_size):
        # Create a fresh frame based on original
        frame = img.copy()
        draw = ImageDraw.Draw(frame)
        
        # A. The Laser Line (Moving Down)
        scan_y = i if i < height else height - 1
        draw.line([(0, scan_y), (width, scan_y)], fill=(0, 255, 0, 200), width=5)
        
        # B. The "Grid" Overlay (Fades in)
        for x_grid in range(0, width, 50):
            draw.line([(x_grid, 0), (x_grid, height)], fill=(0, 255, 0, 50), width=1)
        for y_grid in range(0, height, 50):
            draw.line([(0, y_grid), (width, y_grid)], fill=(0, 255, 0, 50), width=1)

        # C. Random "Target Locks" (Crosshairs)
        for _ in range(3):
            rx, ry = random.randint(20, width-20), random.randint(20, height-20)
            length = 10
            # Draw Cross
            draw.line([(rx-length, ry), (rx+length, ry)], fill=(255, 0, 0, 255), width=2)
            draw.line([(rx, ry-length), (rx, ry+length)], fill=(255, 0, 0, 255), width=2)
            # Draw Box
            draw.rectangle([rx-15, ry-15, rx+15, ry+15], outline=(255, 0, 0, 150), width=1)

        # D. Update Image on Screen
        image_placeholder.image(frame, caption="🔍 SCANNING CELLULAR STRUCTURE...", use_container_width=True)
        
        # E. Update Graphs (The "Heavy Calculation" look)
        with graph_placeholder.container():
            g1, g2 = st.columns(2)
            # Random "Biometrics" data
            chart_data = [random.randint(10, 100) for _ in range(20)]
            g1.line_chart(chart_data, height=100)
            g1.caption(f"Chlorophyll Levels: {random.randint(400, 800)} nm")
            
            # Random "Confidence" bars
            g2.progress(min(i / height, 1.0))
            g2.caption("Analyzing Texture Patterns...")
            
        time.sleep(0.15) # Control speed of scan

# --- PAGE 1: HOME ---
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

# --- PAGE 2: PREDICTION ---
elif st.session_state.page == 'predict':
    
    col_back, col_title = st.columns([1, 8])
    with col_back:
        if st.button("← Back"): navigate_to('home')
    
    with col_title:
        st.title(f"{st.session_state.selected_crop} Diagnostics")

    uploaded_file = st.file_uploader(f"Upload {st.session_state.selected_crop} Leaf", type=["jpg", "png", "jpeg"])

    if uploaded_file is not None:
        # Layout: Left for Image/Scan, Right for Results/Graphs
        col1, col2 = st.columns([1, 1])
        
        image = Image.open(uploaded_file)
        
        # Placeholders must be created OUTSIDE the button to persist
        with col1:
            scan_placeholder = st.empty()
            # Show original static image first
            scan_placeholder.image(image, caption="Original Specimen", use_container_width=True)
        
        with col2:
            graph_placeholder = st.empty() # For the "Heavy Duty" graphs
            results_placeholder = st.empty() # For the final answer

        # BUTTON LOGIC
        if st.button("INITIATE DEEP SCAN"):
            # 1. RUN THE ANIMATION
            heavy_duty_scan(scan_placeholder, graph_placeholder, image)
            
            # 2. CLEAR GRAPHS (Optional: or keep them as "History")
            graph_placeholder.empty()
            
            # 3. SHOW RESULTS
            result = predict_disease(image)
            
            if "error" in result:
                results_placeholder.error("❌ " + result["error"])
            else:
                disease_key = result["class"]
                confidence = result["confidence"]
                clean_name = disease_key.replace("_", " ").lower()
                found_info = None
                
                for db_key in KNOWLEDGE_BASE:
                    if clean_name in db_key.lower():
                        found_info = KNOWLEDGE_BASE[db_key]
                        break
                
                with results_placeholder.container():
                    if found_info:
                        st.toast("Scan Complete. Match Found.", icon="✅")
                        st.markdown(f"""
                        <div style="background-color: #1E1E1E; padding: 20px; border-radius: 10px; border: 1px solid #4CAF50; box-shadow: 0 0 15px rgba(76, 175, 80, 0.3);">
                            <h2 style="color: #4CAF50 !important; margin:0;">{found_info['disease_name']}</h2>
                            <h4 style="color: #bbb !important;">Confidence: <span style="color:#fff">{confidence}</span></h4>
                            <hr style="border-color: #333;">
                            <p style="color: #ddd !important;"><strong>🔬 Diagnosis:</strong> {found_info['description']}</p>
                            <p style="color: #ddd !important;"><strong>💊 Recommended Action:</strong> {found_info['treatment']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.warning(f"AI Detected: {disease_key}")
                        st.info("Database entry missing for this specific variant.")

# --- SIDEBAR ---
with st.sidebar:
    st.title("AgroScan AI")
    st.markdown("---")
    st.subheader("System Status")
    st.success("🟢 Neural Engine Online")
    st.info(f"📁 Database: {len(KNOWLEDGE_BASE)} Pathogens")
    st.caption("v2.5.0 - MobileNet Architecture")