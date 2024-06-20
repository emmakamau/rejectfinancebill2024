import json
import africastalking
from datetime import datetime
import pytz

current_message_index = 0


def initialize_sms_service(username, api_key):
    africastalking.initialize(username, api_key)
    return africastalking.SMS


def initialize_application(username, api_key):
    africastalking.initialize(username, api_key)
    application = africastalking.Application
    res = application.fetch_application_data()
    return res


def send_bulk_sms(sms, recipients_file, messages_file, timezone):
    global current_message_index
    now = datetime.now(pytz.timezone(timezone))
    if now.hour < 8 or now.hour >= 17:
        return  # Only run between 9am and 5pm

    recipients = load_recipients(recipients_file)
    messages = load_messages(messages_file)
    if not recipients or not messages:
        print("No recipients or messages found in the JSON file")
        return

    current_message = messages[current_message_index]
    responses = []

    for recipient in recipients:
        if recipient.get('blocked'):
            continue  # Skip blocked recipients

        message = structure_message(recipient.get('name'), current_message)
        try:
            response = sms.send(message, [recipient.get('phone')])
            print(response)
            status = response.get('SMSMessageData', {}).get('Recipients', [{}])[0].get('status', 'Unknown')
            number = response.get('SMSMessageData', {}).get('Recipients', [{}])[0].get('number', 'Unknown')
            response = {'status': status, 'number': number}
            responses.append(response)

            if status.lower() == 'success':
                recipient['message_count'] = recipient.get('message_count', 0) + 1
            elif status == 'UserInBlacklist':
                recipient['blocked'] = True  # Mark recipient as blocked

        except Exception as e:
            print(f'Failed to send message: {e}')
            responses.append({'error': str(e), 'recipient': recipient.get('phone')})

    save_recipients(recipients, recipients_file)
    current_message_index = (current_message_index + 1) % len(messages)
    print("SMS sending task completed with responses:", responses)


def load_recipients(file_path):
    try:
        with open(file_path, 'r') as file:
            recipients = json.load(file)
            sorted_recipients = sorted(recipients, key=lambda r: r.get('blocked', False))
            return sorted_recipients
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f'Error loading recipients: {e}')
        return []


def load_messages(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f'Error loading messages: {e}')
        return []


def save_recipients(recipients, file_path):
    try:
        with open(file_path, 'w') as file:
            json.dump(recipients, file, indent=4)
    except Exception as e:
        print(f'Error saving recipients: {e}')


def structure_message(name, text):
    opt_out = opt_out_text()
    message = f"Hello {name}, {text}. {opt_out}"
    return message


def opt_out_text():
    opt_out = "OPTOUT NEVER"
    return opt_out
