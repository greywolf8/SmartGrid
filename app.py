from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 🔥 Hardcoded Firebase credentials (Replace with actual values from your JSON file)
firebase_credentials = {
    "type": "service_account",
    "project_id": "smartgrid-70254",
    "private_key_id": "531ce737d4086a87cd4b0753a14d5a614ff69899",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCIVjSm0D89bTme\nkdZECUOTKMu/vCwTfgrs759+FoduGfUFx0XnnTjOM0SBO9Ds80wUEIT81tM/wWMF\nO6RpFGoyU5ciCyAEX+LO0QaQlnw+5ySZgwBTHvlzD19umhxFWRF78+fQLf3b/iTm\n8fCl4YBc9tDggN9XNMes97Nh+tOy/3wSYhjpSKwKsRQX6wbIuuuChhwu1RwEiuT/\nIDRO91YeSgNBxn0enJACmmxaJ7Ocn7hGN8g4wqxXw/Qwd2aOXftm5KdoIDW/Kkze\n/LxmgahKcijzpD86N+t817Dteob0H/fqNyEKBJ+JVi29osr7Lg2I0OJTXlFtmCBk\nQKG3akudAgMBAAECggEAATPGEpYsXJcO5pmmyqJMnNVZA0eTmZdnXW1ZL3Q057EQ\nZ/zjc6uqAX19FD5UtRDfLJ/JqxjHiPIkX0/blGFNn28nxRvVLDIJRBAepJ3txLiR\nP3j4LYN3fn7V9VnOt9jVeThDz3eRsRkwYPNPZIhqHfJqPJ8+TkdPnx7vD2/gt90a\nwtlSLLmApcvJqcvTTgYTQ16VhQl3kDwV5xNQrG2QnOcjT30+XfsDZDaB46QN8Xty\nPnsNJkeCQTz3JZb5V9HixHYiTiDxse9qBb3rQGH2BQOQFpyJJSjhfsIv/q5Mal8C\nCL2a2fCeksOeHbU2kPQQj4VFd7f25CqqMmBrTNWjQQKBgQC9EadDVRvwuJNfTH+q\nokFxDrTx3V7Nkmk+eYH0YLcy4gQ6lvK6m4NeEp8CyEmx05VpW2xFfngZ14y5W8sW\nzf1Byb1twt7BWWom/IvvI1YpBxbI2EQ2LUB+mnw1DiLgcM8NKbFAtebNQL5lFrkI\nLXRIdkx9Zk+CzZhP2HCDOPzU3QKBgQC4mbPrvnlGR/5F+lej1KbnQ1exXt4s6YUS\nyzc4/myQcSIkFZiTfq9O2hAc6DwG7+LSEZvL93Y6BNMh7Rf7rav0VpR73S5WXaen\n3TmLT42CvoDMTJBQ8mBzk+hY00oF+MYpW/GpdEgehqv99acoNP2TM0wt2r3Xr0s3\njik5vCOFwQKBgFgPLNRTg5vum9U7EAstX0WFEAnGjS06EAKlHT3w/eKZGlcfjxYS\n8HCUQ7NMDebhISndBuSnLtD6b/S1KDYK4vYNPEkvBgkP2D0oSxSqZKrfPmF1OO/y\ny6Mr2MXtO5lFcWo0DPaSwli+2u7CUpPYd9x4HNAbItVNZK9ro5u6oyeRAoGAfOzP\nfMc/DRfldPfw3VcoyDKjos4fructfkV2DqTnVWyqfR78TTybaNJbuyRSkyM+LYlr\nFMJYCPWA6GGqLFEgoE8DVzucgygIMKqeqa9hhcxkH13lAFK2gSDkSVBbtOThPdYS\nGeoucDIVLN1UjPonbLl3YUS52r+vOF6FeaPfqkECgYBExR7mxBvDCLBKkyPOPvoL\nXqbcgRK5uA/jt4gm/XrKu4naahIGKZ3ai/f9wf7uQ8ejn0W/6leHoupkft+tRXx+\nMJyhl6hxtJnrXEKSgzIZvrZT08cKQW8c7W+ImqfEB408rX4PjWWmpYI2mCXfQ999\nHrUkhaIwWIbQnx3uzRAVsg==\n-----END PRIVATE KEY-----\n",
    "client_email": "firebase-adminsdk-fbsvc@smartgrid-70254.iam.gserviceaccount.com",
    "client_id": "109029954456226467075",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40smartgrid-70254.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

# Initialize Firebase with hardcoded credentials
cred = credentials.Certificate(firebase_credentials)

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
