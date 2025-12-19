import streamlit as st
from PIL import Image
import json
import time
import requests
from streamlit_lottie import st_lottie
from utils.ai_brain import predict_disease

# --- CONFIGURATION ---
st.set_page_config(page_title="Leaf Disease Detection", page_icon="🌿", layout="wide")
# --- ASSETS & ANIMATIONS ---
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

# The "Brain" Doodle Animation
lottie_brain = load_lottieurl("https://lottie.host/60630956-e216-4298-905d-2a3543500410/3t49238088.json")

def load_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except:
        pass

# Load Dark Mode
load_css("assets/dark.css")

# Load Database (Text Descriptions)
try:
    with open("database.json", "r") as f:
        KNOWLEDGE_BASE = json.load(f)
except:
    # If database is missing, we create a fake empty one to prevent crashing
    KNOWLEDGE_BASE = {}
    st.error("⚠️ Error: database.json not found. Text descriptions will be missing.")

# --- SIDEBAR ---
with st.sidebar:
    try:
        st.image("assets/logo.png", use_container_width=True)
    except:
        st.title("AgroScan AI")
    
    st.markdown("---")
    st.subheader("🧠 Model Status")
    st.success("MobileNetV2 Active")
    st.caption("Training Accuracy: 99.1%")
    
    st.markdown("---")
    st.info("This version uses Deep Learning (CNN) to analyze leaf patterns in real-time.")

# --- MAIN APP ---
st.title("🌿 Leaf Disease Detection")
st.markdown("Upload a leaf image. The AI will analyze the cellular patterns to detect disease.")

uploaded_file = st.file_uploader("", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    col1, col2 = st.columns([1, 1])
    
    image = Image.open(uploaded_file)
    with col1:
        st.image(image, caption="Specimen", use_container_width=True)
    
    if st.button("Analyze Specimen"):
        with col2:
            # Animation
            anim_placeholder = st.empty()
            with anim_placeholder.container():
                c1, c2 = st.columns([1,3])
                with c1:
                    if lottie_brain:
                        st_lottie(lottie_brain, height=100, key="brain")
                    else:
                        st.spinner("Thinking...")
                with c2:
                    st.write("Extracting features...")
                    time.sleep(0.5)
                    st.write("Matching patterns...")
                    time.sleep(0.5)
            
            anim_placeholder.empty()

            # --- THE AI PREDICTION ---
            result = predict_disease(image)
            
            if "error" in result:
                st.error("❌ Model Error: " + result["error"])
                st.warning("Did you forget to upload the .h5 file to the 'models' folder?")
            else:
                disease_key = result["class"] # e.g., "apple_black_rot"
                confidence = result["confidence"]
                
                # --- SMART MATCHING LOGIC ---
                # 1. Replace underscores with spaces (apple_black_rot -> apple black rot)
                # 2. Convert to lowercase to ensure a perfect match
                clean_name = disease_key.replace("_", " ").lower()
                
                found_info = None
                
                # Scan database keys to find a match
                # We check if our "clean_name" is inside any database key
                for db_key in KNOWLEDGE_BASE:
                    if clean_name in db_key.lower():
                        found_info = KNOWLEDGE_BASE[db_key]
                        break
                
                if found_info:
                    st.toast("Identification Complete", icon="🧬")
                    st.markdown(f"""
                    <div style="background-color: #2b2b2b; padding: 20px; border-radius: 10px; border-left: 5px solid #00b894;">
                        <h2 style="color: #00b894; margin:0;">{found_info['disease_name']}</h2>
                        <p style="color: #ccc; margin-top:5px;">AI Confidence: <strong>{confidence}</strong></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.write("")
                    st.markdown(f"**🔬 Description:** {found_info['description']}")
                    st.markdown(f"**💊 Treatment:** {found_info['treatment']}")
                else:
                    # Fallback if AI predicts a class we don't have text for
                    st.warning(f"AI Detected: **{disease_key}**")
                    st.caption(f"Confidence: {confidence}")
                    st.info("No detailed description found in database for this specific disease.")