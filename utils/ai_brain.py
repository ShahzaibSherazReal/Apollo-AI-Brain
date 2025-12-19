import tensorflow as tf
import numpy as np
import h5py
import json
import os
import tempfile
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
        return None, "File not found."

    # 2. BRAIN SURGERY: Fix the 'batch_shape' error on the fly
    try:
        print(f"🔧 Attempting to patch model file: {selected_path}")
        
        # Open the file and read the configuration
        with h5py.File(selected_path, 'r') as f:
            model_config = f.attrs.get('model_config')
            if model_config is None:
                raise ValueError("No model config found in file.")
            
            # Decode and parse JSON
            if isinstance(model_config, bytes):
                model_config = model_config.decode('utf-8')
            config_dict = json.loads(model_config)

        # RECURSIVE FUNCTION to find and delete 'batch_shape'
        def remove_batch_shape(node):
            if isinstance(node, dict):
                if 'batch_shape' in node:
                    print("🔪 Removed 'batch_shape' from config.")
                    del node['batch_shape']
                for key, value in node.items():
                    remove_batch_shape(value)
            elif isinstance(node, list):
                for item in node:
                    remove_batch_shape(item)

        # Perform the surgery
        remove_batch_shape(config_dict)

        # Save to a temporary file
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, 'patched_model.h5')
        
        # Copy original file to temp path first
        import shutil
        shutil.copy(selected_path, temp_path)
        
        # Overwrite the config in the temp file
        with h5py.File(temp_path, 'r+') as f:
            f.attrs['model_config'] = json.dumps(config_dict).encode('utf-8')

        # 3. Load the Patched Model
        print(f"🔄 Loading patched model from {temp_path}...")
        _model = tf.keras.models.load_model(temp_path, compile=False)
        print("✅ Model loaded successfully!")
        
        return _model, None

    except Exception as e:
        return None, f"Patching Failed: {str(e)}"

def predict_disease(image_file):
    model, error_msg = load_prediction_model()
    
    if model is None:
        return {"error": f"❌ {error_msg}"}

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