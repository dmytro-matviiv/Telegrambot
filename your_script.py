import datetime
import pytz

# ... existing code ...

def parse_alarm_time(alarm_time_str):
    try:
        alarm_time = datetime.datetime.fromisoformat(alarm_time_str.replace('Z', '+00:00'))
        return alarm_time
    except ValueError:
        return None

def main():
    # ... existing code ...
    for alarm in new_alarms:
        alarm_time_str = alarm['createdAt']
        alarm_time = parse_alarm_time(alarm_time_str)

        if alarm_time:
            now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc) # Ensure 'now' is timezone-aware (UTC)
            time_difference = now - alarm_time.replace(tzinfo=pytz.utc) # Make alarm_time timezone-aware for subtraction
            minutes_since_alarm = time_difference.total_seconds() / 60
