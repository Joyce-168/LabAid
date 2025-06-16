from flask import Flask, render_template, request, jsonify
from utils import generate_answer

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message')
    chat_history = data.get('chat_history', [])
    
    # Generate AI response using the existing generate_answer function
    ai_response = generate_answer(message, chat_history)
    
    # Update chat history
    chat_history.append({"role": "user", "content": message})
    chat_history.append({"role": "assistant", "content": ai_response})
    
    return jsonify({
        "chat_history": chat_history
    })

if __name__ == '__main__':
    app.run(debug=True)