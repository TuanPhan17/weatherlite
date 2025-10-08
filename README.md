# Weatherlite ☀️🌧️

A minimal command-line weather app powered by the [Open-Meteo API](https://open-meteo.com/).  
Displays current weather conditions for any city with temperature, humidity, and wind speed.

---

## 🚀 Features
- Command-line arguments (no prompts)
- City auto-geocoding via Open-Meteo
- Displays:
  - Temperature (°F / °C)
  - Weather description
  - Relative humidity (%)
  - Wind speed (mph)
- Smart city handling (e.g. `Los Angeles, California` works)
- Timestamped local time display

---

## 🧩 Usage
```bash
# Default city (Seattle)
python3 main.py

# Specific city
python3 main.py "Los Angeles"

# City + State (auto-handles commas)
python3 main.py "Los Angeles, California"

# Celsius output
python3 main.py "Paris" -u c





