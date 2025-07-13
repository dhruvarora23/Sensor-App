import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

st.set_page_config(page_title="Sensor Dashboard", layout="wide")
st.title("📊 Sensor Data Analysis App")

uploaded_file = st.file_uploader("Upload the Excel file exported from your dashboard (.xlsx)", type="xlsx")

if uploaded_file:
    # Read Excel
    df = pd.read_excel(uploaded_file, header=4).iloc[1:].copy()

    # Convert necessary columns
    df['X9_numeric'] = pd.to_numeric(df['X9'], errors='coerce')      # Vibration
    df['X10_numeric'] = pd.to_numeric(df['X10'], errors='coerce')    # Vibration threshold
    df['X27_numeric'] = pd.to_numeric(df['X27'], errors='coerce')    # Temperature
    df['X26_datetime'] = pd.to_datetime(df['X26'], errors='coerce')  # Timestamp
    df['SensorLabel'] = df['X8'].astype(str) + " - " + df['X4'].astype(str)

    # Threshold checks
    df['Vibration_Warning'] = df['X9_numeric'] > df['X10_numeric']
    df['Temperature_Status'] = df['X27_numeric'].apply(
        lambda x: 'Red' if x > 50 else 'Orange' if x >= 40 else 'Green'
    )

    st.success("✅ Analysis complete.")

    # Show summary counts
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🔧 Vibration Warnings", df['Vibration_Warning'].sum())
    with col2:
        st.metric("🌡️ Temperature Warnings", sum(df['Temperature_Status'].isin(['Red', 'Orange'])))

    # Download flagged rows
    def to_excel(filtered_df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            filtered_df.to_excel(writer, index=False)
        return output.getvalue()

    vib_flags = df[df['Vibration_Warning'] == True]
    temp_flags = df[df['Temperature_Status'].isin(['Red', 'Orange'])]

    st.subheader("⚠️ Download Warnings")
    if not vib_flags.empty:
        st.download_button("📥 Vibration Warnings Excel", to_excel(vib_flags), "vibration_warnings.xlsx")
    if not temp_flags.empty:
        st.download_button("📥 Temperature Warnings Excel", to_excel(temp_flags), "temperature_warnings.xlsx")

    # Vibration plots
    st.subheader("📈 Vibration Trends (with Thresholds)")
    for sensor in df['X8'].dropna().unique():
        if sensor == '17ND': continue
        sensor_df = df[df['X8'] == sensor].dropna(subset=['X9_numeric', 'X10_numeric', 'X26_datetime'])
        if sensor_df.empty:
            continue
        plt.figure(figsize=(10, 4))
        plt.plot(sensor_df['X26_datetime'], sensor_df['X9_numeric'], label='Vibration (mm/s)', marker='o')
        plt.plot(sensor_df['X26_datetime'], sensor_df['X10_numeric'], linestyle='--', label='Threshold', color='red')
        plt.title(f"Sensor: {sensor_df['SensorLabel'].iloc[0]}")
        plt.xlabel("Time")
        plt.ylabel("Vibration")
        plt.legend()
        plt.grid(True)
        st.pyplot(plt)

    # Temperature plots
    st.subheader("🌡️ Temperature Trends with Risk Bands")
    for sensor in df['X8'].dropna().unique():
        if sensor == '17ND': continue
        sensor_df = df[df['X8'] == sensor].dropna(subset=['X27_numeric', 'X26_datetime'])
        if sensor_df.empty:
            continue
        plt.figure(figsize=(10, 4))
        plt.plot(sensor_df['X26_datetime'], sensor_df['X27_numeric'], label='Temperature (°C)', marker='o', color='orange')
        plt.axhspan(0, 40, color='green', alpha=0.1)
        plt.axhspan(40, 50, color='orange', alpha=0.1)
        plt.axhspan(50, sensor_df['X27_numeric'].max() + 5, color='red', alpha=0.1)
        plt.title(f"Sensor: {sensor_df['SensorLabel'].iloc[0]}")
        plt.xlabel("Time")
        plt.ylabel("Temperature")
        plt.legend()
        plt.grid(True)
        st.pyplot(plt)
