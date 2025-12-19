import streamlit as st
from PIL import Image
import time
import requests
import os
from streamlit_lottie import st_lottie
from utils.ai_brain import predict_disease

# --- CONFIGURATION ---
st.set_page_config(page_title="Leaf Disease Detection", page_icon="🌿", layout="wide")

# --- SESSION STATE INITIALIZATION ---
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'selected_crop' not in st.session_state:
    st.session_state.selected_crop = None
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'  # Default to dark

# --- THEME LOGIC ---
def toggle_theme():
    if st.session_state.theme == 'dark':
        st.session_state.theme = 'light'
    else:
        st.session_state.theme = 'dark'

# Define Colors based on current theme
if st.session_state.theme == 'dark':
    # DARK MODE PALETTE
    main_bg = "#000000"
    sidebar_bg = "#000000"
    card_bg = "#121212"
    text_color = "#E0E0E0"
    border_color = "#333333"
    button_bg = "#2b2b2b"
    button_border = "#4CAF50"
    button_text = "#FFFFFF"
    card_shadow = "none"
else:
    # LIGHT MODE PALETTE
    main_bg = "#FFFFFF"
    sidebar_bg = "#F0F2F6"
    card_bg = "#FFFFFF"
    text_color = "#31333F"
    border_color = "#DDDDDD"
    button_bg = "#FFFFFF"
    button_border = "#4CAF50"
    button_text = "#31333F"
    card_shadow = "0 4px 6px rgba(0,0,0,0.1)"

# --- INJECT DYNAMIC CSS ---
st.markdown(f"""
<style>
    /* 1. MAIN BACKGROUND */
    .stApp {{
        background-color: {main_bg};
    }}
    
    /* 2. SIDEBAR BACKGROUND */
    section[data-testid="stSidebar"] {{
        background-color: {sidebar_bg};
    }}

    /* 3. BUTTON STYLES */
    .stButton>button {{
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: {button_bg};
        color: {button_text};
        border: 1px solid {button_border};
        transition: all 0.3s ease;
    }}
    .stButton>button:hover {{
        background-color: #4CAF50;
        color: white;
        border-color: #45a049;
    }}

    /* 4. CARD STYLES */
    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: {card_bg};
        border: 1px solid {border_color};
        border-radius: 10px;
        padding: 10px;
        box-shadow: {card_shadow};
    }}
    
    /* 5. TEXT COLOR OVERRIDES */
    h1, h2, h3, h4, h5, h6, p, div, span, li, label {{
        color: {text_color} !important;
    }}
    
    /* Fix for file uploader text in light mode */
    .stFileUploader label {{
        color: {text_color} !important;
    }}
</style>
""", unsafe_allow_html=True)

# --- NAVIGATION FUNCTION ---
def navigate_to(page, crop=None):
    st.session_state.page = page
    st.session_state.selected_crop = crop

# --- ASSETS ---
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

lottie_brain = load_lottieurl("https://lottie.host/60630956-e216-4298-905d-2a3543500410/3t49238088.json")

# --- DATABASE ---
KNOWLEDGE_BASE = {
    "Apple Black Rot": {
        "disease_name": "Apple Black Rot",
        "description": "A fungal disease caused by Botryosphaeria obtusa. It causes purple spots on leaves and rotting fruit that turns black and mummified.",
        "treatment": "Prune dead branches, remove mummified fruit, and use fungicides like Captan or Sulfur."
    },
    "Apple Healthy": {
        "disease_name": "Healthy Apple Leaf",
        "description": "The plant is in good health. Leaves are green, vibrant, and free of spots or lesions.",
        "treatment": "Continue regular watering and fertilization. No treatment needed."
    },
    "Apple Scab": {
        "disease_name": "Apple Scab",
        "description": "A serious fungal disease causing olive-green to black velvety spots on leaves and fruit.",
        "treatment": "Remove fallen leaves to prevent wintering spores. Apply fungicides early in the season."
    },
    "Corn Common Rust": {
        "disease_name": "Corn Common Rust",
        "description": "Fungal pustules appear on leaves, turning from cinnamon-brown to black as the plant matures.",
        "treatment": "Plant resistant hybrids. Fungicides are effective if applied early."
    },
    "Corn Healthy": {
        "disease_name": "Healthy Corn Plant",
        "description": "Vibrant green leaves with no signs of discoloration or pustules.",
        "treatment": "Maintain proper irrigation and nitrogen levels."
    },
    "Corn Leaf Blight": {
        "disease_name": "Northern Corn Leaf Blight",
        "description": "Large, cigar-shaped grey-green lesions on leaves that can kill the plant tissue.",
        "treatment": "Crop rotation and resistant varieties are the best defense. Fungicides may be needed for severe cases."
    },
    "Potato Early Blight": {
        "disease_name": "Potato Early Blight",
        "description": "Target-shaped bullseye spots with yellow halos on older leaves.",
        "treatment": "Improve air circulation, avoid overhead watering, and apply copper-based fungicides."
    },
    "Potato Healthy": {
        "disease_name": "Healthy Potato Plant",
        "description": "Leaves are dark green and firm. No signs of wilting or spotting.",
        "treatment": "Keep soil moist but well-drained. Hilling soil around the base helps tuber growth."
    },
    "Potato Late Blight": {
        "disease_name": "Potato Late Blight",
        "description": "The disease that caused the Irish Potato Famine. Water-soaked spots turn brown/black with white mold.",
        "treatment": "Remove infected plants immediately (do not compost). Apply preventative fungicides regularly."
    }
}

