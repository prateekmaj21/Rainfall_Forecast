import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import altair as alt
# ---------- CONFIG ----------
st.set_page_config(page_title="Rain Calendar", layout="wide")
st.title("🌧️ 14-Day Rainfall Forecast Calendar")



# ---------- PREDEFINED LOCATIONS ----------
default_places = {
    "Jamnagar BETC": (22.397826, 69.909285),
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
        f"&hourly=precipitation&forecast_days=14&timezone=auto&model=gefs"
    )
    try:
        response = requests.get(api_url, verify=False)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"⚠️ Failed to fetch forecast data: {e}")
        return {}

# ---------- FETCH PAST 7-DAY RAINFALL ----------
@st.cache_data(ttl=3600)
def fetch_past_15_days_rainfall(lat, lon):
    end_date = datetime.now().date() #- timedelta(days=1)
    start_date = end_date - timedelta(days=15)
    url = (
        f"https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={lat}&longitude={lon}&start_date={start_date}&end_date={end_date}"
        f"&daily=precipitation_sum&timezone=auto"
    )
    response = requests.get(url, verify=False)
    data = response.json()
    df_hist = pd.DataFrame({
        "Date": pd.to_datetime(data["daily"]["time"]),
        "Rainfall (mm)": data["daily"]["precipitation_sum"]
    })
    return df_hist

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
        st.markdown("## 📊 Rain Forecast Summary")
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

    # ---------- LEGEND SCALE ----------
    st.markdown("### 🌈 Rainfall Intensity Legend")
    legend_html = """
    <div style="display: flex; width: 100%; max-width: 1000px; margin: auto; flex-wrap: wrap;">
      <div style="flex: 1; background-color: #D3D3D3; padding: 10px; text-align: center; font-size: 12px; font-weight: bold; border-radius: 6px 0 0 6px;">No Rain</div>
      <div style="flex: 1; background-color: #ADD8E6; padding: 10px; text-align: center; font-size: 12px; font-weight: bold;">Trace<br>(0.01–0.04)</div>
      <div style="flex: 1; background-color: #A0C4FF; padding: 10px; text-align: center; font-size: 12px; font-weight: bold;">Very Light<br>(0.1–2.4)</div>
      <div style="flex: 1; background-color: #7FB77E; padding: 10px; text-align: center; font-size: 12px; font-weight: bold;">Light<br>(2.5–7.5)</div>
      <div style="flex: 1; background-color: #FFD700; padding: 10px; text-align: center; font-size: 12px; font-weight: bold;">Moderate<br>(7.6–35.5)</div>
      <div style="flex: 1; background-color: #FF8C00; padding: 10px; text-align: center; font-size: 12px; font-weight: bold;">Rather Heavy<br>(35.6–64.4)</div>
      <div style="flex: 1; background-color: #FF4500; padding: 10px; text-align: center; font-size: 12px; font-weight: bold;">Heavy<br>(64.5–124.4)</div>
      <div style="flex: 1; background-color: #DC143C; padding: 10px; text-align: center; font-size: 12px; font-weight: bold;">Very Heavy<br>(124.5–244.4)</div>
      <div style="flex: 1; background-color: #8B0000; color: white; padding: 10px; text-align: center; font-size: 12px; font-weight: bold; border-radius: 0 6px 6px 0;">Extreme<br>(>244.4)</div>
    </div>
    """
    st.markdown(legend_html, unsafe_allow_html=True)

    # ---------- PAST 15-DAY RAINFALL SECTION ----------
    st.markdown("---")
    st.markdown("## ⏳ Past 15 Days Rainfall")

    df_past = fetch_past_15_days_rainfall(lat, lon)

    if not df_past.empty:
        import altair as alt

        total_15d = df_past["Rainfall (mm)"].sum()
        max_day = df_past.loc[df_past["Rainfall (mm)"].idxmax()]
        min_day = df_past.loc[df_past["Rainfall (mm)"].idxmin()]

        st.markdown(f"**📊 Total Rainfall** in Past 15 Days: `{total_15d:.1f} mm`")
        col1, col2 = st.columns(2)
        with col1:
            st.success(f"🌧️ Wettest: {max_day['Date'].date()} — {max_day['Rainfall (mm)']:.1f} mm")
        with col2:
            st.info(f"🌤️ Driest: {min_day['Date'].date()} — {min_day['Rainfall (mm)']:.1f} mm")

        chart = alt.Chart(df_past).mark_bar(size=35).encode(
            x=alt.X("Date:T", title="Date"),
            y=alt.Y("Rainfall (mm):Q", title="Rainfall (mm)"),
            tooltip=["Date:T", "Rainfall (mm):Q"]
        ).properties(
            width="container",
            height=300,
            title="📉 Daily Rainfall Over Last 15 Days"
        ).configure_title(fontSize=16).configure_axis(
            labelFontSize=12,
            titleFontSize=14
        )

        st.altair_chart(chart, use_container_width=True)
    else:
        st.warning("⚠️ Could not retrieve past 15 days rainfall data.")



# ---------- ENTRY POINT ----------
if __name__ == "__main__":
    main()


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

---
This app is powered by real-time data from [Open-Meteo](https://open-meteo.com/) and updates every 30 minutes.
    """)
