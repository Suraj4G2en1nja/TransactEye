from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
from datetime import datetime
import mysql.connector
import os


# --- Database config ---
MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")       # default to 'mysql' service name
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "Suraj@4dec")
MYSQL_DB = os.getenv("MYSQL_DB", "fraud_detection")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))

conn = mysql.connector.connect(
    host=MYSQL_HOST,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DB,
    port=MYSQL_PORT
)


# --- Flask app ---
app = Flask(__name__)
CORS(app)

# --- Load ML model ---
model = joblib.load(os.path.join(os.path.dirname(__file__), "fraud_detection_pipeline.pkl"))

# --- Database connection ---
conn = mysql.connector.connect(
    host=MYSQL_HOST,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DB
)
cursor = conn.cursor()

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # 👇 Get data from frontend
        data = request.get_json()

        # 👇 Convert input to pandas DataFrame
        input_df = pd.DataFrame([data])

        # 👇 Make prediction and fraud probability
        prediction = int(model.predict(input_df)[0])
        fraud_score = round(float(model.predict_proba(input_df)[0][1]), 2)

        current_time = datetime.now()

        # 👇 Insert the transaction with full fields
        insert_query = """
            INSERT INTO Transactions (
                TransactionType, Amount,
                OldBalanceSender, NewBalanceSender,
                OldBalanceReceiver, NewBalanceReceiver,
                Timestamp,
                is_fraud, fraud_score
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(insert_query, (
            data["type"].lower(),         # maps to TransactionType
            data["amount"],
            data["oldbalanceOrg"],        # maps to OldBalanceSender
            data["newbalanceOrig"],       # maps to NewBalanceSender
            data["oldbalanceDest"],       # maps to OldBalanceReceiver
            data["newbalanceDest"],       # maps to NewBalanceReceiver
            current_time,                 # Timestamp
            prediction,                   # is_fraud
            fraud_score                   # fraud_score
        ))
        conn.commit()

        # 👇 Return prediction back to frontend
        return jsonify({
            "prediction": prediction,
            "fraud_score": fraud_score
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
