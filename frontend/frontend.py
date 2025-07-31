import streamlit as st
import pandas as pd
import requests
import mysql.connector
from datetime import datetime
import os

# --- MySQL config from environment variables ---
MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")   # Docker service name, or 'localhost' if running locally outside Docker
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "Suraj@4dec")
MYSQL_DB = os.getenv("MYSQL_DB", "fraud_detection")

# --- API endpoint URL from environment ---

api_url = os.getenv("API_URL", "http://backend:5000/predict")

# Database connection helper
def get_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )
# --- Load data ---
def load_history():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Transactions ORDER BY TransactionID DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    df = pd.DataFrame(rows)

    if not df.empty:
        df.columns = [col.lower() for col in df.columns]
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['Month'] = df['timestamp'].dt.strftime('%B')
        df['Year'] = df['timestamp'].dt.year
        df.rename(columns={'is_fraud': 'Prediction'}, inplace=True)

    return df

# --- Delete all records and reset ID ---
def delete_history():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Transactions")
    cursor.execute("ALTER TABLE Transactions AUTO_INCREMENT = 1")
    conn.commit()
    cursor.close()
    conn.close()

# --- Delete specific rows by ID ---
def delete_selected_rows(transaction_ids):
    if not transaction_ids:
        return
    conn = get_connection()
    cursor = conn.cursor()
    format_strings = ','.join(['%s'] * len(transaction_ids))
    query = f"DELETE FROM Transactions WHERE TransactionID IN ({format_strings})"
    cursor.execute(query, transaction_ids)
    conn.commit()
    cursor.close()
    conn.close()

# -------------------- Streamlit UI --------------------

st.set_page_config(page_title="Fraud Detection", layout="wide")
st.title(" 🛡️✔️ TransactEye ")
st.markdown("Enter transaction details and detect fraudulent behavior.")
st.divider()

# --- Input form ---
transaction_type = st.selectbox("Transaction Type", ["PAYMENT", "TRANSFER", "CASH_OUT"])
amount = st.number_input("Amount", min_value=0.0, value=1000.0)
oldbalanceOrg = st.number_input("Old Balance (Sender)", min_value=0.0, value=10000.0)
newbalanceOrig = st.number_input("New Balance (Sender)", min_value=0.0, value=9000.0)
oldbalanceDest = st.number_input("Old Balance (Receiver)", min_value=0.0, value=0.0)
newbalanceDest = st.number_input("New Balance (Receiver)", min_value=0.0, value=0.0)

if st.button("🚀 Predict"):
    input_payload = {
        "type": transaction_type,
        "amount": amount,
        "oldbalanceOrg": oldbalanceOrg,
        "newbalanceOrig": newbalanceOrig,
        "oldbalanceDest": oldbalanceDest,
        "newbalanceDest": newbalanceDest
    }

    try:
        response = requests.post(api_url, json=input_payload)
        result = response.json()
        prediction = result['prediction']
        score = round(result['fraud_score'] * 100, 2)

        st.subheader(f"🧠 Prediction: **{'FRAUD' if prediction == 1 else 'NOT FRAUD'}**")
        st.metric("Fraud Score", f"{score}%")

        if prediction == 1:
            st.error("⚠️ This transaction is likely FRAUDULENT.")
        else:
            st.success("✅ This transaction seems safe.")

    except Exception as e:
        st.error(f"❌ Error: {e}")

st.divider()

# --- Dashboard & History ---
st.header("📜 Prediction History")

if st.button("🗑️ Delete All History"):
    delete_history()
    st.success("✅ All history deleted!")
    st.rerun()

history_df = load_history()

if history_df.empty:
    st.info("No prediction history found yet.")
else:
    # KPIs
    total_txns = len(history_df)
    fraud_txns = history_df[history_df['Prediction'] == 1].shape[0]

    col1, col2 = st.columns(2)
    col1.metric("📦 Total Transactions", total_txns)
    col2.metric("🚨 Fraudulent Transactions", fraud_txns)

    st.divider()

    # Transaction Type Chart
    st.subheader("🧾 Transactions by Type")
    type_counts = history_df['transactiontype'].value_counts().reset_index()
    type_counts.columns = ['Transaction Type', 'Count']
    st.bar_chart(type_counts.set_index('Transaction Type'))

    # Time Filters
    st.subheader("📅 Filter by Time")
    selected_year = st.selectbox("Select Year", sorted(history_df['Year'].unique(), reverse=True))
    filtered_df = history_df[history_df['Year'] == selected_year]

    selected_month = st.selectbox("Select Month", ["All"] + sorted(
        filtered_df['Month'].unique(), key=lambda m: datetime.strptime(m, "%B").month
    ))

    if selected_month != "All":
        filtered_df = filtered_df[filtered_df['Month'] == selected_month]

    # Monthly Fraud Chart
    st.subheader("📈 Monthly Fraud Overview")
    monthly_grouped = (
        history_df[history_df['Year'] == selected_year]
        .groupby("Month")
        .agg(Total=('transactionid', 'count'),
             Fraud=('Prediction', 'sum'))
        .reindex(['January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December'])
        .dropna(how='all')
    )
    st.bar_chart(monthly_grouped)

    # Transaction Table with Delete Option
    st.subheader("🔍 Transaction Records")
    filtered_df = filtered_df.copy()
    filtered_df["Delete"] = False  # Add delete checkbox column

    edited_df = st.data_editor(
        filtered_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Delete": st.column_config.CheckboxColumn(label="🗑️ Delete?"),
            "transactionid": st.column_config.NumberColumn("Transaction ID", disabled=True),
        },
        disabled=["timestamp", "Month", "Year", "transactiontype", "amount", "oldbalanceorg", "newbalanceorig", "oldbalancedest", "newbalancedest", "Prediction"]
    )

    to_delete_ids = edited_df[edited_df["Delete"] == True]["transactionid"].dropna().astype(int).tolist()

    if to_delete_ids:
        if st.button("❌ Confirm Delete Selected"):
            delete_selected_rows(to_delete_ids)
            st.success(f"✅ Deleted entries: {', '.join(map(str, to_delete_ids))}")
            st.rerun()
