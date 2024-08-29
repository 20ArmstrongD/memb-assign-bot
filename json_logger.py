import json
from datetime import datetime

# Path to the JSON log file
LOG_FILE_PATH = 'member_events.json'

def log_member_event(member_name, event_type, description):
    """Log member events to a JSON file."""
    event_data = {
        'member_name': member_name,
        'event_type': event_type,
        'description': description,
        'timestamp': datetime.now().isoformat()  # Use ISO 8601 format for timestamps
    }

    # add the new event to the JSON log file
    try:
        # read events that are already stored
        with open(LOG_FILE_PATH, 'r') as log_file:
            events = json.load(log_file)
    except (FileNotFoundError, json.JSONDecodeError):
        # the file does not exist or is empty, initialize an empty list
        events = []

    # addthe new event that occured
    events.append(event_data)

    # write back the updated list of events
    with open(LOG_FILE_PATH, 'w') as log_file:
        json.dump(events, log_file, indent=4)  # Pretty-print with indentation

    print(f'Logged event: {description}')  # Print to console for debugging