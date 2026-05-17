import os
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import GlobalAveragePooling2D, Dense, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam

BREED_LABELS = [
    'Gir',
    'Sahiwal',
    'Ongole',
    'Red Sindhi',
    'Murrah',
    'Surti'
]

IMAGE_SIZE = (224, 224)


def create_mobilenetv2_model(num_classes):
    base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(IMAGE_SIZE[0], IMAGE_SIZE[1], 3))
    base_model.trainable = False

    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dropout(0.35)(x)
    x = Dense(256, activation='relu')(x)
    x = Dropout(0.25)(x)
    predictions = Dense(num_classes, activation='softmax')(x)

    model = Model(inputs=base_model.input, outputs=predictions)
    model.compile(optimizer=Adam(learning_rate=1e-4), loss='categorical_crossentropy', metrics=['accuracy'])
    return model


def load_breed_model(model_path):
    if os.path.exists(model_path):
        return load_model(model_path)
    return create_mobilenetv2_model(len(BREED_LABELS))


def preprocess_image(image):
    image = image.resize(IMAGE_SIZE)
    array = np.array(image) / 255.0
    array = np.expand_dims(array, axis=0)
    return array


def predict_breed(model, image):
    input_data = preprocess_image(image)
    if model is None:
        return 'Unknown Breed', 0.0

    output = model.predict(input_data)
    score = float(np.max(output))
    label_index = int(np.argmax(output))
    return BREED_LABELS[label_index], score
