from __future__ import print_function
import datetime
import os.path
import pytz

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from astro_front_helpers import get_visible_objects, generate_description, get_emoji_summary

from config import LAT, LON, TIMEZONE_NAME, CALENDAR_ID, EVENT_TAG_KEY, EVENT_UPDATED_TAG_KEY



def authenticate_google_calendar():
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds)


def update_event_with_astro_data(event, service):
    # # Skip if already updated
    # extended = event.get('extendedProperties', {}).get('private', {})
    # if extended.get('astro_updated') == 'true':
    #     print(f"⏭️ Skipping already-updated event: {event['summary']}")
    #     return

    start_str = event['start'].get('dateTime')
    end_str = event['end'].get('dateTime')
    if not start_str or not end_str:
        return

    tz =  pytz.timezone(TIMEZONE_NAME)
    start_dt = datetime.datetime.fromisoformat(start_str).astimezone(tz)
    end_dt = datetime.datetime.fromisoformat(end_str).astimezone(tz)

    visible = get_visible_objects(start_dt, end_dt, LAT, LON)
    if not visible:
        return

    summary_emojis = get_emoji_summary(visible)
    description = generate_description(visible, 'hebrew')

    base_title = base_title = event['summary'].split("  ")[0].strip() #using 2 spaces before the emojis
    updated_summary = base_title + "  " + summary_emojis

    updated_event = {
        'summary': updated_summary,
        'description': description,
        'extendedProperties': {
            'private': {
                EVENT_TAG_KEY: 'true',
                EVENT_UPDATED_TAG_KEY: 'true'
            }
        }
    }

    service.events().patch(calendarId=CALENDAR_ID, eventId=event['id'], body=updated_event).execute()
    print(f"✅ Updated event: {updated_summary}")


def main():
    service = authenticate_google_calendar()
    now = datetime.datetime.now(pytz.utc).isoformat()
    six_months = (datetime.datetime.now(pytz.utc) + datetime.timedelta(days=180)).isoformat()

    events_result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=now,
        timeMax=six_months,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    events = events_result.get('items', [])

    for event in events:
        title = event.get('summary', '')
        
        if 'ערב קהל במצפה' in title:
            # start_dt = datetime.datetime.fromisoformat(event['start']['dateTime']).astimezone(pytz.timezone(TIMEZONE_NAME))
            # if start_dt.date() == datetime.date(2025, 6, 3):  # year, month, day
            #     update_event_with_astro_data(event, service)
            update_event_with_astro_data(event, service)

if __name__ == '__main__':
    main()
