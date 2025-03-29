import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# Initialize Firebase
cred = credentials.Certificate("smartgrid-70254-firebase-adminsdk-fbsvc-16987a2fa8.json")
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
    
    # Find which component is mentioned
    found_section = None
    found_component = None
    
    for section, items in components.items():
        for keyword, component_name in items.items():
            if keyword.lower() in message:
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

# Example usage
def handle_user_message(user_message):
    result = process_message(user_message)
    print(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

gunicorn_app = app
# Test the function
if __name__ == "__main__":
    while True:
        user_input = input("Enter your command (or 'quit' to exit): ")
        if user_input.lower() == 'quit':
            break
        handle_user_message(user_input)
