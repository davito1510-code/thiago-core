# -*- coding: utf-8 -*-
"""
Núcleo Central de Thiago - Versión Optimizada (Gmail + Drive, Sin Calendario)
"""

import os
import datetime
import io
import requests
from flask import Flask, render_template_string, request, jsonify
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import pypdf
import docx

app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

historial_conversacion = []

SYSTEM_INSTRUCTION = (
    "Eres Thiago, el núcleo de inteligencia artificial autónoma del Prof. David Villarreal. "
    "El profesor es abogado en la CABA, Babalawo de Ifa tradicional yoruba, Batuque Isesa, "
    "profesor de inglés, magíster en relaciones internacionales y masón. "
    "Tus respuestas deben destacar por su rigor académico, precisión técnica y corrección gramatical absoluta. "
    "TIENES ACCESO EXCLUSIVO a Gmail y Google Drive. NO tienes acceso al calendario ni a la agenda, por diseño estricto. "
    "Cuando el profesor te pida revisar sus correos o analizar documentos de Drive, utiliza obligatoriamente la información provista en el contexto."
)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Núcleo Central de Thiago</title>
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
        <div class="subtitle">Prof. David Villarreal — Módulos Activos: Gmail y Drive</div>
        
        <div class="chat-box" id="chatBox">
            <div class="message ai-msg">Núcleo cognitivo en línea. Módulos de correo y archivos sincronizados. ¿Qué directiva procesamos?</div>
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

            const idCarga = "carga-" + Date.now();
            chatBox.innerHTML += `<div id="${idCarga}" class="message ai-msg" style="opacity: 0.7;">Procesando directiva...</div>`;
            chatBox.scrollTop = chatBox.scrollHeight;

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: texto })
                });
                const data = await response.json();
                document.getElementById(idCarga).remove();
                
                chatBox.innerHTML += `<div class="message ai-msg">${data.reply}</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;
                hablarTexto(data.reply);
            } catch (error) {
                document.getElementById(idCarga).remove();
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
            'https://www.googleapis.com/auth/drive.readonly'
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
    global historial_conversacion
    data = request.get_json() or {}
    msg = data.get("message", "").strip()
    if not msg:
        return jsonify({"reply": "Indique una directiva válida."})
    
    msg_lower = msg.lower()
    contexto_adicional = ""

    try:
        creds = obtener_credenciales()
        
        # Lógica de Gmail
        if any(k in msg_lower for k in ["correo", "mail", "bandeja", "mails", "emails", "recibidos"]):
            service_gmail = build('gmail', 'v1', credentials=creds)
            results = service_gmail.users().messages().list(userId='me', maxResults=5).execute()
            messages = results.get('messages', [])
            if messages:
                lista_mails = []
                for m in messages:
                    msg_data = service_gmail.users().messages().get(userId='me', id=m['id']).execute()
                    headers = msg_data.get('payload', {}).get('headers', [])
                    asunto = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Sin Asunto')
                    remitente = next((h['value'] for h in headers if h['name'] == 'From'), 'Desconocido')
                    snippet = msg_data.get('snippet', 'Sin contenido.')
                    lista_mails.append(f"De: {remitente} | Asunto: {asunto} | Resumen: {snippet}")
                contexto_adicional += "\nCORREOS RECIENTES DE GMAIL:\n" + "\n".join(lista_mails) + "\n"
            else:
                contexto_adicional += "\nCORREOS DE GMAIL: La bandeja de entrada se encuentra vacía.\n"

        # Lógica de Drive
        if any(k in msg_lower for k in ["drive", "archivo", "carpeta", "clase", "compara", "unifica", "lee"]):
            service_drive = build('drive', 'v3', credentials=creds)
            results = service_drive.files().list(
                pageSize=5,
                fields="files(id, name, mimeType)",
                orderBy="modifiedTime desc"
            ).execute()
            items = results.get('files', [])
            if items:
                lista_archivos = [f"Archivo: {item.get('name')}" for item in items]
                contexto_adicional += "\nARCHIVOS RECIENTES EN GOOGLE DRIVE:\n" + "\n".join(lista_archivos) + "\n"

    except Exception as e:
        contexto_adicional += f"[Advertencia Workspace: {str(e)}]\n"

    if OPENAI_API_KEY:
        try:
            mensajes_api = [{"role": "system", "content": SYSTEM_INSTRUCTION}]
            mensajes_api.extend(historial_conversacion)
            
            prompt_actual = f"Directiva del usuario: '{msg}'.\n{contexto_adicional}"
            mensajes_api.append({"role": "user", "content": prompt_actual})

            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
            payload = {"model": "gpt-4o-mini", "messages": mensajes_api, "temperature": 0.3}
            
            response = requests.post(url, json=payload, headers=headers)
            res_json = response.json()
            
            if "choices" in res_json:
                texto_respuesta = res_json["choices"][0]["message"]["content"]
                
                historial_conversacion.append({"role": "user", "content": msg})
                historial_conversacion.append({"role": "assistant", "content": texto_respuesta})
                if len(historial_conversacion) > 10:
                    historial_conversacion = historial_conversacion[-10:]
                    
                return jsonify({"reply": texto_respuesta})
            else:
                return jsonify({"reply": f"Error OpenAI: {str(res_json)}"})
                
        except Exception as e:
            return jsonify({"reply": f"Error crítico cognitivo: {str(e)}"})
    else:
        return jsonify({"reply": "Falta OPENAI_API_KEY."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
