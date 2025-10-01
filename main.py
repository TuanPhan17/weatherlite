import sys, datetime as dt, json, os, urllib.parse
import requests

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WX_URL  = "https://api.open-meteo.com/v1/forecast"

CACHE_FILE = "geo_cache.json"

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

def geocode(city: str):
    cache = load_cache()
    key = city.lower().strip()
    if key in cache:
        return cache[key]

    params = {"name": city, "count": 1}
    r = requests.get(GEO_URL, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    if not data.get("results"):
        raise SystemExit(f"Couldn’t find '{city}'. Try a larger city or check spelling.")
    res = data["results"][0]
    lat, lon = res["latitude"], res["longitude"]
    cache[key] = {"lat": lat, "lon": lon, "name": res["name"], "country": res.get("country", "")}
    save_cache(cache)
    return cache[key]

def fetch_weather(lat, lon, tz="auto"):
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "hourly": "temperature_2m,precipitation_probability",
        "timezone": tz,
    }
    r = requests.get(WX_URL, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

def fmt_time(iso_str):
    # iso like "2025-10-01T11:00"
    return iso_str.split("T")[1]

def print_report(city_label, wx):
    cur = wx["current_weather"]
    print(f"\nWeather — {city_label}")
    print("-" * (10 + len(city_label)))
    print(f"Now: {cur['temperature']}°C, wind {cur['windspeed']} km/h at {cur['time']}")

    hours = wx["hourly"]["time"]
    temps = wx["hourly"]["temperature_2m"]
    pops  = wx["hourly"].get("precipitation_probability", [None]*len(hours))

    # find index of current or next hour
    now_iso = cur["time"][:13]  # up to hour
    start_idx = next((i for i, t in enumerate(hours) if t.startswith(now_iso)), 0)

    print("\nNext 12 hours:")
    print("Time  | Temp | POP%")
    print("--------------------")
    for i in range(start_idx+1, min(start_idx + 13, len(hours))):
        t  = fmt_time(hours[i])
        tp = f"{temps[i]:.1f}"
        pp = "" if pops[i] is None else str(pops[i])
        print(f"{t:<5} | {tp:>4} | {pp:>4}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <city name>\nExample: python main.py \"Seattle\"")
        raise SystemExit(1)

    city = " ".join(sys.argv[1:])
    geo = geocode(city)
    wx = fetch_weather(geo["lat"], geo["lon"])
    label = f"{geo['name']}, {geo.get('country','')}".strip().strip(",")
    print_report(label, wx)

if __name__ == "__main__":
    main()
