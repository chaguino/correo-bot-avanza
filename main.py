import poplib
import ssl
from email.parser import BytesParser
from email.policy import default
from twilio.rest import Client
import hashlib
import os
import csv
from datetime import datetime
import time

# --- Configuración de correo (POP3) ---
EMAIL_USER = "santiagog@avanzaloop.com"
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")  # Se guarda en Render
POP_SERVER = "vmail.globalpc.net"
POP_PORT = 995

# --- Palabras clave y remitentes importantes ---
PALABRAS_CLAVE = ["Santiago", "Santi", "Guerrero", "Urgente", "Crítico"]
REMITENTES_IMPORTANTES = [
    "ricardoat@avanzaloop.com",
    "robertoat@avanzaloop.com",
    "gabrielv@avanzaloop.com"
]

# --- Configuración de Twilio WhatsApp ---
ACCOUNT_SID = os.environ.get("ACCOUNT_SID")
AUTH_TOKEN = os.environ.get("AUTH_TOKEN")
FROM_NUMBER = 'whatsapp:+14155238886'
TO_NUMBER = 'whatsapp:+19568981394'
client = Client(ACCOUNT_SID, AUTH_TOKEN)

# --- Archivos locales ---
ARCHIVO_CONTROL = "correos_ya_enviados.txt"
ARCHIVO_HISTORIAL = "historial_correos.csv"

# --- Funciones auxiliares ---
def cargar_ids_previos():
    if not os.path.exists(ARCHIVO_CONTROL):
        return set()
    with open(ARCHIVO_CONTROL, "r") as f:
        return set(line.strip() for line in f)

def guardar_id(id_unico):
    with open(ARCHIVO_CONTROL, "a") as f:
        f.write(id_unico + "\n")

def generar_id_mensaje(subject, from_, body):
    base = subject + from_ + body[:200]
    return hashlib.md5(base.encode()).hexdigest()

def limpiar_texto(texto):
    texto = texto.replace('\r', '').replace('\n\n', '\n').strip()
    lineas = texto.split('\n')
    bloqueos = ["disclaimer", "confidential", "no imprimir", "privileged", "legal", "correo electrónico"]
    filtradas = []
    for linea in lineas:
        if any(bloqueo in linea.lower() for bloqueo in bloqueos):
            break
        if linea.strip():
            filtradas.append(linea.strip())
    return '\n'.join(filtradas[:6])

def registrar_en_historial(fecha, remitente, asunto, fue_notificado):
    nueva_linea = [fecha, remitente, asunto, fue_notificado]
    archivo_existe = os.path.exists(ARCHIVO_HISTORIAL)
    with open(ARCHIVO_HISTORIAL, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        if not archivo_existe:
            writer.writerow(["Fecha", "De", "Asunto", "Notificado"])
        writer.writerow(nueva_linea)

def revisar_correos():
    print("📬 Revisión iniciada...")
    ids_previos = cargar_ids_previos()
    context = ssl.create_default_context()
    server = poplib.POP3_SSL(POP_SERVER, POP_PORT)
    server.user(EMAIL_USER)
    server.pass_(EMAIL_PASSWORD)

    num_messages = len(server.list()[1])
    for i in range(max(1, num_messages - 10), num_messages + 1):
        raw_email = b"\n".join(server.retr(i)[1])
        email_message = BytesParser(policy=default).parsebytes(raw_email)

        subject = email_message.get("subject", "")
        from_ = email_message.get("from", "")
        to_ = email_message.get("to", "")
        cc_ = email_message.get("cc", "")
        body = ""
        adjuntos = []

        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                filename = part.get_filename()
                if filename:
                    adjuntos.append(filename)
                elif content_type == "text/plain":
                    body += part.get_content()
        else:
            body = email_message.get_content()

        texto = f"{subject} {to_} {cc_} {body}"
        from_email_raw = email_message.get("from", "").lower()
        from_email_real = from_email_raw[from_email_raw.find("<")+1:from_email_raw.find(">")] if "<" in from_email_raw else from_email_raw
        id_unico = generar_id_mensaje(subject, from_email_real, body)

        if id_unico in ids_previos:
            continue

        if any(p.lower() in texto.lower() for p in PALABRAS_CLAVE) or from_email_real in REMITENTES_IMPORTANTES:
            print(f"✅ Correo relevante detectado de {from_email_real}")
            cuerpo_limpio = limpiar_texto(body)

            resumen = (
                f"📨 *Nuevo correo importante:*\n"
                f"🧑‍💼 *De:* {from_email_real}\n"
                f"📝 *Asunto:* {subject}\n"
                f"📄 *Contenido:* \n{cuerpo_limpio}"
            )

            if adjuntos:
                resumen += f"\n📎 *Adjuntos:* {', '.join(adjuntos)}"

            resumen += "\n\nEscribe *VER COMPLETO* si deseas el mensaje completo."

            message = client.messages.create(
                body=resumen,
                from_=FROM_NUMBER,
                to=TO_NUMBER
            )
            print(f"📲 WhatsApp enviado (SID: {message.sid})")
            guardar_id(id_unico)
            registrar_en_historial(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), from_email_real, subject, "Sí")
        else:
            registrar_en_historial(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), from_email_real, subject, "No")

    server.quit()

# --- Ciclo infinito para Render (3 minutos) ---
if __name__ == "__main__":
    while True:
        try:
            revisar_correos()
            time.sleep(180)  # Espera 3 minutos
        except Exception as error:
            print(f"💥 Error en ciclo: {error}")
            time.sleep(180)
