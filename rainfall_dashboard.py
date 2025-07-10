import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ---------- CONFIG ----------
st.set_page_config(page_title="Rain Calendar", layout="wide")
st.markdown("<h1 style='text-align: center;'>🌧️ 14-Day Rainfall Forecast Calendar</h1>", unsafe_allow_html=True)

# ---------- USER GUIDE ----------
with st.expander("ℹ️ How to Use This App", expanded=True):
    st.markdown("""
<div style='background-color:#f9f9f9; padding:10px 20px; border-radius:10px; font-size:15px;'>
Welcome! This dashboard helps you monitor upcoming rainfall at your location.

1. 📍 Select a city from the dropdown menu.
2. 📅 Explore the 14-day rainfall calendar. Each box shows total rainfall.
3. 🔍 Click a date to view hourly breakdown.
4. ⬅️ Use the back button to return.
5. 🌈 Rainfall intensity is color-coded — see legend below.
</div>
""", unsafe_allow_html=True)

# ---------- LOCATIONS ----------
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

# ---------- CITY SELECTION ----------
st.markdown("#### 📍 Select a City")
selected_city = st.selectbox("", sorted(default_places.keys()), label_visibility="collapsed")
lat, lon = default_places[selected_city]
st.markdown(f"<div style='background-color:#e6f4f1; padding:10px 16px; border-radius:10px;'>"
            f"City Selected: {selected_city} (Lat: {lat}, Lon: {lon})</div>", unsafe_allow_html=True)

# ---------- FETCH WEATHER ----------
@st.cache_data(ttl=1800)
def fetch_weather_data(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&hourly=precipitation&forecast_days=14&timezone=auto"
    )
    response = requests.get(url, verify=False)
    return response.json()

# ---------- COLOR SCALE ----------
def rain_color(val):
    if val == 0:
        return "#D3D3D3"
    elif 0 < val <= 0.04:
        return "#ADD8E6"
    elif 0.05 <= val <= 2.4:
        return "#A0C4FF"
    elif 2.5 <= val <= 7.5:
        return "#7FB77E"
    elif 7.6 <= val <= 35.5:
        return "#FFD700"
    elif 35.6 <= val <= 64.4:
        return "#FF8C00"
    elif 64.5 <= val <= 124.4:
        return "#FF4500"
    elif 124.5 <= val <= 244.4:
        return "#DC143C"
    else:
        return "#8B0000"

# ---------- MAIN ----------
def main():
    data = fetch_weather_data(lat, lon)
    df = pd.DataFrame({
        "time": data["hourly"]["time"],
        "precipitation": data["hourly"]["precipitation"]
    })
    df["time"] = pd.to_datetime(df["time"])
    df["date"] = df["time"].dt.date
    df["hour"] = df["time"].dt.hour

    if "expanded_day" not in st.session_state:
        st.session_state.expanded_day = None

    # ---------- EXPANDED VIEW ----------
    if st.session_state.expanded_day:
        day = st.session_state.expanded_day
        st.markdown(f"## 🗓️ {day.strftime('%d').lstrip('0')} {day.strftime('%B')} {day.year} - Hourly Rainfall")
        day_df = df[df["date"] == day]
        subcols = st.columns(6)
        for idx, row in day_df.iterrows():
            with subcols[idx % 6]:
                st.markdown(
                    f"<div style='background-color:{rain_color(row['precipitation'])}; padding:10px; border-radius:8px; margin-bottom:8px; text-align:center;'>"
                    f"{row['time'].strftime('%H:%M')}🌧️ {row['precipitation']:.1f} mm</div>",
                    unsafe_allow_html=True
                )
        if st.button("⬅️ Back to Calendar View"):
            st.session_state.expanded_day = None

    # ---------- CALENDAR GRID ----------
    if not st.session_state.expanded_day:
        st.markdown("### 📆 Rainfall Forecast (Daily)")
        weeks = [df["date"].unique()[i:i+7] for i in range(0, len(df["date"].unique()), 7)]

        for week in weeks:
            cols = st.columns(7)
            for i, day in enumerate(week):
                day_df = df[df["date"] == day]
                total_rain = day_df["precipitation"].sum()
                color = rain_color(total_rain)

                with cols[i]:
                    label = f"{day.strftime('%d')}{day.strftime('%b')} {total_rain:.1f} mm"
                    clicked = st.button(label, key=f"day_{day}")
                    if clicked:
                        st.session_state.expanded_day = pd.to_datetime(day)
                    st.markdown(
                        f"<div style='background-color:{color}; height:6px; border-radius:4px; margin-top:4px;'></div>",
                        unsafe_allow_html=True
                    )

    # ---------- LEGEND ----------
    st.markdown("### 🌈 Rainfall Intensity Legend")
    legend = [
        ("No Rain", "#D3D3D3"),
        ("Trace (0.01–0.04 mm)", "#ADD8E6"),
        ("Very Light (0.1–2.4 mm)", "#A0C4FF"),
        ("Light (2.5–7.5 mm)", "#7FB77E"),
        ("Moderate (7.6–35.5 mm)", "#FFD700"),
        ("Rather Heavy (35.6–64.4 mm)", "#FF8C00"),
        ("Heavy (64.5–124.4 mm)", "#FF4500"),
        ("Very Heavy (124.5–244.4 mm)", "#DC143C"),
        ("Extremely Heavy (>244.4 mm)", "#8B0000"),
    ]

    col_l = st.columns(len(legend))
    for i, (label, color) in enumerate(legend):
        with col_l[i]:
            st.markdown(
                f"<div style='background-color:{color}; padding:6px; border-radius:8px; text-align:center;'>"
                f"<span style='font-size:11px'>{label}</span></div>",
                unsafe_allow_html=True
            )

# ---------- ENTRY ----------
if __name__ == "__main__":
    main()
