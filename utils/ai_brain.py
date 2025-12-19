import tensorflow as tf
import numpy as np
import h5py
import json
import os
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

    # 1. Search for file
    possible_locations = ["plant_disease_model.h5", "models/plant_disease_model.h5"]
    selected_path = None
    for path in possible_locations:
        if os.path.exists(path):
            selected_path = path
            break
            
    if selected_path is None:
        return None, "File not found on server."

    # 2. THE BYPASS STRATEGY (Enhanced)
    try:
        print(f"🔧 Starting manual reconstruction of: {selected_path}")
        
        with h5py.File(selected_path, 'r') as f:
            model_config = f.attrs.get('model_config')
            if model_config is None:
                raise ValueError("No config found in file.")
            
            if isinstance(model_config, bytes):
                model_config = model_config.decode('utf-8')
            
            model_json = json.loads(model_config)

        # A. FIX: Rename 'batch_shape' to 'batch_input_shape'
        def fix_json_config(node):
            if isinstance(node, dict):
                if 'batch_shape' in node:
                    node['batch_input_shape'] = node['batch_shape']
                    del node['batch_shape']
                
                if 'config' in node and isinstance(node['config'], dict):
                    if 'batch_shape' in node['config']:
                        node['config']['batch_input_shape'] = node['config']['batch_shape']
                        del node['config']['batch_shape']
                        
                for key, value in node.items():
                    fix_json_config(value)
            elif isinstance(node, list):
                for item in node:
                    fix_json_config(item)

        fix_json_config(model_json)

        # B. FIX: Define the Translation Dictionary (The "Rosetta Stone")
        # This tells the loader exactly what every word means
        custom_objects = {
            "Sequential": tf.keras.Sequential,
            "Functional": tf.keras.Model,
            "InputLayer": tf.keras.layers.InputLayer,
            "Rescaling": tf.keras.layers.Rescaling,
            "Conv2D": tf.keras.layers.Conv2D,
            "BatchNormalization": tf.keras.layers.BatchNormalization,
            "ReLU": tf.keras.layers.ReLU,
            "DepthwiseConv2D": tf.keras.layers.DepthwiseConv2D,
            "ZeroPadding2D": tf.keras.layers.ZeroPadding2D,
            "Add": tf.keras.layers.Add,
            "GlobalAveragePooling2D": tf.keras.layers.GlobalAveragePooling2D,
            "Dropout": tf.keras.layers.Dropout,
            "Dense": tf.keras.layers.Dense
        }

        # 3. Rebuild Model with the Dictionary
        print("🔨 Rebuilding model architecture...")
        _model = tf.keras.models.model_from_json(
            json.dumps(model_json), 
            custom_objects=custom_objects  # <--- This fixes the 'Could not locate' error
        )

        # 4. Load the Weights
        print("⚖️ Loading weights...")
        _model.load_weights(selected_path)
        
        print("✅ Model successfully reconstructed!")
        return _model, None

    except Exception as e:
        return None, f"Reconstruction Failed: {str(e)}"

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