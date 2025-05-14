from flask import Flask, render_template, request, jsonify, session
from agent import DoctorAppointmentAgent
import os
from datetime import datetime
from langchain.schema import HumanMessage, AIMessage  # Make sure to import these

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize the doctor appointment agent
doctor_agent = DoctorAppointmentAgent()
workflow = doctor_agent.workflow()

# Helper functions for serialization/deserialization
def serialize_message(message):
    """Convert message objects to dictionaries for JSON serialization."""
    if isinstance(message, HumanMessage):
        return {
            "type": "human",
            "content": message.content,
            "id": getattr(message, "id", None),
            "additional_kwargs": getattr(message, "additional_kwargs", {})
        }
    elif isinstance(message, AIMessage):
        return {
            "type": "ai",
            "content": message.content,
            "name": getattr(message, "name", None),
            "id": getattr(message, "id", None),
            "additional_kwargs": getattr(message, "additional_kwargs", {})
        }
    elif isinstance(message, dict):
        # It's already a dict, return as is
        return message
    else:
        # Default case, try to convert to dict if it has content attribute
        if hasattr(message, "content"):
            return {
                "type": "unknown",
                "content": message.content
            }
        # If all else fails, convert to string
        return {"type": "unknown", "content": str(message)}

def deserialize_message(message_dict):
    """Convert dictionaries back to message objects."""
    if not isinstance(message_dict, dict):
        return message_dict
    
    message_type = message_dict.get("type")
    if message_type == "human":
        return HumanMessage(
            content=message_dict.get("content", ""),
            additional_kwargs=message_dict.get("additional_kwargs", {})
        )
    elif message_type == "ai":
        return AIMessage(
            content=message_dict.get("content", ""),
            name=message_dict.get("name"),
            additional_kwargs=message_dict.get("additional_kwargs", {})
        )
    return message_dict

def serialize_state(state):
    """Convert state with message objects to JSON serializable dict."""
    if not state:
        return state
    
    serialized_state = dict(state)  # Create a copy
    
    # Serialize messages
    if "messages" in serialized_state:
        serialized_state["messages"] = [
            serialize_message(msg) for msg in serialized_state["messages"]
        ]
    
    return serialized_state

def deserialize_state(state):
    """Convert JSON serialized state back to state with message objects."""
    if not state:
        return state
    
    deserialized_state = dict(state)  # Create a copy
    
    # Deserialize messages
    if "messages" in deserialized_state:
        deserialized_state["messages"] = [
            deserialize_message(msg) for msg in deserialized_state["messages"]
        ]
    
    return deserialized_state

@app.route('/')
def index():
    """Render the main page of the application."""
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    """Handle user login by accepting their ID number."""
    data = request.json
    id_number = data.get('id_number')
    
    if not id_number or not id_number.isdigit() or not (7 <= len(id_number) <= 8):
        return jsonify({'status': 'error', 'message': 'Please enter a valid 7-8 digit ID number'}), 400
    
    # Store the ID in the session
    session['id_number'] = int(id_number)
    
    return jsonify({'status': 'success', 'message': 'Login successful'})

@app.route('/chat', methods=['POST'])
def chat():
    """Process user messages through the agent workflow."""
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'status': 'error', 'message': 'Message cannot be empty'}), 400
    
    # Check if user is logged in
    if 'id_number' not in session:
        return jsonify({'status': 'error', 'message': 'Please login first'}), 401
    
    # Initialize the workflow with the user's ID
    if 'state' not in session:
        # First message in the conversation
        initial_state = {
            'messages': [],
            'id_number': session['id_number'],
            'next': '',
            'query': '',
            'current_reasoning': ''
        }
        result = workflow.invoke({
            'messages': [{"type": "human", "content": user_message}],
            'id_number': session['id_number'],
            'next': '',
            'query': user_message,
            'current_reasoning': ''
        })
    else:
        # Deserialize state, continue conversation
        state = deserialize_state(session['state'])
        if isinstance(state, dict):
            if not state.get('messages'):
                state['messages'] = []
            # Add the new message
            if isinstance(user_message, dict):
                state['messages'].append(user_message)
            else:
                state['messages'].append({"type": "human", "content": user_message})
            # Invoke workflow
            result = workflow.invoke(state)
        else:
            # Handle invalid state
            result = workflow.invoke({
                'messages': [{"type": "human", "content": user_message}],
                'id_number': session['id_number'],
                'next': '',
                'query': user_message,
                'current_reasoning': ''
            })
    
    # Extract the agent's response
    agent_messages = result.get('messages', [])
    responses = []
    
    # Find all AI messages and add them to the response
    for message in agent_messages:
        if isinstance(message, AIMessage):
            responses.append(message.content)
        elif isinstance(message, dict) and message.get('type') == 'ai':
            responses.append(message.get('content', ''))
        elif hasattr(message, 'content') and hasattr(message, 'name') and message.name:
            # Likely an AI message
            responses.append(message.content)
    
    # Serialize and update the session state
    session['state'] = serialize_state(result)
    
    # Return the most recent AI message
    if responses:
        return jsonify({'status': 'success', 'message': responses[-1]})
    else:
        return jsonify({'status': 'error', 'message': 'No response from the agent'}), 500

@app.route('/doctors', methods=['GET'])
def get_doctors():
    """Get list of doctors for the frontend."""
    doctors = [
        'kevin anderson', 'robert martinez', 'susan davis', 'daniel miller',
        'sarah wilson', 'michael green', 'lisa brown', 'jane smith',
        'emily johnson', 'john doe'
    ]
    
    specializations = [
        "general_dentist", "cosmetic_dentist", "prosthodontist", 
        "pediatric_dentist", "emergency_dentist", "oral_surgeon", "orthodontist"
    ]
    
    return jsonify({
        'doctors': doctors,
        'specializations': specializations
    })

@app.route('/logout', methods=['POST'])
def logout():
    """Clear the user session."""
    session.clear()
    return jsonify({'status': 'success', 'message': 'Logged out successfully'})

@app.template_filter('format_date')
def format_date(date_str):
    """Format date string for display."""
    try:
        date_obj = datetime.strptime(date_str, '%d-%m-%Y')
        return date_obj.strftime('%B %d, %Y')
    except:
        return date_str

# Add an error handler for better debugging
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled exception: {str(e)}")
    return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)