# --- PAGE 1: HOME ---
if st.session_state.page == 'home':
    st.title("🌿 Leaf Disease Detection")
    st.subheader("① Select Your Plant System")
    st.write("Choose a crop below to initialize the specific diagnostic model.")
    st.write("") 

    col1, col2, col3 = st.columns(3)

    # --- CARD 1: APPLE ---
    with col1:
        with st.container(border=True):
            st.markdown("<h1 style='text-align: center;'>🍎</h1>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center;'>Apple</h3>", unsafe_allow_html=True)
            st.write("Detects: Scab, Rot, Healthy")
            if st.button("Select Apple Model"):
                navigate_to('predict', 'Apple')

    # --- CARD 2: CORN ---
    with col2:
        with st.container(border=True):
            st.markdown("<h1 style='text-align: center;'>🌽</h1>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center;'>Corn (Maize)</h3>", unsafe_allow_html=True)
            st.write("Detects: Blight, Rust, Healthy")
            if st.button("Select Corn Model"):
                navigate_to('predict', 'Corn')

    # --- CARD 3: POTATO ---
    with col3:
        with st.container(border=True):
            st.markdown("<h1 style='text-align: center;'>🥔</h1>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center;'>Potato</h3>", unsafe_allow_html=True)
            st.write("Detects: Early Blight, Late Blight, Healthy")
            if st.button("Select Potato Model"):
                navigate_to('predict', 'Potato')
    
    st.markdown("---")
    st.caption("🚀 More crops (Tomato, Grape, Cotton) coming in v3.0 update...")


# --- PAGE 2: PREDICTION ---
elif st.session_state.page == 'predict':
    
    col_back, col_title = st.columns([1, 8])
    with col_back:
        if st.button("← Back"):
            navigate_to('home')
    
    with col_title:
        st.title(f"{st.session_state.selected_crop} Disease Detection")

    st.markdown(f"Upload a **{st.session_state.selected_crop}** leaf image. The AI will analyze the cellular patterns.")
    
    uploaded_file = st.file_uploader("", type=["jpg", "png", "jpeg"])

    if uploaded_file is not None:
        col1, col2 = st.columns([1, 1])
        
        image = Image.open(uploaded_file)
        with col1:
            st.image(image, caption="Specimen", use_container_width=True)
        
        if st.button("Analyze Specimen"):
            with col2:
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

                result = predict_disease(image)
                
                if "error" in result:
                    st.error("❌ Model Error: " + result["error"])
                else:
                    disease_key = result["class"]
                    confidence = result["confidence"]
                    
                    clean_name = disease_key.replace("_", " ").lower()
                    found_info = None
                    
                    for db_key in KNOWLEDGE_BASE:
                        if clean_name in db_key.lower():
                            found_info = KNOWLEDGE_BASE[db_key]
                            break
                    
                    if found_info:
                        st.toast("Identification Complete", icon="🧬")
                        # Info Card Style
                        info_bg = "#F0F2F6" if st.session_state.theme == 'light' else "#2b2b2b"
                        text_c = "#31333F" if st.session_state.theme == 'light' else "#ccc"
                        
                        st.markdown(f"""
                        <div style="background-color: {info_bg}; padding: 20px; border-radius: 10px; border-left: 5px solid #00b894;">
                            <h2 style="color: #00b894 !important; margin:0;">{found_info['disease_name']}</h2>
                            <p style="color: {text_c} !important; margin-top:5px;">AI Confidence: <strong>{confidence}</strong></p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.write("")
                        st.markdown(f"**🔬 Description:** {found_info['description']}")
                        st.markdown(f"**💊 Treatment:** {found_info['treatment']}")
                    else:
                        st.warning(f"AI Detected: **{disease_key}**")
                        st.caption(f"Confidence: {confidence}")
                        st.info("No detailed description found in database for this specific disease.")

# --- SIDEBAR ---
with st.sidebar:
    try:
        st.image("assets/logo.png", use_container_width=True)
    except:
        st.title("Leaf Disease Detection")
    
    # --- THEME TOGGLE BUTTON ---
    btn_text = "☀️ Light Mode" if st.session_state.theme == 'dark' else "🌑 Dark Mode"
    if st.button(btn_text):
        toggle_theme()
        st.rerun() # Force reload to apply new CSS immediately
    
    st.markdown("---")
    st.subheader("🧠 Model Status")
    st.success("MobileNetV2 Active")
    st.caption("Training Accuracy: 99.1%")
    
    st.markdown("---")
    if st.session_state.page == 'home':
        st.info("Select a crop system to begin diagnostics.")
    else:
        st.info(f"Currently analyzing: **{st.session_state.selected_crop}**")