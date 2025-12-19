import os
# ==========================================
# 🛑 CRITICAL FIX: FORCE LEGACY MODE
# This tells the server to act like the old TensorFlow
# This fixes the "Dense Layer" and "Batch Shape" errors instantly.
os.environ['TF_USE_LEGACY_KERAS'] = '1'
# ==========================================

import tensorflow as tf
import numpy as np
from PIL import Image

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

_model = None

def load_prediction_model():
    global _model
    if _model is not None:
        return _model, None

    # 1. Simple Search
    possible_locations = [
        "plant_disease_model.h5",
        "models/plant_disease_model.h5"
    ]
    
    selected_path = None
    for path in possible_locations:
        if os.path.exists(path):
            selected_path = path
            break
            
    if selected_path is None:
        return None, "File not found. Please upload .h5 file to GitHub."

    # 2. Load the Model (Standard Way)
    # Because we set the Legacy Flag at the top, this will now work!
    try:
        print(f"🔄 Loading model from {selected_path} in Legacy Mode...")
        _model = tf.keras.models.load_model(selected_path)
        print("✅ Model loaded successfully!")
        return _model, None
    except Exception as e:
        return None, f"Load Error: {str(e)}"

def predict_disease(image_file):
    model, error_msg = load_prediction_model()
    
    if model is None:
        return {"error": f"❌ {error_msg}"}

    # Prepare Image
    target_size = (224, 224)
    image = image_file.resize(target_size)
    img_array = np.array(image)
    
    if img_array.shape[-1] == 4:
        img_array = img_array[..., :3]
        
    img_array = tf.expand_dims(img_array, 0) 

    # Predict
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