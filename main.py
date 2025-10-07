#!/usr/bin/env python3
import sys, requests
from datetime import datetime


# ----- config -----
DEFAULT_CITY = "Seattle"
GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WX_URL  = "https://api.open-meteo.com/v1/forecast"

def f_to_c(f):
    return (f - 32) * 5/9

# ----- weather code map -----
WMO = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Light rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Light snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Light rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Light snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}

def wmo_to_text(code: int) -> str:
    return WMO.get(code, f"Code {code}")

def fail(msg: str, code: int = 1):
    print(msg)
    raise SystemExit(code)

def main():
    raw = " ".join(sys.argv[1:]).strip()
    raw = raw.split("#", 1)[0].strip()   # ignore accidental comments
    city = raw or DEFAULT_CITY
    unit = input("Unit (c/f)? ").strip().lower() or "f"

    # --- geocode ---
    try:
        r = requests.get(GEO_URL, params={"name": city, "count": 1}, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data.get("results"):
            fail(f"Could not geocode city: {city}")
        lat = data["results"][0]["latitude"]
        lon = data["results"][0]["longitude"]
        pretty_name = data["results"][0]["name"]
    except requests.RequestException as e:
        fail(f"Network error (geocoding): {e}")

    # --- weather (current) ---
    try:
        r = requests.get(
            WX_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,weather_code",
                "temperature_unit": "fahrenheit",
                "timezone": "auto",
            },
            timeout=10,
        )
        r.raise_for_status()
        wx = r.json().get("current", {})
        temp_f = wx.get("temperature_2m")
        code = int(wx.get("weather_code"))
    except requests.RequestException as e:
        fail(f"Network error (weather): {e}")

    # --- convert + print ---
    if unit == "c":
        temp = f_to_c(temp_f)
        suffix = "°C"
    else:
        temp = temp_f
        suffix = "°F"

    print(f"{pretty_name}: {temp:.1f}{suffix}, {wmo_to_text(code)}")

    # Timestamp (prefer API time; fallback to local)
    as_of = wx.get("time") if isinstance(wx.get("time"), str) else None
    if not as_of:
        as_of = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    print(f"As of {as_of}")



if __name__ == "__main__":
    main()
