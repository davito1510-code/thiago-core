# -*- coding: utf-8 -*-
from flask import Flask, render_template_string, request, jsonify
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Núcleo Central de Thiago</title>
    <style>
        body { font-family: Arial, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; }
        .container { width: 100%; max-width: 750px; background: #1e293b; padding: 25px; border-radius: 10px; }
        h1 { color: #38bdf8; text-align: center; }
        .chat-box { background: #090d16; border: 1px solid #334155; height: 340px; overflow-y: auto; padding: 12px; margin-bottom: 15px; border-radius: 6px; display: flex; flex-direction: column; gap: 8px; }
        .message { padding: 9px 13px; border-radius: 6px; max-width: 85%; word-break: break-word; }
        .user-msg { background: #0284c7; color: white; align-self: flex-end; }
        .ai-msg { background: #334155; color: #f1f5f9; align-self: flex-start; }
        .input-group { display: flex; gap: 8px; }
        input[type="text"] { flex: 1; padding: 10px; border-radius: 5px; background: #0f172a; color: white; border: 1px solid #475569; }
        button { padding: 10px 16px; background-color: #38bdf8; color: #0f172a; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Núcleo Central de Thiago</h1>
        <div class="chat-box" id="chatBox">
            <div class="message ai-msg">Hola, profesor David. Núcleo autónomo operativo. ¿Qué directiva procesamos?</div>
        </div>
        <div class="input-group">
            <input type="text" id="userInput" placeholder="Escriba su consulta..." autofocus>
            <button type="button" onclick="enviarMensaje()">Enviar</button>
        </div>
    </div>
    <script>
        async function enviarMensaje() {
            const input = document.getElementById('userInput');
            const chatBox = document.getElementById('chatBox');
            const texto = input.value.trim();
            if (!texto) return;
            chatBox.innerHTML += `<div class="message user-msg">${texto}</div>`;
            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: texto })
                });
                const data = await response.json();
                chatBox.innerHTML += `<div class="message ai-msg">${data.reply}</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;
            } catch (error) {
                chatBox.innerHTML += `<div class="message ai-msg" style="color:#f87171;">Error de comunicación.</div>`;
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
    creds = Credentials(
        token=None,
        refresh_token="1//0hNRrDJiz-K6NCgYIARAAGBESNWf-L9Ir5kRTiruuhVrzJvkKRwj9dQrGhMkNGQndoySA_agJpz6qipyBkEkiZl4DbwS9_pMazU",
        token_uri="https://oauth2.googleapis.com/token",
        client_id="377709097034-hj0bnbv02onkarp3vpq1vlidalfjfb5r.apps.googleusercontent.com",
        client_secret="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",
        scopes=['https://www.googleapis.com/auth/gmail.readonly']
    )
    if not creds.valid:
        creds.refresh(Request())
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
    
    if any(k in msg.lower() for k in ["correo", "mail", "bandeja", "llegó", "mensajes", "mails", "ingresas", "traer", "leer"]):
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
                lista_mails.append(f"De: {remitente}. Asunto: {asunto}")
            
            return jsonify({"reply": "Últimos correos detectados:\n\n" + "\n".join(lista_mails)})
        except Exception as e:
            return jsonify({"reply": f"Error de autorización en la cuenta de Google: {str(e)}"})
            
    elif any(k in msg.lower() for k in ["hola", "thiago", "saludos"]):
        return jsonify({"reply": "Hola, profesor David. Núcleo en línea, escuchando y preparado."})
    else:
        return jsonify({"reply": f"Instrucción procesada correctamente: {msg}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
