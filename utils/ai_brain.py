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

# UPDATED PATH: We are looking for the file in the SAME directory as the app
# This removes the "models/" folder complexity
MODEL_PATH = "plant_disease_model.h5"

_model = None

def load_prediction_model():
    global _model
    if _model is not None:
        return _model

    # Debugging: Print where we are looking
    print(f"🔍 Looking for model at: {os.path.abspath(MODEL_PATH)}")

    if not os.path.exists(MODEL_PATH):
        print("❌ CRITICAL ERROR: The file is not on the server!")
        return None

    try:
        _model = tf.keras.models.load_model(MODEL_PATH)
        print("✅ Model loaded successfully.")
        return _model
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return None

def predict_disease(image_file):
    model = load_prediction_model()
    
    if model is None:
        # This error will now show exactly what went wrong
        return {"error": f"File '{MODEL_PATH}' not found on Cloud. Did you upload it to the main folder?"}

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