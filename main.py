import streamlit as st
from PIL import Image
import time
import requests
import os
from streamlit_lottie import st_lottie
from utils.ai_brain import predict_disease

# --- CONFIGURATION ---
st.set_page_config(page_title="Leaf Disease Detection", page_icon="🌿", layout="wide")

# --- CUSTOM CSS (THE FIX) ---
st.markdown("""
<style>
    /* 1. MAKE MAIN BACKGROUND PURE BLACK */
    .stApp {
        background-color: #000000;
    }
    
    /* 2. MAKE SIDEBAR PURE BLACK */
    section[data-testid="stSidebar"] {
        background-color: #000000;
    }

    /* 3. STYLE BUTTONS */
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #2b2b2b;
        color: white;
        border: 1px solid #4CAF50;
    }
    .stButton>button:hover {
        background-color: #4CAF50;
        color: white;
        border-color: #45a049;
    }

    /* 4. TARGET ONLY THE CROP CARDS (Containers with borders) */
    /* This specific selector targets the 'st.container(border=True)' elements */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #121212; /* Dark Grey for Cards */
        border: 1px solid #333;
        border-radius: 10px;
        padding: 10px;
    }
    
    /* 5. FIX TEXT COLOR & HEADINGS */
    h1, h2, h3, p, div, span {
        color: #E0E0E0 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE MANAGEMENT ---
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'selected_crop' not in st.session_state:
    st.session_state.selected_crop = None

def navigate_to(page, crop=None):
    st.session_state.page = page
    st.session_state.selected_crop = crop

# --- ASSETS & ANIMATIONS ---
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    except:
        return None

lottie_brain = load_lottieurl("https://lottie.host/60630956-e216-4298-905d-2a3543500410/3t49238088.json")

# --- EMBEDDED DATABASE ---
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

# --- PAGE 1: HOME (SELECTION SCREEN) ---
if st.session_state.page == 'home':
    st.title("🌿 Leaf Disease Detection")
    st.subheader("① Select Your Plant System")
    st.write("Choose a crop below to initialize the specific diagnostic model.")
    st.write("") # Spacer

    col1, col2, col3 = st.columns(3)

    # --- CARD 1: APPLE ---
    with col1:
        with st.container(border=True):
            st.markdown("<h1 style='text-align: center;'>🍎</h1>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center;'>Apple</h3>", unsafe_allow_html=True)
            st.write("Detects: Scab, Black Rot, Rust")
            if st.button("Select Apple Model"):
                navigate_to('predict', 'Apple')

    # --- CARD 2: CORN ---
    with col2:
        with st.container(border=True):
            st.markdown("<h1 style='text-align: center;'>🌽</h1>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center;'>Corn (Maize)</h3>", unsafe_allow_html=True)
            st.write("Detects: Blight, Rust, Gray Leaf")
            if st.button("Select Corn Model"):
                navigate_to('predict', 'Corn')

    # --- CARD 3: POTATO ---
    with col3:
        with st.container(border=True):
            st.markdown("<h1 style='text-align: center;'>🥔</h1>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center;'>Potato</h3>", unsafe_allow_html=True)
            st.write("Detects: Early Blight, Late Blight")
            if st.button("Select Potato Model"):
                navigate_to('predict', 'Potato')
    
    st.markdown("---")
    st.caption("🚀 More crops (Tomato, Grape, Cotton) coming in v3.0 update...")


# --- PAGE 2: PREDICTION (ANALYSIS SCREEN) ---
elif st.session_state.page == 'predict':
    
    # Back Button Logic
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
                else:
                    disease_key = result["class"] # e.g., "apple_black_rot"
                    confidence = result["confidence"]
                    
                    # --- SMART MATCHING LOGIC ---
                    clean_name = disease_key.replace("_", " ").lower()
                    
                    found_info = None
                    
                    # Scan database keys to find a match
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

# --- SIDEBAR (Always Visible) ---
with st.sidebar:
    try:
        st.image("assets/logo.png", use_container_width=True)
    except:
        st.title("Leaf Disease Detection")
    
    st.markdown("---")
    st.subheader("🧠 Model Status")
    st.success("MobileNetV2 Active")
    st.caption("Training Accuracy: 99.1%")
    
    st.markdown("---")
    if st.session_state.page == 'home':
        st.info("Select a crop system to begin diagnostics.")
    else:
        st.info(f"Currently analyzing: **{st.session_state.selected_crop}**")