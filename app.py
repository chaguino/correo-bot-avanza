from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os

# Obtener credenciales desde variables de entorno
ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER")

# Inicializar Twilio Client
client = Client(ACCOUNT_SID, AUTH_TOKEN)

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "WhatsApp Flask Bot is Running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.form  # Twilio envía los datos en formato 'form'
    
    # Extraer el mensaje recibido y el número del usuario
    sender_number = data.get("From")
    message_body = data.get("Body").strip().lower()

    # Responder al mensaje recibido
    response = MessagingResponse()
    response.message(f"Hola, recibimos tu mensaje: {message_body}")

    return str(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
