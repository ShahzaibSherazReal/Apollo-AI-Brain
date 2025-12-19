import tensorflow as tf
import numpy as np
from PIL import Image

# --- CONFIGURATION ---
# These names match your Colab training data exactly (lowercase)
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

MODEL_PATH = "models/plant_disease_model.h5"

# Global variable to store the model so we don't reload it every single time
_model = None

def load_prediction_model():
    """
    Loads the trained model from the file.
    Uses a global variable to cache the model for speed.
    """
    global _model
    if _model is not None:
        return _model

    try:
        # Load the model (this can take 1-2 seconds the first time)
        _model = tf.keras.models.load_model(MODEL_PATH)
        print("✅ Model loaded successfully.")
        return _model
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return None

def predict_disease(image_file):
    """
    1. Receives the image (PIL format)
    2. Prepares it (Resize 224x224)
    3. Asks the Brain (Model) what it sees
    """
    model = load_prediction_model()
    
    if model is None:
        return {"error": "Model file not found. Did you download the .h5 file?"}

    # 1. Prepare Image
    # Resize to 224x224 (The exact size MobileNetV2 expects)
    target_size = (224, 224)
    image = image_file.resize(target_size)
    
    # Convert image to a list of numbers (Array)
    img_array = np.array(image)
    
    # Safety Check: If image has a transparent background (PNG), remove the 4th layer
    if img_array.shape[-1] == 4:
        img_array = img_array[..., :3]
        
    # Create a batch of 1 (The model expects a list of images, even if it's just one)
    # Shape becomes: (1, 224, 224, 3)
    img_array = tf.expand_dims(img_array, 0) 

    # 2. Ask the Brain
    predictions = model.predict(img_array)
    
    # 3. Interpret Results
    # "softmax" converts the weird math numbers into percentages (0.0 to 1.0)
    score = tf.nn.softmax(predictions[0]) 
    
    # Find the winner (highest score)
    winner_index = np.argmax(score)
    predicted_class = CLASS_NAMES[winner_index]
    confidence_score = 100 * np.max(score) # Convert 0.95 to 95.0

    return {
        "class": predicted_class,
        "confidence": f"{confidence_score:.2f}%",
        "raw_score": confidence_score
    }