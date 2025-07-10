import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ---------- CONFIG ----------
st.set_page_config(page_title="Rain Calendar", layout="wide")
st.title("🌧️ 14-Day Rainfall Forecast Calendar")

# ---------- USER GUIDE ----------
with st.expander("ℹ️ How to Use This App", expanded=True):
    st.markdown("""
**Welcome to the Rainfall Forecast Calendar!** Here's how you can explore the 14-day rainfall forecast:

1. **📍 Select a City** from the dropdown menu — choose from over 20 locations across India.
2. **📅 View Calendar**: The forecast is shown in a weekly grid.
   - Each block shows the **total rainfall** for the day.
   - Colored bars below each date indicate intensity (legend at bottom).
3. **🔍 Click Any Day** to view the **hourly rainfall** breakdown with time and intensity.
4. **⬅️ Go Back**: Use the "Back to Calendar View" button to return to the full calendar.
5. **🌈 Rainfall Intensity Legend** at the bottom helps interpret rainfall levels.
   - From *No Rain* to *Extremely Heavy Rain*, color-coded from grey to dark red.

---

This app is powered by real-time data from [Open-Meteo](https://open-meteo.com/) and updates every 30 minutes.

Enjoy planning your week ahead! ☔
    """)

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

# ---------- RAIN COLOR SCALE ----------
def rain_color(val):
    if val == 0:
        return "#D3D3D3"  # No Rain
    elif 0 < val <= 0.04:
        return "#ADD8E6"  # Trace Rain
    elif 0.04 < val <= 2.4:
        return "#A0C4FF"  # Very Light
    elif 2.4 < val <= 7.5:
        return "#7FB77E"  # Light
    elif 7.5 < val <= 35.5:
        return "#FFD700"  # Moderate
    elif 35.5 < val <= 64.4:
        return "#FF8C00"  # Rather Heavy
    elif 64.4 < val <= 124.4:
        return "#FF4500"  # Heavy
    elif 124.4 < val <= 244.4:
        return "#DC143C"  # Very Heavy
    else:
        return "#8B0000"  # Extreme

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

    st.markdown("""<style>
        .calendar-box, .hour-box {
            border-radius: 10px;
            padding: 10px;
            margin-bottom: 10px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        }
        .hour-box {
            text-align: center;
            font-size: 14px;
            font-weight: 500;
        }
        .rain-bar {
            height: 6px;
            border-radius: 4px;
            margin-top: 4px;
        }
    </style>""", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("## 📊 Rain Summary")
        total_rain_all = df["precipitation"].sum()
        st.metric("Total Rain (14 Days)", f"{total_rain_all:.1f} mm")

        df_daily = df.groupby("date")["precipitation"].sum().reset_index()
        df_daily["week"] = ((df_daily.index) // 7) + 1
        weekly_totals = df_daily.groupby("week")["precipitation"].sum()

        for i, rain in weekly_totals.items():
            st.metric(f"Week {i} Total", f"{rain:.1f} mm")

        st.markdown("---")
        avg_daily = df_daily["precipitation"].mean()
        wettest_day = df_daily.loc[df_daily["precipitation"].idxmax()]
        driest_day = df_daily.loc[df_daily["precipitation"].idxmin()]

        st.write("**Daily Avg Rainfall**")
        st.code(f"{avg_daily:.1f} mm/day")

        st.write("**Wettest Day**")
        st.code(f"{wettest_day['date']}: {wettest_day['precipitation']:.1f} mm")

        st.write("**Driest Day**")
        st.code(f"{driest_day['date']}: {driest_day['precipitation']:.1f} mm")

    if st.session_state.expanded_day:
        day = st.session_state.expanded_day
        st.markdown(f"## 🗓️ {day.strftime('%d').lstrip('0')} {day.strftime('%B')} {day.year} - Hourly Rainfall")

        day_df = df[df["date"] == day]
        subcols = st.columns(6)
        for idx, row in day_df.iterrows():
            with subcols[idx % 6]:
                st.markdown(
                    f"<div class='hour-box' style='background-color:{rain_color(row['precipitation'])};'>"
                    f"<b>{row['time'].strftime('%H:%M')}</b><br>🌧️ {row['precipitation']:.1f} mm</div>",
                    unsafe_allow_html=True
                )
        st.markdown("---")
        if st.button("⬅️ Back to Calendar View"):
            st.session_state.expanded_day = None
            st.stop()

    else:
        st.markdown("### 🗓️ Calendar View")
        rows = [df["date"].unique()[i:i + 7] for i in range(0, len(df["date"].unique()), 7)]

        for week in rows:
            cols = st.columns(7)
            for i, day in enumerate(week):
                day_df = df[df["date"] == day]
                total_rain = day_df["precipitation"].sum()
                color = rain_color(total_rain)

                with cols[i]:
                    label_date = f"{day.strftime('%d')} {day.strftime('%b')}, {day.year}"
                    label_rain = f"🌧️ {total_rain:.1f} mm"
                    btn_label = f"{label_date}\n{label_rain}"

                    if st.button(btn_label, key=f"day_{day}"):
                        st.session_state.expanded_day = day
                        st.stop()

                    st.markdown(
                        f"<div class='rain-bar' style='background-color:{color};'></div>",
                        unsafe_allow_html=True
                    )

    # ---------- LEGEND ----------
    st.markdown("### 🌈 Rainfall Intensity Legend")
    legend_items = [
        ("No Rain                         ", "#D3D3D3", "black"),
        ("Trace (0.01–0.04 mm)            ", "#ADD8E6", "black"),
        ("Very Light (0.1–2.4 mm)         ", "#A0C4FF", "black"),
        ("Light (2.5–7.5 mm)              ", "#7FB77E", "black"),
        ("Moderate (7.6–35.5 mm)          ", "#FFD700", "black"),
        ("Rather Heavy (35.6–64.4 mm)     ", "#FF8C00", "black"),
        ("Heavy (64.5–124.4 mm)", "#FF4500", "black"),
        ("Very Heavy (124.5–244.4 mm)     ", "#DC143C", "black"),
        ("Extreme (>244.4 mm)             ", "#8B0000", "white"),
    ]

    legend_cols = st.columns(len(legend_items))
    for i, (label, bg_color, text_color) in enumerate(legend_items):
        with legend_cols[i]:
            st.markdown(
                f"""
                <div style='
                    background-color:{bg_color};
                    color:{text_color};
                    padding:10px;
                    border-radius:8px;
                    text-align:center;
                    font-size:13px;
                    min-height:48px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    font-weight:600;
                '>
                    {label}
                </div>
                """,
                unsafe_allow_html=True
            )

# ---------- ENTRY POINT ----------
if __name__ == "__main__":
    main()
