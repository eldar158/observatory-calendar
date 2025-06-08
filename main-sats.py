import datetime
import pytz

from config import CALENDAR_ID, SAT_TAG_KEY, TIMEZONE_NAME
from get_sat_passes import generate_satellite_passes_json, format_pass_description

# importing from main is stupid i need to make the structure normal
from main import authenticate_google_calendar



def delete_existing_satellite_events(service, time_min, time_max):
    events = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=time_min.isoformat(),
        timeMax=time_max.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute().get('items', [])

    for event in events:
        props = event.get('extendedProperties', {}).get('private', {})
        if props.get(SAT_TAG_KEY) == 'true':
            service.events().delete(calendarId=CALENDAR_ID, eventId=event['id']).execute()
            print(f"❌ Deleted satellite event: {event.get('summary', '')}")


def create_satellite_events(service, days_ahead=10, lang='he'):
    now = datetime.datetime.now(pytz.utc)
    until = now + datetime.timedelta(days=days_ahead)

    # Step 1: Delete existing tagged satellite events
    delete_existing_satellite_events(service, now, until)

    # Step 2: Create new events for each pass
    passes = generate_satellite_passes_json(days=days_ahead)
    for p in passes:
        description = format_pass_description(p, p, lang='he') #!why p and then p again fix!
        sat_name = p['he_name'] if lang == 'he' else p['name']
        event = {
            'summary': f"{p['symbol']} {sat_name}",
            'description': description,
            'start': {'dateTime': p['start'], 'timeZone': TIMEZONE_NAME},
            'end': {'dateTime': p['end'], 'timeZone': TIMEZONE_NAME},
            'extendedProperties': {
                'private': {
                    SAT_TAG_KEY: 'true'
                }
            }
        }

        service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        print(f"🆕 Created satellite event: {event['summary']}")




service = authenticate_google_calendar()
create_satellite_events(service)