import json
import requests

# Dictionary of track coordinates to look up for weather forecasting
TRACK_COORDS = {
    'silverstone': {'lat': 52.0786, 'lon': -1.0169},
    'spa':         {'lat': 50.4372, 'lon':  5.9714},
    'monza':       {'lat': 45.6156, 'lon':  9.2811},
    'nurburgring': {'lat': 50.3356, 'lon':  6.9475},
    'bahrain':     {'lat': 26.0325, 'lon': 50.5106},
    'monaco':      {'lat': 43.7347, 'lon':  7.4206},
    'suzuka':      {'lat': 34.8431, 'lon': 136.5407},
    'interlagos':  {'lat': -23.7036, 'lon': -46.6997},
    'australia':   {'lat': -37.8497, 'lon': 144.9680},
    'barcelona':   {'lat': 41.5700, 'lon':  2.2611},
}


def get_track_weather(track_name: str) -> str:
    # Look up the weather for the given F1 circuit using the Open-Meteo API
    
    # Normalize input
    key = track_name.lower().replace(' ', '').replace('-', '')
    
    # Match the input with our keys
    matched = None
    for k in TRACK_COORDS:
        if k in key or key in k:
            matched = k
            break

    if not matched:
        return json.dumps({
            'error': f"Unknown circuit '{track_name}'. Known: {list(TRACK_COORDS)}"
        })

    # Get coordinates
    lat = TRACK_COORDS[matched]['lat']
    lon = TRACK_COORDS[matched]['lon']
    
    # URL query for Open-Meteo API
    url = (
        f'https://api.open-meteo.com/v1/forecast'
        f'?latitude={lat}&longitude={lon}'
        f'&current=temperature_2m,rain,surface_temperature,wind_speed_10m,relative_humidity_2m'
    )

    try:
        r = requests.get(url, timeout=10)
        data = r.json()['current']
        
        # Check if there is rain
        is_wet = 'DRY'
        if data['rain'] > 0:
            is_wet = 'WET'
            
        return json.dumps({
            'circuit':              matched,
            'air_temp_c':           data['temperature_2m'],
            'track_surface_temp_c': data['surface_temperature'],
            'rain_mm':              data['rain'],
            'wind_speed_kmh':       data['wind_speed_10m'],
            'humidity_pct':         data['relative_humidity_2m'],
            'conditions':           is_wet,
        })
    except Exception as e:
        return json.dumps({'error': f'Weather API request failed: {str(e)}'})
