from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, db
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app)

# Load Firebase credentials from the secret file
FIREBASE_SECRET_PATH = "/etc/secrets/firebase-credentials.json"

if not os.path.exists(FIREBASE_SECRET_PATH):
    raise FileNotFoundError(f"Firebase secret file not found at {FIREBASE_SECRET_PATH}")

with open(FIREBASE_SECRET_PATH, "r") as f:
    firebase_credentials = json.load(f)

# Initialize Firebase with credentials from the secret file
cred = credentials.Certificate(firebase_credentials)

if not firebase_admin._apps:  # Prevent re-initialization error
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://smartgrid-70254-default-rtdb.firebaseio.com/'
    })

def process_message(message):
    message = message.lower()
    
    on_keywords = ['on', 'turn on', 'switch on', 'enable']
    off_keywords = ['off', 'turn off', 'switch off', 'disable']
    
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
    
    state = None
    if any(keyword in message for keyword in on_keywords):
        state = 1
    elif any(keyword in message for keyword in off_keywords):
        state = 0
    
    if state is None:
        return "Could not determine if you want to turn something on or off"
    
    if 'streetlight' in message and 'techpark' in message:
        found_section = 'Night_LEDs'
        found_component = 'Streetlights techpark'
    elif 'java' in message and 'streetlight' in message:
        found_section = 'Night_LEDs'
        found_component = 'Java streetlights'
    else:
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
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
