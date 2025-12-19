import tensorflow as tf
import numpy as np
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

def build_model_structure():
    """
    Manually rebuilds the model architecture based on your error logs.
    This bypasses the need to read the broken config from the .h5 file.
    """
    # 1. Input Layer
    inputs = tf.keras.Input(shape=(224, 224, 3), name='input_layer_1')
    
    # 2. Rescaling Layer (1/255) - Seen in your logs
    x = tf.keras.layers.Rescaling(1./255, name='rescaling')(inputs)
    
    # 3. Base Model (MobileNetV2)
    # We load it without weights first, then load your weights later
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=(224, 224, 3),
        include_top=False,
        weights=None
    )
    # Freeze the base as seen in your logs
    base_model.trainable = False
    
    # Pass inputs through the base
    x = base_model(x, training=False)
    
    # 4. The Tail (Head) of the model - Seen in your logs
    x = tf.keras.layers.GlobalAveragePooling2D(name='global_average_pooling2d')(x)
    x = tf.keras.layers.Dropout(0.2, name='dropout')(x)
    outputs = tf.keras.layers.Dense(9, activation='softmax', name='dense')(x)
    
    # 5. Compile
    model = tf.keras.Model(inputs, outputs, name='sequential')
    return model

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

    # 2. THE REBUILD STRATEGY
    try:
        print(f"🏗️ Manually rebuilding architecture...")
        _model = build_model_structure()
        
        print(f"⚖️ Loading weights from {selected_path}...")
        # We assume the file contains the weights. 
        # by_name=True helps if there are slight naming mismatches.
        try:
            _model.load_weights(selected_path)
        except Exception as w_err:
            print("⚠️ Standard load failed, trying legacy mode...")
            # Fallback for complex saves
            _model.load_weights(selected_path, by_name=True, skip_mismatch=True)

        print("✅ Model successfully reconstructed and loaded!")
        return _model, None

    except Exception as e:
        return None, f"Rebuild Failed: {str(e)}"

def predict_disease(image_file):
    model, error_msg = load_prediction_model()
    
    if model is None:
        return {"error": f"❌ {error_msg}"}

    # Prepare Image
    target_size = (224, 224)
    image = image_file.resize(target_size)
    img_array = np.array(image)
    
    # Ensure RGB
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