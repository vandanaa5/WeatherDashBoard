import streamlit as st

'''geocoding API : to help to convert location name to lat and long
weather API : to get the weather data for the given lat and long
'''
st.set_page_config(page_title="Weather App", page_icon=":sun_with_face:", layout="wide")

WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm (any intensity)",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail"
}
 
def get_wmo(code):
    return WMO_CODES.get(code, "Unknown weather condition")

def wind_direction(degree):
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    deg = ((degree/45)%8)
    return directions[int(deg)]

def geocode(city):
    import requests
    r = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 5, "language": "en", "format": "json"},
        timeout=8
    )
    r.raise_for_status() # 200: success, 300: redirection, 400: client error, 500: server error
    return r.json().get("results", [])
   
def fetch_weather(lat, lon):
    import requests
    r = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": lat,
                 "longitude": lon,
                   "current": "temperature_2m,windspeed_10m,apparent_temperature,relative_humidity_2m,weather_code,winddirection_10m,precipitation,uv_index",
                   "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,uv_index_max,weather_code",
                   "hourly": "temperature_2m,precipitation_probability",
                   "timezone":"auto",
                   "forecast_days":7
                   },
        timeout=10
    )
    r.raise_for_status()
    return r.json()

st.title("Weather App :sun_with_face:")
st.caption("Get the current weather and 7-day forecast for any city in the world.")

city_input = st.text_input("Enter a city name", placeholder="e.g. New York, London, Tokyo")

unit = st.radio("Select temperature unit", ("Celsius", "Fahrenheit"), horizontal=True)

if not city_input:
    st.info("Please enter a city name to get the weather information.") 
    st.stop()

with st.spinner("Fetching location data..."):
    try:
        locations = geocode(city_input)
        if not locations:
            st.error("Invalid city name. Please enter a valid city.")
            st.stop()
    except Exception as e:
        st.error(f"Error fetching location data: {e}")
        st.stop()

options = [f"{loc['name']}, {loc.get('country', '')}, {loc.get('admin1', '')}" for loc in locations]
selected_location = st.selectbox("Select a location", range(len(options)), format_func=lambda x: options[x])
res = locations[selected_location]

with st.spinner("Fetching weather data..."):
    try:
        data = fetch_weather(res["latitude"], res["longitude"])
    except Exception as e:
        st.error(f"Error fetching weather data: {e}")
        st.stop()

cur = data.get("current")
daily = data.get("daily")
hourly = data.get("hourly")

def fmt (c):
    return round(c*9/5+32, 1) if unit == "Fahrenheit" else c   
 
#current weather

st.divider()
st.subheader(f"Current Weather -- {options[selected_location]}")
st.metric("Temperature", f"{fmt(cur['temperature_2m'])}°{unit}", delta=f"Feels like {fmt(cur['apparent_temperature'])}°{unit}")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Humidity", f"{cur['relative_humidity_2m']}%")
with col2:
    st.metric("Precipitation", f"{cur['precipitation']}mm")
with col3:
    st.metric("Wind Speed", f"{cur['windspeed_10m']}km/h")
with col4:
    st.metric("Wind Direction", f"{wind_direction(cur['winddirection_10m'])}")
with col5:
    st.metric("UV Index", f"{cur['uv_index']}")

st.caption(f"Conditions: {get_wmo(cur['weather_code'])}")

# 7-day forecast
st.divider()
st.subheader("7-Day Forecast")

# Emoji mapping for weather codes
WEATHER_EMOJIS = {
    0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️", 45: "🌫️", 48: "🌫️",
    51: "🌦️", 53: "🌦️", 55: "🌧️", 56: "🌨️", 57: "🌨️",
    61: "🌦️", 63: "🌧️", 65: "⛈️", 66: "🌨️", 67: "🌨️",
    71: "🌨️", 73: "🌨️", 75: "❄️", 77: "🌨️",
    80: "🌦️", 81: "🌧️", 82: "⛈️", 85: "🌨️", 86: "❄️",
    95: "⛈️", 96: "⛈️", 99: "⛈️"
}

cols = st.columns(7)
for i in range(7):
    with cols[i]:
        date = daily["time"][i]
        max_temp = fmt(daily["temperature_2m_max"][i])
        min_temp = fmt(daily["temperature_2m_min"][i])
        precipitation = daily["precipitation_sum"][i]
        weather_code = daily["weather_code"][i]
        emoji = WEATHER_EMOJIS.get(weather_code, "🌍")
        
        st.metric(date, f"{max_temp}°{unit}", delta=f"Low: {min_temp}°{unit}")
        st.caption(f"{emoji} {get_wmo(weather_code)}")
        st.caption(f"Precipitation: {precipitation}mm")