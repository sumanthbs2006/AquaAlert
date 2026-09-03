"""
AquaAlert AI - Configuration & External API Credentials
Stores CARTO, Mappls, and meteorological API configurations.
"""

import os

# Automatically load .env file if present
def _load_env():
    env_paths = [
        os.path.join(os.path.dirname(__file__), "..", ".env"),
        os.path.join(os.path.dirname(__file__), ".env"),
        ".env"
    ]
    for path in env_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k, v = k.strip(), v.strip()
                            if k and k not in os.environ:
                                os.environ[k] = v
                break
            except Exception:
                pass

_load_env()

CARTO_API_KEY = os.environ.get("CARTO_API_KEY", "")
MAPPLS_REST_KEY = os.environ.get("MAPPLS_REST_KEY", "")

# CARTO Basemap Styles with authenticated tile URL templates
CARTO_BASEMAPS = {
    "dark_matter": {
        "id": "dark_matter",
        "name": "CARTO Dark Matter (Tactical Night EOC)",
        "url": f"https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png?key={CARTO_API_KEY}",
        "attribution": "&copy; <a href='https://carto.com/'>CARTO</a> &copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a>",
        "max_zoom": 20
    },
    "voyager": {
        "id": "voyager",
        "name": "CARTO Voyager (Hydrology & Streets)",
        "url": f"https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png?key={CARTO_API_KEY}",
        "attribution": "&copy; <a href='https://carto.com/'>CARTO</a> &copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a>",
        "max_zoom": 20
    },
    "positron": {
        "id": "positron",
        "name": "CARTO Positron (High-Contrast Light)",
        "url": f"https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png?key={CARTO_API_KEY}",
        "attribution": "&copy; <a href='https://carto.com/'>CARTO</a> &copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a>",
        "max_zoom": 20
    },
    "satellite": {
        "id": "satellite",
        "name": "Satellite Hybrid Imagery",
        "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "attribution": "Tiles &copy; Esri, Maxar, Earthstar Geographics",
        "max_zoom": 19
    }
}
