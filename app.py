# -*- coding: utf-8 -*-
"""
Núcleo Central de Thiago - Versión Operativa Definitiva con OAuth Corregido.
Diseñado para el Prof. David Villarreal.
"""

from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import os
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "clave-segura-thiago")

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

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
        .mic-btn { background-color: #ef4444; color: white; }
        .mic-btn.listening { background-color: #22c55e; animation: pulse 1.5s infinite; }
        .auth-link { color: #38bdf8; text-decoration: underline; font-weight: bold; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    </style>
</head>
<body>
    <div class="container">
        <h1>Núcleo Central de Thiago</h1>
        <div class="subtitle">Prof. David Villarreal — Inteligencia Autónoma Activa</div>
        
        <div class="chat-box" id="chatBox">
            <div class="message ai-msg">Hola, profesor David. Núcleo operativo y enlazado. ¿Qué directiva procesamos?</div>
        </div>

        <div class="input-group">
            <input type="text" id="userInput" placeholder="Escriba su consulta o instrucción..." autofocus>
            <button type="button" id="micBtn" class="mic-btn" onclick="alternarEscucha()" title="Hablar con Thiago">🎤 Hablar</button>
            <button type="button" onclick="enviarMensaje()">Enviar</button>
        </div>
    </div>

    <script>
        let vocesDisponibles = [];
        window.speechSynthesis.onvoiceschanged = () => {
            vocesDisponibles = window.speechSynthesis.getVoices();
        };

        function hablar(texto) {
            if (!('speechSynthesis' in window)) return;
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(texto);
            utterance.lang = 'es-ES';
            utterance.rate = 1.0;
            const vozEspanol = vocesDisponibles.find(v => v.lang.startsWith('es'));
            if (vozEspanol) utterance.voice = vozEspanol;
            window.speechSynthesis.speak(utterance);
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        let recognition = null;
        let escuchando = false;

        if (SpeechRecognition) {
            recognition = new SpeechRecognition();
            recognition.lang = 'es-ES';
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.onstart = () => {
                escuchando = true;
                const btn = document.getElementById('micBtn');
                btn.classList.add('listening');
                btn.textContent = '🔴 Escuchando...';
            };
            recognition.onresult = (event) => {
                const textoTranscrito = event.results[0][0].transcript;
                document.getElementById('userInput').value = textoTranscrito;
                enviarMensaje();
            };
            recognition.onerror = () => { detenerEscucha(); };
            recognition.onend = () => { detenerEscucha(); };
        } else {
            document.getElementById('micBtn').style.display = 'none';
        }

        function alternarEscucha() {
            if (!recognition) {
                alert("Su navegador no soporta reconocimiento de voz nativo. Utilice Google Chrome.");
                return;
            }
            if (escuchando) { recognition.stop(); } else { recognition.start(); }
        }

        function detenerEscucha() {
            escuchando = false;
            const btn = document.getElementById('micBtn');
            btn.classList.remove('listening');
            btn.textContent = '🎤 Hablar';
        }

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
                
                if (data.auth_url) {
                    chatBox.innerHTML += `<div class="message ai-msg">Para acceder a sus correos, haga clic en el siguiente enlace de autorización segura: <br><br><a href="${data.auth_url}" target="_blank" class="auth-link">🔗 Autorizar Acceso a Gmail</a></div>`;
                    hablar("Necesito autorización para acceder a sus correos.");
                } else {
                    chatBox.innerHTML += `<div class="message ai-msg">${data.reply}</div>`;
                    hablar(data.reply);
                }
                chatBox.scrollTop = chatBox.scrollHeight;
            } catch (error) {
                chatBox.innerHTML += `<div class="message ai-msg" style="color:#f87171;">Error de comunicación con el núcleo.</div>`;
            }
        }

        document.getElementById('userInput').addEventListener('keypress', function (e) {
            if (e.key === 'Enter') enviarMensaje();
        });
    </script>
</body>
</html>
"""

def obtener_cliente_oauth():
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    
    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=['https://www.googleapis.com/auth/gmail.readonly'],
        redirect_uri="https://thiago-core.onrender.com/oauth2callback"
    )
    # Deshabilitar PKCE para evitar el error de code verifier en servidores web tradicionales
    flow.code_verifier = None
    return flow

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/oauth2callback")
def oauth2callback():
    code = request.args.get("code")
    if not code:
        return "Error: No se recibió código de autorización.", 400
    try:
        flow = obtener_cliente_oauth()
        flow.fetch_token(code=code)
        session['credentials'] = {
            'token': flow.credentials.token,
            'refresh_token': flow.credentials.refresh_token,
            'token_uri': flow.credentials.token_uri,
            'client_id': flow.credentials.client_id,
            'client_secret': flow.credentials.client_secret,
            'scopes': flow.credentials.scopes
        }
        return redirect(url_for('index'))
    except Exception as e:
        return f"Error al procesar el token: {str(e)}", 500

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    msg = data.get("message", "").strip()
    if not msg:
        return jsonify({"reply": "Indique una directiva válida."})
    
    if any(k in msg.lower() for k in ["correo", "mail", "bandeja", "llegó", "mensajes", "mails"]):
        creds_data = session.get('credentials')
        if not creds_data:
            try:
                flow = obtener_cliente_oauth()
                auth_url, _ = flow.authorization_url(
                    access_type='offline',
                    include_granted_scopes='true',
                    prompt='consent'
                )
                return jsonify({"auth_url": auth_url})
            except Exception as e:
                return jsonify({"reply": f"Error generando enlace: {str(e)}"})
        
        try:
            from google.oauth2.credentials import Credentials
            creds = Credentials(**creds_data)
            service = build('gmail', 'v1', credentials=creds)
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
            return jsonify({"reply": "Últimos correos detectados:\n\n" + "\n\n".join(lista_mails)})
        except Exception as e:
            session.pop('credentials', None)
            flow = obtener_cliente_oauth()
            auth_url, _ = flow.authorization_url(access_type='offline', include_granted_scopes='true', prompt='consent')
            return jsonify({"auth_url": auth_url})
            
    elif any(k in msg.lower() for k in ["hola", "thiago", "saludos"]):
        return jsonify({"reply": "Hola, profesor David. A su entera disposición."})
    else:
        return jsonify({"reply": f"Instrucción procesada: {msg}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
