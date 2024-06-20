import os
import schedule
import time
import threading
from dotenv import load_dotenv
from flask import Flask, render_template, jsonify
from controllers.send_sms import load_recipients, load_messages, initialize_sms_service, send_bulk_sms, initialize_application
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# Load environment variables
load_dotenv()

username = os.getenv('AFRICASTALKING_USERNAME')
api_key = os.getenv('AFRICASTALKING_APIKEY')
if not username or not api_key:
    logging.error("AFRICASTALKING_USERNAME or AFRICASTALKING_APIKEY not found in environment variables.")
sms = initialize_sms_service(username, api_key)


RECIPIENTS_FILE = 'recipients.json'
MESSAGES_FILE = 'messages.json'
TIMEZONE = 'Africa/Nairobi'


@app.route('/home')
def hello_world():
    return 'Hello World!'


@app.route('/', methods=['GET'])
def get_recipients():
    try:
        recipients = load_recipients(RECIPIENTS_FILE)
        messages = load_messages(MESSAGES_FILE)

        balance_info = initialize_application(username, api_key)
        actual_balance = balance_info['UserData']['balance']

        logging.debug(f"Balance: {actual_balance}")

        balance = actual_balance
        return render_template("recipients.html", recipients=recipients, messages=messages, balance=balance)
    except Exception as e:
        logging.error(f"Error in get_recipients: {e}")
        return "Error fetching recipients and messages", 500


@app.route('/balance', methods=['GET'])
def get_balance():
    try:
        balance_info = initialize_application(username, api_key)
        actual_balance = balance_info['UserData']['balance']
        return jsonify(balance=actual_balance)
    except Exception as e:
        logging.error(f"Error in get_balance: {e}")
        return jsonify(error=str(e)), 500


def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    try:
        # Schedule the SMS sending task
        schedule.every(5).minutes.do(send_bulk_sms, sms=sms, recipients_file=RECIPIENTS_FILE, messages_file=MESSAGES_FILE, timezone=TIMEZONE)
        logging.info("Scheduler initialized")

        # Start the scheduler in a separate thread
        scheduler_thread = threading.Thread(target=run_scheduler)
        scheduler_thread.daemon = True
        scheduler_thread.start()
        logging.info("Scheduler thread started")

        # Start the Flask application
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        logging.error(f"Error in main execution: {e}")
