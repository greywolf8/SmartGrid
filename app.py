from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from flask_cors import CORS
import os
import json
import tempfile

app = Flask(__name__)
CORS(app)

# Initialize Firebase
firebase_credentials_path = "/etc/secrets/FIREBASE_CREDENTIALS"  # Default secret file path in Render

if not os.path.exists(firebase_credentials_path):
    raise ValueError("Firebase credentials file is missing. Make sure you added it as a secret file in Render.")

# Load the JSON credentials from the file
with open(firebase_credentials_path, "r") as f:
    cred_dict = json.load(f)

# Create a temporary file for Firebase credentials
with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix=".json") as temp_cred_file:
    json.dump(cred_dict, temp_cred_file)
    temp_cred_file.flush()  # Ensure data is written before Firebase reads it

# Initialize Firebase with the temporary credential file
cred = credentials.Certificate(temp_cred_file.name)

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
