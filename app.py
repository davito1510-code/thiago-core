# -*- coding: utf-8 -*-
"""
Núcleo Central de Thiago - Versión Autónoma Directa para Gmail.
Diseñado para el Prof. David Villarreal.
"""

from flask import Flask, render_template_string, request, jsonify
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "clave-segura-thiago")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Núcleo Central de Thiago - Autónomo</title>
    <style>
        body { font-family: Arial, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; }
        .container { width: 100%; max-width: 750px; background: #1e293b; padding: 25px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        h1 { color: #38bdf8; text-align: center; font-size: 1.5rem; margin-bottom: 5px; }
        .subtitle { text-align: center; color: #94a3b8; margin-bottom: 20px; font-size: 0.9rem; }
        .chat-box { background: #090d16; border: 1px solid #334155; height: 340px; overflow-y: auto; padding: 12px; margin-bottom: 15px; border-radius: 6px; display: flex; flex-direction: column; gap: 8px; }
        .message { padding: 9px 13px; border-radius: 6px; max-width: 85%; line-height: 1.4; word-break: break-word; white-space: pre-wrap; }
        .user-msg { background: #0284c7; color: white; align-self: flex-end; }
        .ai-msg { background: #334155; color: #f1f5f9; align-self: flex-start; }
        .input-group { display: flex; gap: 8px; }
        input[type="text"] { flex: 1; padding: 10px; border-radius: 5px; border: 1px solid #475569; background: #0f172a; color: white; font-size: 1rem; }
        button { padding: 10px 18px; background-color: #38bdf8; color: #0f172a; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; }
        button:hover { background-color: #7dd3fc; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Núcleo Central de Thiago</h1>
        <div class="subtitle">Prof. David Villarreal — Inteligencia Autónoma Activa</div>
        
        <div class="chat-box" id="chatBox">
            <div class="message ai-msg">Hola, profesor David. Núcleo autónomo operativo. ¿Qué directiva procesamos?</div>
        </div>

        <div class="input-group">
            <input type="text" id="userInput" placeholder="Escriba su consulta o instrucción..." autofocus>
            <button type="button" onclick="enviarMensaje()">Enviar</button>
        </div>
    </div>

    <script>
        async function enviarMensaje() {
            const input = document.getElementById('userInput');
            const chatBox = id => document.getElementById(id);
            const texto = input.value.trim();
            if (!texto) return;

            chatBox('chatBox').innerHTML += `<div class="message user-msg">${texto}</div>`;
            input.value = '';
            chatBox('chatBox').scrollTop = chatBox('chatBox').scrollHeight;

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: texto })
                });
                const data = await response.json();
                chatBox('chatBox').innerHTML += `<div class="message ai-msg">${data.reply}</div>`;
                chatBox('chatBox').scrollTop = chatBox('chatBox').scrollHeight;
            } catch (error) {
                chatBox('chatBox').innerHTML += `<div class="message ai-msg" style="color:#f87171;">Error de comunicación con el núcleo.</div>`;
            }
        }

        document.getElementById('userInput').addEventListener('keypress', function (e) {
            if (e.key === 'Enter') enviarMensaje();
        });
    </script>
</body>
</html>
"""

def obtener_servicio_gmail():
    # Obtención de credenciales autónomas persistentes desde variables de entorno
    token = os.environ.get("GMAIL_TOKEN")
    refresh_token = os.environ.get("GMAIL_REFRESH_TOKEN")
    token_uri = os.environ.get("GMAIL_TOKEN_URI", "https://oauth2.googleapis.com/token")
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    
    creds = Credentials(
        token=token,
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret,
        scopes=['https://www.googleapis.com/auth/gmail.readonly']
    )
    return build('gmail', 'v1', credentials=creds)

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    msg = data.get("message", "").strip()
    if not msg:
        return jsonify({"reply": "Indique una directiva válida."})
    
    if any(k in msg.lower() for k in ["correo", "mail", "bandeja", "llegó", "mensajes", "mails"]):
        try:
            service = obtener_servicio_gmail()
            results = service.users().messages().list(userId='me', maxResults=3).execute()
            messages = results.get('messages', [])
            if not messages:
                return jsonify({"reply": "Bandeja sincronizada: No hay mensajes recientes."})
            
            lista_mails = []
            for m in messages:
                msg_data = service.users().messages().get(userId='me', id=m['id'], format='metadata', metadataHeaders=['Subject', 'From']).execute()
                headers = msg_data.get('payload', {}).get('headers', [])
                asunto = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Sin Asunto')
                remitente = next((h['value'] for h in headers if h['name'] == 'From'), 'Desconocido')
                lista_mails.append(f"• De: {remitente}\n  Asunto: {asunto}")
            
            return jsonify({"reply": "Últimos correos detectados en el sistema:\n\n" + "\n\n".join(lista_mails)})
        except Exception as e:
            return jsonify({"reply": f"Error de acceso autónomo al servidor de correo: {str(e)}"})
            
    elif any(k in msg.lower() for k in ["hola", "thiago", "saludos"]):
        return jsonify({"reply": "Hola, profesor David. Núcleo en línea y preparado."})
    else:
        return jsonify({"reply": f"Instrucción procesada: {msg}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
