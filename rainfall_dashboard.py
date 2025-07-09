import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ---------- CONFIG ----------
st.set_page_config(page_title="Rain Calendar", layout="wide")
st.title("🌧️ 14-Day Rainfall Forecast Calendar")

# ---------- PREDEFINED LOCATIONS ----------
default_places = {
    "Vadodara": (22.3855, 73.1124),
    "Nagpur": (21.16596, 79.37988),
    "METC - Jhajjar": (28.52778, 76.81399),
    "Dhenkanal": (20.72582, 85.51291),
    "Jabalpur": (23.27223, 79.86855),
    "Satna": (24.5803, 80.7172),
    "Nagothane": (18.5508, 73.1029),
    "Kakinada 1": (17.04536, 82.13721),
    "Kakinada 2": (17.04536, 82.13721),
    "Kakinada 3": (16.89717, 82.23543),
    "Rajahmundry-1": (17.02173, 81.65886),
    "Rajahmundry 2": (17.02173, 81.65886),
    "Nellore": (14.60333, 79.96064),
    "Bhopal": (23.25132, 77.53396),
    "Kurnool": (15.65461, 77.97856),
    "Malegaon": (20.60897, 74.62382),
    "Akola": (20.63028, 76.98194),
    "Hapur (Gaziabad)": (28.70217, 77.77188),
    "Kota": (25.19562, 76.00716),
    "Indore": (22.86608, 75.96125),
    "Yawatmal": (20.43247, 77.96905),
    "Surat(Navsari)": (20.91193, 73.01233),
    "Suratgarh": (29.33278, 73.89899),
    "METC J- Expansion": (28.53056, 76.81444),
    "Dhenkanal-2": (20.72582, 85.51291),
}

# ---------- CITY SELECT ----------
with st.container():
    selected_city = st.selectbox("Choose a city:", sorted(default_places.keys()))
lat, lon = default_places[selected_city]
city_label = selected_city
st.markdown(f"### 📍 Forecast for: `{city_label}`")

# ---------- FETCH WEATHER ----------
@st.cache_data(ttl=1800)
def fetch_weather_data(lat, lon):
    api_url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&hourly=precipitation&forecast_days=14&timezone=auto"
    )
    response = requests.get(api_url, verify=False)
    return response.json()

# ---------- PREPARE DATA ----------
data = fetch_weather_data(lat, lon)
df = pd.DataFrame({
    "time": data["hourly"]["time"],
    "precipitation": data["hourly"]["precipitation"]
})
df["time"] = pd.to_datetime(df["time"])
df["date"] = df["time"].dt.date
df["hour"] = df["time"].dt.hour

# ---------- RAIN COLOR SCALE ----------
def rain_color(val):
    if val == 0:
        return "#D3D3D3"  # No Rain - Light Grey
    elif 0 < val <= 0.04:
        return "#ADD8E6"  # Trace Rain - Light Blue
    elif 0.05 <= val <= 2.4:
        return "#A0C4FF"  # Very Light Rain - Soft Blue
    elif 2.5 <= val <= 7.5:
        return "#7FB77E"  # Light Rain - Green
    elif 7.6 <= val <= 35.5:
        return "#FFD700"  # Moderate Rain - Yellow
    elif 35.6 <= val <= 64.4:
        return "#FF8C00"  # Rather Heavy - Orange
    elif 64.5 <= val <= 124.4:
        return "#FF4500"  # Heavy - Orange Red
    elif 124.5 <= val <= 244.4:
        return "#DC143C"  # Very Heavy - Crimson
    else:
        return "#8B0000"  # Extremely Heavy - Dark Red

# ---------- STATE MGMT ----------
if "expanded_day" not in st.session_state:
    st.session_state.expanded_day = None

# ---------- FULL-DAY EXPANDED VIEW ----------
if st.session_state.expanded_day:
    day = st.session_state.expanded_day
    st.markdown(f"## 🗓️ {day.strftime('%d').lstrip('0')} {day.strftime('%B')} {day.year} - Hourly Rainfall")
    day_df = df[df["date"] == day]
    subcols = st.columns(6)
    for idx, row in day_df.iterrows():
        with subcols[idx % 6]:
            st.markdown(
                f"<div style='background-color:{rain_color(row['precipitation'])}; padding:10px; border-radius:6px; margin-bottom:8px;'>"
                f"<b>{row['time'].strftime('%H:%M')}</b><br>🌧️ {row['precipitation']:.1f} mm</div>",
                unsafe_allow_html=True
            )
    if st.button("⬅️ Back to Calendar View"):
        st.session_state.expanded_day = None
        st.stop()

# ---------- CALENDAR GRID VIEW ----------
st.markdown("### 🗓️ Calendar View")
rows = [df["date"].unique()[i:i+7] for i in range(0, len(df["date"].unique()), 7)]
