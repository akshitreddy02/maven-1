# app.py
from flask import Flask, render_template, request, jsonify, session
import json
from datetime import datetime
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for session management

# Store notes and active users
NOTES_FILE = 'notes.json'
active_users = {}

#func to remove users if they are not using the site anymore
def cleanup_inactive_users():
    current_time = time.time()
    # Remove users inactive for more than 30 seconds
    inactive = [uid for uid, data in active_users.items() 
               if current_time - data['last_active'] > 30]
    for uid in inactive:
        del active_users[uid]

def load_notes():
    try:
        with open(NOTES_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_notes(notes):
    with open(NOTES_FILE, 'w') as f:
        json.dump(notes, f)

@app.route('/')
def home():
    if 'user_id' not in session:
        session['user_id'] = f'user_{len(active_users) + 1}'
    
    user_id = session['user_id']
    ip_address = request.remote_addr
    active_users[user_id] = {
        'ip': ip_address,
        'last_active': time.time()
    }
    return render_template('index.html', user_id=user_id)

@app.route('/api/notes', methods=['GET'])
def get_notes():
    if 'user_id' in session:
        active_users[session['user_id']]['last_active'] = time.time()
    cleanup_inactive_users()
    notes = load_notes()
    return jsonify(notes)

@app.route('/api/notes', methods=['POST'])
def add_note():
    if 'user_id' not in session:
        return jsonify({'error': 'No session'}), 401
    
    active_users[session['user_id']]['last_active'] = time.time()
    data = request.get_json()
    content = data.get('content')
    if content:
        notes = load_notes()
        note = {
            'id': len(notes) + 1,
            'content': content,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': session['user_id'],
            'ip': request.remote_addr
        }
        notes.append(note)
        save_notes(notes)
        return jsonify(note), 201
    return jsonify({'error': 'Content is required'}), 400

@app.route('/api/active-users', methods=['GET'])
def get_active_users():
    cleanup_inactive_users()
    return jsonify(list(active_users.items()))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

# templates/index.html
