import requests
import datetime
import pytz

from skyfield.api import load, Topos
from skyfield import almanac

from config import SAT_API_KEY, SAT_API_ADRESS, LAT, LON, ALT, TIMEZONE_NAME

tz =  pytz.timezone(TIMEZONE_NAME)

# Skyfield setup
ts = load.timescale()
eph = load('de421.bsp')
observer = Topos(latitude_degrees=LAT, longitude_degrees=LON, elevation_m=ALT)


SATELLITES = {
    'ISS': {
        'id': 25544,
        'symbol': '🛰️',
        'name': 'The international space station',
        'he_name': 'תחנת החלל הבין לאומית',
        'min_elevation': 25,
        'min_minutes_after_sunset': 20,
        'max_minutes_after_sunset': 110,
    },

    'Tiangong': {
        'id': 48274,
        'symbol': '🛰️',
        'name': 'The Chinese space station',
        'he_name': 'תחנת החלל הסינית',
        'min_elevation': 50,
        'min_minutes_after_sunset': 40,
        'max_minutes_after_sunset': 110,
    },

    'Hubble': {
        'id': 20580,
        'symbol': '🛰️',
        'name': 'The Hubble space telescope',
        'he_name': 'טלסקופ החלל האבל',
        'min_elevation': 35,
        'min_minutes_after_sunset': 40,
        'max_minutes_after_sunset': 110,
    }
}


COMPASS_TRANSLATIONS = {
    'N':   {'en': 'North',         'he': 'צפון'},
    'NNE': {'en': 'North-Northeast', 'he': 'צפון צפון-מזרח'},
    'NE':  {'en': 'Northeast',     'he': 'צפון-מזרח'},
    'ENE': {'en': 'East-Northeast','he': 'מזרח צפון-מזרח'},
    'E':   {'en': 'East',          'he': 'מזרח'},
    'ESE': {'en': 'East-Southeast','he': 'מזרח דרום-מזרח'},
    'SE':  {'en': 'Southeast',     'he': 'דרום-מזרח'},
    'SSE': {'en': 'South-Southeast','he': 'דרום דרום-מזרח'},
    'S':   {'en': 'South',         'he': 'דרום'},
    'SSW': {'en': 'South-Southwest','he': 'דרום דרום-מערב'},
    'SW':  {'en': 'Southwest',     'he': 'דרום-מערב'},
    'WSW': {'en': 'West-Southwest','he': 'מערב דרום-מערב'},
    'W':   {'en': 'West',          'he': 'מערב'},
    'WNW': {'en': 'West-Northwest','he': 'מערב צפון-מערב'},
    'NW':  {'en': 'Northwest',     'he': 'צפון-מערב'},
    'NNW': {'en': 'North-Northwest','he': 'צפון צפון-מערב'},
}


def get_sunset_local(date):
    t0 = ts.utc(date.year, date.month, date.day)
    t1 = ts.utc(date.year, date.month, date.day + 1)
    f = almanac.sunrise_sunset(eph, observer)
    times, events = almanac.find_discrete(t0, t1, f)
    for ti, ev in zip(times, events):
        if ev == 0:  # sunset
            return ti.astimezone(tz)
    return None


def is_within_sunset_window(local_start, min_minutes, max_minutes):
    sunset = get_sunset_local(local_start.date())
    if not sunset:
        return False
    delta_min = (local_start - sunset).total_seconds() / 60
    return min_minutes <= delta_min <= max_minutes


def get_passes(sat_info, days):
    sat_id = sat_info['id']
    min_el = sat_info['min_elevation']
    min_after = sat_info['min_minutes_after_sunset']
    max_after = sat_info['max_minutes_after_sunset']

    url = f'{SAT_API_ADRESS}/{sat_id}/{LAT}/{LON}/{ALT}/{days}/30?apiKey={SAT_API_KEY}'
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    result = []

    for p in data.get('passes', []):
        if p.get('maxEl', 0) < min_el: continue
        start_utc = datetime.datetime.fromtimestamp(p['startUTC'], tz=pytz.utc)
        local_start = start_utc.astimezone(tz)
        if not is_within_sunset_window(local_start, min_after, max_after): continue

        end_utc = datetime.datetime.fromtimestamp(p['endUTC'], tz=pytz.utc)
        result.append({
            'start': local_start.isoformat(),
            'end': end_utc.astimezone(tz).isoformat(),
            'duration_seconds': p['duration'],
            'startAzCompass': p['startAzCompass'],
            'endAzCompass': p['endAzCompass'],
            'max_elevation': p['maxEl']
        })

    return result



def generate_satellite_passes_json(days=10):
    sats_json = []
    for key, info in SATELLITES.items():
        passes = get_passes(info, days)
        for p in passes:
            sats_json.append({
                'key': key,
                'name': info['name'],
                'he_name': info['he_name'],
                'symbol': info['symbol'],
                'start': p['start'],
                'end': p['end'],
                'duration_seconds': p['duration_seconds'],
                'max_elevation': p['max_elevation'],
                'startAzCompass': p['startAzCompass'],
                'endAzCompass': p['endAzCompass'],
            })
    return sats_json


def format_pass_description(pass_data, sat_info, lang='he'):
    start_dt = datetime.datetime.fromisoformat(pass_data['start']).astimezone(tz)
    end_dt = datetime.datetime.fromisoformat(pass_data['end']).astimezone(tz)

    start_str = start_dt.strftime('%H:%M')
    end_str = end_dt.strftime('%H:%M')

    max_el = round(pass_data['max_elevation'])

    # Translate directions
    start_az = COMPASS_TRANSLATIONS.get(pass_data.get('startAzCompass', ''), {}).get(lang, pass_data.get('startAzCompass', ''))
    end_az = COMPASS_TRANSLATIONS.get(pass_data.get('endAzCompass', ''), {}).get(lang, pass_data.get('endAzCompass', ''))

    if lang == 'he':
        return (
            f"מעבר של {sat_info['he_name']} "
            f"משעה {start_str} עד {end_str}, "
            f"מכיוון {start_az} לכיוון {end_az}, "
            f"בגובה מירבי של {max_el}°"
        )
    else:
        return (
            f"Pass of {sat_info['name']} "
            f"from {start_str} to {end_str}, "
            f"rising in the {start_az} and setting in the {end_az}, "
            f"with a maximum elevation of {max_el}°"
        )

