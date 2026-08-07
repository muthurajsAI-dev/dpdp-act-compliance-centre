from flask import Blueprint, render_template, session, redirect, url_for

assistant_bp = Blueprint('assistant', __name__)

@assistant_bp.route('/chat')
def chat_assistant():
    # If the user is logged in, show the chat interface
    if 'user_id' in session:
        return render_template('index.html')
    
    # If not logged in, gracefully load the home page (where login/signup is handled)
    return render_template('index.html')