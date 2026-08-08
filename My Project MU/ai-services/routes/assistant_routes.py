from flask import Blueprint, render_template

assistant_bp = Blueprint('assistant', __name__)

@assistant_bp.route('/chat')
def chat_assistant():
    # Render the profile/chat interface directly; 
    # frontend JavaScript handles token verification and fetching
    return render_template('profile.html')