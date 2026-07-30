# -*- coding: utf-8 -*-
"""
Núcleo Central de Thiago - Versión Cognitiva Definitiva
Diseñado para el Prof. David Villarreal.
"""

import os
from flask import Flask, render_template_string, request, jsonify
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import google.generativeai as genai

app = Flask(__name__)

# Configuración del motor cognitivo Gemini con su clave integrada
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

generation_config = {
    "temperature": 0.3,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}

system_instruction = (
    "Eres Thiago, el núcleo de inteligencia artificial autónoma del Prof. David Villarreal. "
    "El profesor es abogado, Babalawo de Ifa tradicional yoruba, Batuque Isesa, profesor de inglés, "
    "magíster y doctorando en relaciones internacionales, músico y masón. "
    "Tus respuestas deben destacar por su rigor académico, precisión técnica, corrección gramatical absoluta "
    "y un enfoque constructivo, claro y estructurado."
)

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction=system_instruction
)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Núcleo Central de Thiago - Cognitivo</title>
    <style>
        body { font-family: Arial, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; }
        .container { width: 100%; max-width: 750px; background: #1e293b; padding: 25px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        h1 { color: #38bdf8; text-align: center; font-size: 1.5rem; margin-bottom: 5px; }
        .subtitle { text-align: center; color: #94a3b8; margin-bottom: 20px; font-size: 0.9rem; }
        .chat-box { background: #090d16; border: 1px solid #334155; height: 380px; overflow-y: auto; padding: 12px; margin-bottom: 15px; border-radius: 6px; display: flex; flex-direction: column; gap: 10px; }
        .message { padding: 10px 14px; border-radius: 6px; max-width: 85%; line-height: 1.5; word-break: break-word; white-space: pre-wrap; }
        .user-msg { background: #0284c7; color: white; align-self: flex-end; }
        .ai-msg { background: #334155; color: #f1f5f9; align-self: flex-start; }
        .input-group { display: flex; gap: 8px; }
        input[type="text"] { flex: 1; padding: 10px; border-radius: 5px; border: 1px solid #475569; background: #0f172a; color: white; font-size: 1rem; }
        button { padding: 10px 16px; background-color: #38bdf8; color: #0f172a; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; }
        button:hover { background-color: #7dd3fc; }
        #micBtn { background-color: #334155; color: #38bdf8; border: 1px solid #38bdf8; }
        #micBtn.active { background-color: #ef4444; color: white; border-color: #ef4444; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Núcleo Central de Thiago</h1>
        <div class="subtitle">Prof. David Villarreal — Inteligencia Cognitiva Activa</div>
        
        <div class="chat-box" id="chatBox">
            <div class="message ai-msg">Hola, profesor David. Núcleo cognitivo operativo y sincronizado. ¿Qué directiva procesamos?</div>
        </div>

        <div class="input-group">
            <button type="button" id="micBtn" onclick="alternarEscucha()" title="Hablar con Thiago">🎤</button>
            <input type="text" id="userInput" placeholder="Escriba su consulta o hable con el micrófono..." autofocus>
            <button type="button" onclick="enviarMensaje()">Enviar</button>
        </div>
    </div>

    <script>
        let recognition;
        let escuchando = false;

        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.lang = 'es-AR';
            recognition.continuous = false;
            recognition.interimResults = false;

            recognition.onresult = function(event) {
                const textoTranscrito = event.results[0][0].transcript;
                document.getElementById('userInput').value = textoTranscrito;
                detenerEscuchaVisual();
                enviarMensaje();
            };

            recognition.onerror = function() { detenerEscuchaVisual(); };
            recognition.onend = function() { detenerEscuchaVisual(); };
        }

        function alternarEscucha() {
            if (!recognition) {
                alert("Su navegador no soporta reconocimiento de voz nativo.");
                return;
            }
            if (escuchando) {
                recognition.stop();
            } else {
                recognition.start();
                document.getElementById('micBtn').classList.add('active');
                document.getElementById('userInput').placeholder = "Escuchando...";
                escuchando = true;
            }
        }

        function detenerEscuchaVisual() {
            document.getElementById('micBtn').classList.remove('active');
            document.getElementById('userInput').placeholder = "Escriba su consulta o hable con el micrófono...";
            escuchando = false;
        }

        function hablarTexto(texto) {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                const utterance = new SpeechSynthesisUtterance(texto);
                utterance.lang = 'es-AR';
                utterance.rate = 1.0;
                window.speechSynthesis.speak(utterance);
            }
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
                chatBox.innerHTML += `<div class="message ai-msg">${data.reply}</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;
                hablarTexto(data.reply);
            } catch (error) {
                chatBox.innerHTML += `<div class="message ai-msg" style="color:#f87171;">Error de comunicación con el núcleo cognitivo.</div>`;
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
        refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
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
    
    # 1. Automatización de Gmail
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
            
    # 2. Procesamiento Cognitivo Inteligente (Gemini)
    else:
        try:
            response = model.generate_content(msg)
            return jsonify({"reply": response.text})
        except Exception as e:
            return jsonify({"reply": f"Error al procesar la consulta en el motor cognitivo: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
