import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow import keras
from flask import Flask, request, jsonify
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import balanced_accuracy_score
import shap
import os

# Initialize Flask app
app = Flask(__name__)

# Load dataset
df = pd.read_csv("suggested_tests.csv")

# Handle missing values (fill with mean)
df.fillna(df.mean(), inplace=True)

# Store Patient IDs separately
patient_ids = df["Patient ID"]

# Drop Patient ID (not a predictive feature for training)
df.drop(columns=["Patient ID"], inplace=True)

# Splitting features and targets
X = df.copy()  # Features
y = (df > 0).astype(int)  # Convert to binary classification (0 or 1)

# Train-test split
X_train, X_test, y_train, y_test, patient_train, patient_test = train_test_split(
    X, y, patient_ids, test_size=0.2, random_state=42
)

# Feature scaling
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# Check if trained model exists
MODEL_PATH = "multilabel_model.keras"

if os.path.exists(MODEL_PATH):
    print("Loading saved model...")
    model = keras.models.load_model(MODEL_PATH)
else:
    print("Training new model...")

    # Define the model
    def build_multilabel_classification_model():
        model = keras.Sequential([
            keras.layers.Input(shape=(X_train.shape[1],)),  # FIXED: Correct input layer definition
            keras.layers.Dense(64, activation="relu"),
            keras.layers.Dense(32, activation="relu"),
            keras.layers.Dense(y.shape[1], activation="sigmoid")  # Multi-label output
        ])
        model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
        return model

    # Train the model
    model = build_multilabel_classification_model()
    model.fit(X_train, y_train, epochs=15, batch_size=16, validation_data=(X_test, y_test), verbose=1)

    # Save trained model in the correct format
    model.save(MODEL_PATH)
    print(f"Model saved at {MODEL_PATH}")

# API Route for Home
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Welcome to the AI-based Test Prediction API!"})

# API Endpoint to predict tests for a specific Patient ID
@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    patient_id = data.get("patient_id")

    if patient_id in patient_test.values:
        idx = np.where(patient_test.values == patient_id)[0][0]
        patient_data = X_test[idx].reshape(1, -1)
        predicted_tests = model.predict(patient_data)[0]

        recommended_tests = (predicted_tests > 0.5).astype(int)
        test_names = df.columns[recommended_tests == 1].tolist()

        return jsonify({"patient_id": patient_id, "recommended_tests": test_names})
    else:
        return jsonify({"error": "Patient ID not found in the dataset."}), 404

# Run Flask app safely
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)  # FIXED: Prevents auto-restart issues
