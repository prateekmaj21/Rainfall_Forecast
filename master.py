import streamlit as st
import requests
import pandas as pd
from datetime import datetime
 
# ---------- CONFIG ----------
st.set_page_config(page_title="Rain Calendar", layout="wide")
st.title("🌧️ 14-Day Rainfall Forecast Calendar")
 
# ---------- PREDEFINED LOCATIONS ----------
default_places = {
    "Vadodara": (22.3, 73.19),
    "Nagpur": (21.15, 79.09),
    "Nagothane": (18.54, 73.19),
    "Jhajjar": (28.6, 76.65),
    "Kakinada": (16.93, 82.22),
    "Dhenkanal": (20.65, 85.6),
}
 
# ---------- UI INPUT ----------
selected_city = st.selectbox("Choose a city:", list(default_places.keys()))
lat, lon = default_places[selected_city]
city_label = selected_city
st.markdown(f"### 📍 Forecast for: `{city_label}`")
 
@st.cache_data(ttl=1800)
def fetch_weather_data(lat, lon):
    api_url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&hourly=precipitation&forecast_days=14&timezone=auto"
    )
    response = requests.get(api_url, verify=False)
    return response.json()
 
# ---------- FETCH & PREPARE DATA ----------
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
    if val < 1:
        return "#ADD8E6"  # Light Blue
    elif val <= 5:
        return "#FFBF00"  # Amber
    else:
        return "#FF3333"  # Pleasant Red
 
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
 
for week in rows:
    cols = st.columns(7)
    for i, day in enumerate(week):
        day_df = df[df["date"] == day]
        total_rain = day_df["precipitation"].sum()
        avg_rain = day_df["precipitation"].mean()
        color = rain_color(total_rain)  # apply logic based on total rain
 
        with cols[i]:
            label_date = f"{day.strftime('%d')} {day.strftime('%B')}, {day.year}"
            label_rain = f"Total🌧️{total_rain:.1f} mm"
            label = f"{label_date}\n{label_rain}"
 
            if st.button(label, key=f"day_{day}"):
                st.session_state.expanded_day = day
                st.stop()
 
            st.markdown(
                f"<div style='background-color:{color}; height:6px; border-radius:4px; margin-top:4px;'></div>",
                unsafe_allow_html=True
            )
