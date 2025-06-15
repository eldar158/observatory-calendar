from skyfield.api import load, Topos, Star
from astro_bodies import planets, double_star_catalog, dso_catalog
eph = load('de421.bsp')
ts = load.timescale()



def moon_emoji(illum):
    if illum < 0.35: return '🌒'
    elif illum < 0.6: return '🌓'
    elif illum < 0.88: return '🌔'
    else: return '🌕'


def get_rising_setting(body, t, observer):
    obs = eph['earth'] + observer
    ra, _, _ = obs.at(t).observe(body).radec()
    lst = observer.lst_hours_at(t)
    ha = (lst - ra.hours) % 24
    if ha > 12:
        ha -= 24
    return "rising" if ha < 0 else "setting"


def get_object_info(name, he_name, body, symbol, t, observer, is_moon=False):
    obs = eph['earth'] + observer
    app = obs.at(t).observe(body).apparent()
    alt, _, _ = app.altaz()
    status = get_rising_setting(body, t, observer)
    he_status = 'זורח' if status == 'rising' else 'שוקע'

    obj = {
        "name": name,
        "he_name": he_name,
        "altitude": round(alt.degrees, 1),
        "status": status,
        "he_status": he_status,
        "symbol": symbol
    }

    if is_moon:
        illum = app.fraction_illuminated(eph['sun'])
        obj["illumination"] = round(illum, 2)
        obj["symbol"] = moon_emoji(illum)

    return obj


def generate_astro_bodies_json(lat, lon, dt_utc):
    observer = Topos(latitude_degrees=lat, longitude_degrees=lon)
    t = ts.from_datetime(dt_utc)

    result = {
        "moon": get_object_info("Moon", "ירח", eph['moon'], "", t, observer, is_moon=True),
        "planets": [],
        "double_stars": [],
        "dsos": [],
    }

    for key, (name, he_name, symbol, ra, dec) in planets.items():
        star = eph[name.lower()+ ' barycenter']
        result["planets"].append(get_object_info(name, he_name, star, symbol, t, observer))

    for key, (name, he_name, symbol, ra, dec) in double_star_catalog.items():
        star = Star(ra_hours=ra, dec_degrees=dec)
        result["double_stars"].append(get_object_info(name, he_name, star, symbol, t, observer))

    for key, (name, he_name, symbol, ra, dec) in dso_catalog.items():
        star = Star(ra_hours=ra, dec_degrees=dec)
        result["dsos"].append(get_object_info(name, he_name, star, symbol, t, observer))


    return result
