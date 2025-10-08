#!/usr/bin/env python3
import sys, requests, argparse
from datetime import datetime

# ----- config -----
DEFAULT_CITY = "Seattle"
GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WX_URL  = "https://api.open-meteo.com/v1/forecast"

def f_to_c(f):
    return (f - 32) * 5/9

# ----- weather code map -----
WMO = {
    0:"Clear sky",1:"Mainly clear",2:"Partly cloudy",3:"Overcast",
    45:"Fog",48:"Depositing rime fog",
    51:"Light drizzle",53:"Moderate drizzle",55:"Dense drizzle",
    56:"Light freezing drizzle",57:"Dense freezing drizzle",
    61:"Light rain",63:"Moderate rain",65:"Heavy rain",
    66:"Light freezing rain",67:"Heavy freezing rain",
    71:"Light snow",73:"Moderate snow",75:"Heavy snow",
    77:"Snow grains",
    80:"Light rain showers",81:"Moderate rain showers",82:"Violent rain showers",
    85:"Light snow showers",86:"Heavy snow showers",
    95:"Thunderstorm",96:"Thunderstorm with slight hail",99:"Thunderstorm with heavy hail",
}

def wmo_to_text(code: int) -> str:
    return WMO.get(code, f"Code {code}")

def fail(msg: str, code: int = 1):
    print(msg)
    raise SystemExit(code)

def parse_args():
    p = argparse.ArgumentParser(prog="weatherlite", description="Tiny CLI weather.")
    p.add_argument("city", nargs="*", help="City name (default: Seattle)")
    p.add_argument("-u","--unit", choices=["f","c"], default="f", help="Temperature unit")
    return p.parse_args()

def main():
    args = parse_args()
    city = " ".join(args.city).strip() or DEFAULT_CITY
    unit = args.unit

    # --- geocode ---
    try:
        search_name = city.split(",")[0].strip()  # handles things like "Los Angeles, California"
        r = requests.get(GEO_URL, params={"name": search_name, "count": 1}, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data.get("results"):
            fail(f"Could not geocode city: {city}")
        res0 = data["results"][0]
        lat = res0["latitude"]; lon = res0["longitude"]; pretty_name = res0["name"]
        display_name = city.strip() or pretty_name
    except requests.RequestException as e:
        fail(f"Network error (geocoding): {e}")

    # --- weather (current) ---
    try:
        r = requests.get(
            WX_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,weather_code,relative_humidity_2m,wind_speed_10m",
                "temperature_unit": "fahrenheit",
                "wind_speed_unit": "mph",
                "timezone": "auto",
            },
            timeout=10,
        )
        r.raise_for_status()
        wx = r.json().get("current", {})
        temp_f = wx.get("temperature_2m")
        code = wx.get("weather_code")
        rh = wx.get("relative_humidity_2m")
        wind = wx.get("wind_speed_10m")
        code = int(code) if code is not None else -1
    except requests.RequestException as e:
        fail(f"Network error (weather): {e}")

    # --- convert + print ---
    if temp_f is None:
        fail("Weather data missing temperature.")
    temp = f_to_c(temp_f) if unit == "c" else temp_f
    suffix = "°C" if unit == "c" else "°F"

    cond = wmo_to_text(code)
    parts = [f"{display_name}: {temp:.1f}{suffix}", cond]
    if rh is not None:   parts.append(f"RH {rh}%")
    if wind is not None: parts.append(f"Wind {wind:.0f} mph")
    print(", ".join(parts))

    # Timestamp (prefer API time; fallback to local)
    as_of = wx.get("time") if isinstance(wx.get("time"), str) else None
    if not as_of:
        as_of = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    print(f"As of {as_of}")

if __name__ == "__main__":
    main()

