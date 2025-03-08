from flask import Flask, request, jsonify
import pandas as pd
import uuid
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Load or create the dataset
file_path = "synthetic_symptoms_500.csv"

try:
    df = pd.read_csv(file_path)
except FileNotFoundError:
    df = pd.DataFrame(columns=["Patient_ID", "Fever", "Cough", "Fatigue", "Headache", "Sore Throat"])  # Example columns

@app.route('/submit_symptoms', methods=['POST'])
def submit_symptoms():
    try:
        # Get symptoms from the frontend
        symptoms = request.json.get("symptoms", [])

        # Generate a unique Patient ID
        patient_id = str(uuid.uuid4())[:8]  # Short UUID for simplicity

        # Create a new patient entry with all symptoms
        new_entry = {"Patient_ID": patient_id}
        for symptom in df.columns[1:]:  # Assuming first column is "Patient_ID"
            new_entry[symptom] = 1 if symptom in symptoms else 0

        # Append to DataFrame and save to CSV
        global df
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        df.to_csv(file_path, index=False)

        return jsonify({"message": "Symptoms recorded!", "patient_id": patient_id}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '_main_':
    app.run(debug=True)