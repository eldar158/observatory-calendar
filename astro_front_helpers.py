from get_astro_bodies import generate_astro_bodies_json

THRESHOLDS = {
    'moon': 10,
    'moon_ilum': 0.05,
    'planets': 20,
    'dsos': 30,
    'double_stars': 30,
}


def get_visible_objects(start_dt, end_dt, lat, lon):
    start = generate_astro_bodies_json(lat, lon, start_dt)
    end = generate_astro_bodies_json(lat, lon, end_dt)

    visible = {
        'moon': None,
        'planets': [],
        'dsos': [],
        'double_stars': []
    }

    if start['moon']['altitude'] >= THRESHOLDS['moon'] or end['moon']['altitude'] >= THRESHOLDS['moon']:
        if start['moon']['illumination'] > THRESHOLDS['moon_ilum']:
            visible['moon'] = start['moon']

    for key in ['planets', 'dsos', 'double_stars']:
        start_objs = {obj['name']: obj for obj in start[key]}
        end_objs = {obj['name']: obj for obj in end[key]}
        all_names = set(start_objs.keys()).union(end_objs.keys())
        for name in all_names:
            start_alt = start_objs.get(name, {}).get('altitude', -999)
            end_alt = end_objs.get(name, {}).get('altitude', -999)
            if max(start_alt, end_alt) >= THRESHOLDS[key]:
                visible[key].append(start_objs.get(name) or end_objs.get(name))

    return visible


def get_emoji_summary(visible_json):
    symbols = set()
    if visible_json['moon']:
        symbols.add(visible_json['moon']['symbol'])
    for key in ['planets', 'dsos', 'double_stars']:
        for obj in visible_json[key]:
            symbols.add(obj['symbol'])
    return ''.join(sorted(symbols))


def generate_description(visible_json, lang):
    if lang == 'hebrew':
        name_field = 'he_name'
        status_field = 'he_status'
    else:
        name_field = 'name'
        status_field = 'status'
    
    lines = []
    if visible_json['moon']:
        m = visible_json['moon']
        lines.append(f"{m['symbol']} {m[name_field]} {m[status_field]} {m['altitude']}°")
    for key in ['planets', 'dsos', 'double_stars']:
        for obj in visible_json[key]:
            lines.append(f"{obj['symbol']} {obj[name_field]} {obj[status_field]} {obj['altitude']}°")
    return '\n'.join(lines)