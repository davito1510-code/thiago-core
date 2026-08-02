# -*- coding: utf-8 -*-
"""
Núcleo Central de Thiago - Versión con Memoria Cognitiva
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

# Memoria global temporal (almacena el historial de la conversación)
historial_conversacion = []

SYSTEM_INSTRUCTION = (
    "Eres Thiago, el núcleo de inteligencia artificial autónoma del Prof. David Villarreal. "
    "El profesor es abogado en la CABA, Babalawo de Ifa tradicional yoruba, Batuque Isesa, "
    "profesor de inglés, magíster en relaciones internacionales y masón. "
    "Tus respuestas deben destacar por su rigor académico y precisión técnica. "
    "REGLAS ESTRICTAS DE OPERACIÓN: "
    "1. TIENES ACCESO a los correos de Gmail, a los eventos de Google Calendar y a los archivos recientes de Google Drive del profesor. Si él pregunta si tienes acceso a alguna de estas herramientas, RESPONDE AFIRMATIVAMENTE. "
    "2. NO PUEDES navegar por carpetas específicas ni buscar archivos por nombre. Solo puedes ver los archivos más recientes. Si el profesor te pide entrar a una carpeta específica, infórmale con honestidad tu limitación técnica y pídele que modifique el archivo recientemente para que aparezca en tu radar. "
    "3. NUNCA inventes que has accedido a un lugar si no tienes los datos en tu contexto."
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
    </style>
</head>
<body>
    <div class="container">
        <h1>Núcleo Central de Thiago</h1>
        <div class="subtitle">Prof. David Villarreal — Memoria Activa</div>
        
        <div class="chat-box" id="chatBox">
            <div class="message ai-msg">Núcleo cognitivo en línea. Memoria de sesión activada. ¿Qué directiva procesamos?</div>
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

            const idCarga = "carga-" + Date.now();
            chatBox.innerHTML += `<div id="${idCarga}" class="message ai-msg" style="opacity: 0.7;">Procesando...</div>`;
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
            } catch (error) {
                document.getElementById(idCarga).remove();
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

def obtener_credenciales():
    creds = Credentials(
        token=None,
        refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        scopes=[
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/calendar.readonly',
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
        if any(k in msg_lower for k in ["correo", "mail", "bandeja", "mails"]):
            service_gmail = build('gmail', 'v1', credentials=creds)
            results = service_gmail.users().messages().list(userId='me', maxResults=3).execute()
            messages = results.get('messages', [])
            if messages:
                contexto_adicional += "\nESTADO DEL SISTEMA: Tienes acceso total a los correos del usuario. Los correos recientes están sincronizados.\n"

        # Lógica de Drive (Simplificada para evitar alucinaciones)
        if any(k in msg_lower for k in ["drive", "archivo", "carpeta"]):
            service_drive = build('drive', 'v3', credentials=creds)
            results = service_drive.files().list(pageSize=3, fields="files(id, name)", orderBy="modifiedTime desc").execute()
            items = results.get('files', [])
            if items:
                contexto_adicional += "\nESTADO DEL SISTEMA: Tienes acceso a Drive. Los archivos más recientes son: " + ", ".join([i['name'] for i in items]) + ".\n"

    except Exception as e:
        contexto_adicional += f"[Advertencia de Sistema: {str(e)}]\n"

    if OPENAI_API_KEY:
        try:
            # Construcción del prompt con memoria
            mensajes_api = [{"role": "system", "content": SYSTEM_INSTRUCTION}]
            mensajes_api.extend(historial_conversacion)
            
            prompt_actual = f"Directiva actual: '{msg}'.\n{contexto_adicional}"
            mensajes_api.append({"role": "user", "content": prompt_actual})

            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
            payload = {"model": "gpt-4o-mini", "messages": mensajes_api, "temperature": 0.3}
            
            response = requests.post(url, json=payload, headers=headers)
            res_json = response.json()
            
            if "choices" in res_json:
                texto_respuesta = res_json["choices"][0]["message"]["content"]
                
                # Actualizamos la memoria
                historial_conversacion.append({"role": "user", "content": msg})
                historial_conversacion.append({"role": "assistant", "content": texto_respuesta})
                
                # Mantenemos solo los últimos 10 mensajes para no saturar la API
                if len(historial_conversacion) > 10:
                    historial_conversacion = historial_conversacion[-10:]
                    
                return jsonify({"reply": texto_respuesta})
            else:
                return jsonify({"reply": f"Error OpenAI: {str(res_json)}"})
                
        except Exception as e:
            return jsonify({"reply": f"Error crítico: {str(e)}"})
    else:
        return jsonify({"reply": "Falta OPENAI_API_KEY."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
