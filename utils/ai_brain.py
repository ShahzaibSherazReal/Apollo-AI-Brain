import tensorflow as tf
import numpy as np
from PIL import Image
import os

# --- CONFIGURATION ---
CLASS_NAMES = [
    'apple_black_rot',
    'apple_healthy',
    'apple_scab',
    'corn_common_rust',
    'corn_healthy',
    'corn_leaf_blight',
    'potato_early_blight',
    'potato_healthy',
    'potato_late_blight'
]

# Global variable to cache the model
_model = None

def load_prediction_model():
    global _model
    if _model is not None:
        return _model

    # --- SMART SEARCH: Hunt for the file ---
    possible_locations = [
        "plant_disease_model.h5",          # Option A: Main Folder
        "models/plant_disease_model.h5",   # Option B: Models Folder
        "Models/plant_disease_model.h5"    # Option C: Capitalized Folder
    ]
    
    selected_path = None
    
    # Check all locations
    for path in possible_locations:
        if os.path.exists(path):
            selected_path = path
            print(f"✅ FOUND IT! Model is at: {path}")
            break
            
    if selected_path is None:
        # DEBUG: If not found, list what IS there to help us fix it
        print("❌ CRITICAL: Model file not found in any expected folder.")
        print(f"📂 Current Directory Files: {os.listdir('.')}")
        if os.path.exists("models"):
            print(f"📂 Models Folder Files: {os.listdir('models')}")
        return None

    try:
        _model = tf.keras.models.load_model(selected_path)
        print("✅ Model loaded successfully.")
        return _model
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return None

def predict_disease(image_file):
    model = load_prediction_model()
    
    if model is None:
        return {"error": "Model file MISSING. I checked the main folder and 'models' folder, but it's not there. Did the upload finish?"}

    target_size = (224, 224)
    image = image_file.resize(target_size)
    img_array = np.array(image)
    
    if img_array.shape[-1] == 4:
        img_array = img_array[..., :3]
        
    img_array = tf.expand_dims(img_array, 0) 

    predictions = model.predict(img_array)
    score = tf.nn.softmax(predictions[0]) 
    
    winner_index = np.argmax(score)
    predicted_class = CLASS_NAMES[winner_index]
    confidence_score = 100 * np.max(score)

    return {
        "class": predicted_class,
        "confidence": f"{confidence_score:.2f}%",
        "raw_score": confidence_score
    }