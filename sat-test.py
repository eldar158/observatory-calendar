from get_sat_passes import generate_satellite_passes_json

LAT = 32.0698925
LON = 34.8139346

satellite_passes = generate_satellite_passes_json(LAT, LON, alt=0, days=10)

print(satellite_passes)
