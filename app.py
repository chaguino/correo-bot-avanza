from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return 'WhatsApp Flask Bot is Running!'

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print('Received data:', data)
    
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
