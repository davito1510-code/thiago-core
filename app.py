# -*- coding: utf-8 -*-
"""
Núcleo Central de Thiago - Versión Profesional Exclusiva (Gemini 1.5 Pro)
"""

import os
import datetime
import requests
from flask import Flask, render_template_string, request, jsonify
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

app = Flask(__name__)

GEMINI_KEY = os.getenv("GEMINI_API_KEY")

SYSTEM_INSTRUCTION = (
    "Eres Thiago, el núcleo de inteligencia artificial autónoma del Prof. David Villarreal. "
    "El profesor es abogado en la CABA, Babalawo de Ifa tradicional yoruba, "
    "Batuque Isesa, profesor de inglés, magíster en relaciones internacionales y masón. "
    "Tus respuestas deben destacar por su rigor académico, precisión técnica y corrección gramatical absoluta. "
    "Si el sistema te provee información de correos o calendario, utilízala obligatoriamente para "
    "responder con naturalidad a la petición del usuario. No utilices rodeos."
)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Núcleo Central de Thiago - IA Activa</title>
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
        <div class="subtitle">Prof. David Villarreal — Inteligencia y Automatización Integrada</div>
        
        <div class="chat-box" id="chatBox">
            <div class="message ai-msg">Núcleo cognitivo profesional en línea (Modelo: Gemini 1.5 Pro). ¿Qué directiva procesamos?</div>
        </div>

        <div class="input-group">
            <button type="button" id="micBtn" onclick="alternarEscucha()" title="Hablar con Thiago">🎤</button>
            <input type="text" id="userInput" placeholder="Escriba su consulta o hable..." autofocus>
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
            document.getElementById('userInput').placeholder = "Escriba su consulta o hable...";
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

def obtener_credenciales():
    creds = Credentials(
        token=None,
        refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        scopes=[
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/calendar.readonly'
        ]
    )
    if not creds.valid:
        creds.refresh(Request())
    return creds

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    msg = data.get("message", "").strip()
    if not msg:
        return jsonify({"reply": "Indique una directiva válida."})
    
    msg_lower = msg.lower()
    contexto_adicional = ""

    try:
        if any(k in msg_lower for k in ["correo", "mail", "bandeja", "mensajes", "mails"]):
            creds = obtener_credenciales()
            service = build('gmail', 'v1', credentials=creds)
            results = service.users().messages().list(userId='me', maxResults=5).execute()
            messages = results.get('messages', [])
            
            if messages:
                lista_mails = []
                for m in messages:
                    msg_data = service.users().messages().get(userId='me', id=m['id']).execute()
                    headers = msg_data.get('payload', {}).get('headers', [])
                    asunto = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Sin Asunto')
                    remitente = next((h['value'] for h in headers if h['name'] == 'From'), 'Desconocido')
                    fragmento = msg_data.get('snippet', 'Sin contenido legible.')
                    lista_mails.append(f"De: {remitente} | Asunto: {asunto} | Contenido: {fragmento}")
                
                contexto_adicional += "INFORMACIÓN DE GMAIL OBTENIDA:\n" + "\n".join(lista_mails) + "\n\n"
            else:
                contexto_adicional += "INFORMACIÓN DE GMAIL: No hay correos en la bandeja.\n\n"

        if any(k in msg_lower for k in ["calendario", "agenda", "compromisos", "evento", "reunión"]):
            creds = obtener_credenciales()
            service = build('calendar', 'v3', credentials=creds)
            now = datetime.datetime.utcnow().isoformat() + 'Z'
            events_result = service.events().list(
                calendarId='primary', timeMin=now,
                maxResults=5, singleEvents=True,
                orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            
            if events:
                lista_eventos = []
                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    summary = event.get('summary', 'Sin título')
                    lista_eventos.append(f"Evento: {summary} | Fecha y Hora: {start}")
                contexto_adicional += "INFORMACIÓN DE CALENDARIO OBTENIDA:\n" + "\n".join(lista_eventos) + "\n\n"
            else:
                contexto_adicional += "INFORMACIÓN DE CALENDARIO: No hay compromisos próximos.\n\n"

    except Exception as e:
        contexto_adicional += f"[Advertencia de Sistema: Error al sincronizar APIs: {str(e)}]\n\n"

    if GEMINI_KEY:
        try:
            if contexto_adicional:
                prompt_final = (
                    f"Directiva del usuario: '{msg}'.\n"
                    f"Utiliza estrictamente la siguiente información extraída en tiempo real:\n\n"
                    f"{contexto_adicional}\n"
                    f"Responde con naturalidad analizando o leyendo los datos."
                )
            else:
                prompt_final = msg

            # Conexión directa y forzada al modelo Premium estable
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={GEMINI_KEY}"
            payload = {
                "contents": [{"parts": [{"text": prompt_final}]}],
                "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
                "generationConfig": {"temperature": 0.3}
            }
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(url, json=payload, headers=headers)
            res_json = response.json()
            
            if "candidates" in res_json:
                texto_respuesta = res_json["candidates"][0]["content"]["parts"][0]["text"]
                return jsonify({"reply": texto_respuesta})
            else:
                return jsonify({"reply": f"Error en respuesta de API: {str(res_json)}"})
                
        except Exception as e:
            return jsonify({"reply": f"Error crítico en el motor cognitivo: {str(e)}"})
    else:
        return jsonify({"reply": "Error: GEMINI_API_KEY no detectada en las variables de entorno."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
