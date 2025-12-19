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

_model = None

def load_prediction_model():
    global _model
    if _model is not None:
        return _model, None  # Return Model + No Error

    # 1. Search for the file
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
        return None, "File not found in Main or Models folder."

    # 2. Check File Size (Crucial Check!)
    file_size_mb = os.path.getsize(selected_path) / (1024 * 1024)
    print(f"📂 Found model at {selected_path} | Size: {file_size_mb:.2f} MB")
    
    if file_size_mb < 1.0:
        return None, f"File found but too small ({file_size_mb:.2f} MB). It should be ~10MB+. Upload failed?"

    # 3. Try to Load
    try:
        _model = tf.keras.models.load_model(selected_path)
        return _model, None
    except Exception as e:
        # Return the ACTUAL error message from TensorFlow
        return None, f"Corrupt File or Version Mismatch. Error: {str(e)}"

def predict_disease(image_file):
    model, error_msg = load_prediction_model()
    
    if model is None:
        return {"error": f"❌ {error_msg}"}

    # Prepare and Predict
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