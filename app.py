from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, db
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app)

# Load Firebase credentials from an environment variable
firebase_credentials = os.getenv("FIREBASE_CREDENTIALS")  # Set this in Render

if not firebase_credentials:
    raise ValueError("Firebase credentials are missing! Set the FIREBASE_CREDENTIALS environment variable.")

# Parse JSON credentials
cred_dict = json.loads(firebase_credentials)

# Initialize Firebase
cred = credentials.Certificate(cred_dict)

if not firebase_admin._apps:  # Prevent re-initialization error
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://smartgrid-70254-default-rtdb.firebaseio.com/'
    })

def process_message(message):
    # Convert message to lowercase for easier matching
    message = message.lower()

    # Define keywords for state
    on_keywords = ['on', 'turn on', 'switch on', 'enable']
    off_keywords = ['off', 'turn off', 'switch off', 'disable']

    # Define components and their variations
    components = {
        'Morning_LEDs': {
            'java': 'Java',
            'ub': 'Ub',
            'techpark': 'Techpark',
            'labs': 'Labs'
        },
        'Night_LEDs': {
            'streetlights techpark': 'Streetlights techpark',
            'java streetlights': 'Java streetlights',
            'hostel': 'Hostel block',
            'clocktower': 'Clocktower lighting',
            'arch gate': 'Arch gate street lighting'
        },
        'RED_LED': {
            'server': 'server',
            'net': 'net',
            'hospital': 'hospital'
        }
    }

    # Determine the state (on/off)
    state = None
    if any(keyword in message for keyword in on_keywords):
        state = 1
    elif any(keyword in message for keyword in off_keywords):
        state = 0

    if state is None:
        return "Could not determine if you want to turn something on or off"

    # Special conditions check
    if 'streetlight' in message and 'techpark' in message:
        found_section = 'Night_LEDs'
        found_component = 'Streetlights techpark'
    elif 'java' in message and 'streetlight' in message:
        found_section = 'Night_LEDs'
        found_component = 'Java streetlights'
    else:
        # Find which component is mentioned
        found_section = None
        found_component = None

        for section, items in components.items():
            for keyword, component_name in items.items():
                if keyword.lower() in message.lower():
                    found_section = section
                    found_component = component_name
                    break
            if found_component:
                break

    if not found_component:
        return "Could not identify which component you want to control"

    # Update the component state in Firebase
    try:
        ref = db.reference(f'/{found_section}/{found_component}')
        ref.set(state)
        action = "on" if state == 1 else "off"
        return f"Successfully turned {action} the {found_component}"
    except Exception as e:
        return f"Error occurred: {str(e)}"

@app.route('/')
def home():
    return '''
    <h1>SmartGrid Control System</h1>
    <p>Send POST requests to /control with a JSON body containing a "message" field.</p>
    '''

@app.route('/control', methods=['POST'])
def control():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    if 'message' not in data:
        return jsonify({"error": "Message field is required"}), 400

    result = process_message(data['message'])
    return jsonify({"response": result})

@app.route('/status', methods=['GET'])
def get_status():
    try:
        ref = db.reference('/')
        current_status = ref.get()
        return jsonify(current_status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
