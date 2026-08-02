# -*- coding: utf-8 -*-
"""
Núcleo Central de Thiago - Agente Autónomo Integrado (Gmail, Calendar y Drive)
"""

import os
import datetime
import json
import io
import base64
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
    "TIENES ACCESO TOTAL Y AUTORIZADO a Gmail (cuerpo íntegro de correos), Google Calendar (eventos y agenda) "
    "y Google Drive (búsqueda y lectura analítica de documentos). "
    "Utiliza tus herramientas de manera autónoma y precisa cuando el profesor lo ordene."
)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Núcleo Central de Thiago - Agente Integrado</title>
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
        <div class="subtitle">Prof. David Villarreal — Agente Autónomo con Conectividad Total</div>
        
        <div class="chat-box" id="chatBox">
            <div class="message ai-msg">Núcleo integral en línea. Módulos de Gmail, Calendar y Drive sincronizados. ¿Qué directiva procesamos?</div>
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
            chatBox.innerHTML += `<div id="${idCarga}" class="message ai-msg" style="opacity: 0.7;">Ejecutando agente autónomo...</div>`;
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
    return Credentials(
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

def extraer_cuerpo_gmail(payload):
    """Extrae recursivamente el cuerpo de texto plano de un mensaje de correo."""
    body = ""
    if 'parts' in payload:
        for part in payload['parts']:
            if part.get('mimeType') == 'text/plain':
                data = part.get('body', {}).get('data')
                if data:
                    try:
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        break
                    except:
                        pass
            elif 'parts' in part:
                body = extraer_cuerpo_gmail(part)
                if body: break
    elif 'body' in payload and payload['body'].get('data'):
        data = payload['body']['data']
        try:
            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        except:
            pass
    return body[:4000] if body else "Sin cuerpo de texto legible."

# --- HERRAMIENTAS AUTÓNOMAS (TOOLS) ---

def tool_listar_correos():
    """Consulta los últimos correos electrónicos de Gmail y extrae su contenido íntegro."""
    try:
        creds = obtener_credenciales()
        if not creds.valid: creds.refresh(Request())
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().messages().list(userId='me', maxResults=3).execute()
        messages = results.get('messages', [])
        if not messages:
            return json.dumps({"resultado": "Bandeja de entrada vacía."})
        
        lista = []
        for m in messages:
            msg_data = service.users().messages().get(userId='me', id=m['id']).execute()
            payload = msg_data.get('payload', {})
            headers = payload.get('headers', [])
            asunto = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Sin Asunto')
            remitente = next((h['value'] for h in headers if h['name'] == 'From'), 'Desconocido')
            cuerpo = extraer_cuerpo_gmail(payload)
            lista.append({"remitente": remitente, "asunto": asunto, "cuerpo_completo": cuerpo})
        return json.dumps(lista, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})

def tool_consultar_calendario():
    """Consulta los próximos eventos en Google Calendar."""
    try:
        creds = obtener_credenciales()
        if not creds.valid: creds.refresh(Request())
        service = build('calendar', 'v3', credentials=creds)
        
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId='primary', timeMin=now,
            maxResults=5, singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        
        if not events:
            return json.dumps({"resultado": "No hay eventos próximos en la agenda."})
        
        lista_eventos = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event.get('summary', 'Sin título')
            lista_eventos.append({"fecha_inicio": start, "evento": summary})
            
        return json.dumps(lista_eventos, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})

def tool_buscar_archivos_drive(query=""):
    """Busca archivos en Google Drive por nombre."""
    try:
        creds = obtener_credenciales()
        if not creds.valid: creds.refresh(Request())
        service = build('drive', 'v3', credentials=creds)
        q = f"name contains '{query}'" if query else ""
        results = service.files().list(
            q=q, pageSize=10,
            fields="files(id, name, mimeType)",
            orderBy="modifiedTime desc"
        ).execute()
        items = results.get('files', [])
        return json.dumps(items, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})

def tool_leer_contenido_drive(file_id):
    """Extrae el texto interno de un archivo específico de Drive dado su ID."""
    try:
        creds = obtener_credenciales()
        if not creds.valid: creds.refresh(Request())
        service = build('drive', 'v3', credentials=creds)
        file_meta = service.files().get(fileId=file_id, fields="name, mimeType").execute()
        nombre = file_meta.get('name')
        mime_type = file_meta.get('mimeType')
        
        limite = 8000
        if 'application/vnd.google-apps.document' in mime_type:
            req = service.files().export_media(fileId=file_id, mimeType='text/plain')
            contenido = req.execute().decode('utf-8')
            return json.dumps({"archivo": nombre, "contenido": contenido[:limite]}, ensure_ascii=False)
        else:
            req = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, req)
            done = False
            while done is False:
                _, done = downloader.next_chunk()
            fh.seek(0)
            texto = ""
            if 'pdf' in mime_type.lower():
                lector = pypdf.PdfReader(fh)
                for i in range(min(5, len(lector.pages))):
                    p_txt = lector.pages[i].extract_text()
                    if p_txt: texto += p_txt + "\n"
            elif 'wordprocessingml' in mime_type.lower():
                doc = docx.Document(fh)
                for para in doc.paragraphs[:50]:
                    texto += para.text + "\n"
            return json.dumps({"archivo": nombre, "contenido": texto[:limite]}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})

available_tools = {
    "tool_listar_correos": tool_listar_correos,
    "tool_consultar_calendario": tool_consultar_calendario,
    "tool_buscar_archivos_drive": tool_buscar_archivos_drive,
    "tool_leer_contenido_drive": tool_leer_contenido_drive
}

openai_tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "tool_listar_correos",
            "description": "Consulta los últimos correos de Gmail y extrae su cuerpo íntegro."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_consultar_calendario",
            "description": "Consulta los próximos eventos y citas en Google Calendar."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_buscar_archivos_drive",
            "description": "Busca archivos en Google Drive por nombre para obtener sus IDs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Término de búsqueda (ej. 'Clase 11')."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_leer_contenido_drive",
            "description": "Extrae el texto interno de un archivo de Drive usando su ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_id": {"type": "string", "description": "El ID del archivo en Google Drive."}
                },
                "required": ["file_id"]
            }
        }
    }
]

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

    if OPENAI_API_KEY:
        try:
            mensajes_api = [{"role": "system", "content": SYSTEM_INSTRUCTION}]
            mensajes_api.extend(historial_conversacion)
            mensajes_api.append({"role": "user", "content": msg})

            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
            
            payload = {
                "model": "gpt-4o-mini",
                "messages": mensajes_api,
                "tools": openai_tools_definition,
                "tool_choice": "auto",
                "temperature": 0.3
            }
            
            response = requests.post(url, json=payload, headers=headers)
            res_json = response.json()
            
            if "choices" in res_json:
                message_resp = res_json["choices"][0]["message"]
                
                if "tool_calls" in message_resp:
                    mensajes_api.append(message_resp)
                    for tool_call in message_resp["tool_calls"]:
                        func_name = tool_call["function"]["name"]
                        func_args = json.loads(tool_call["function"]["arguments"] or "{}")
                        
                        if func_name in available_tools:
                            tool_result = available_tools[func_name](**func_args)
                        else:
                            tool_result = json.dumps({"error": "Herramienta no encontrada"})
                            
                        mensajes_api.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": tool_result
                        })
                    
                    payload_seguimiento = {
                        "model": "gpt-4o-mini",
                        "messages": mensajes_api,
                        "temperature": 0.3
                    }
                    resp_final = requests.post(url, json=payload_seguimiento, headers=headers)
                    json_final = resp_final.json()
                    texto_respuesta = json_final["choices"][0]["message"]["content"]
                else:
                    texto_respuesta = message_resp.get("content", "Procesamiento completado.")

                historial_conversacion.append({"role": "user", "content": msg})
                historial_conversacion.append({"role": "assistant", "content": texto_respuesta})
                if len(historial_conversacion) > 10:
                    historial_conversacion = historial_conversacion[-10:]
                    
                return jsonify({"reply": texto_respuesta})
            else:
                return jsonify({"reply": f"Error OpenAI: {str(res_json)}"})
                
        except Exception as e:
            return jsonify({"reply": f"Error crítico del agente: {str(e)}"})
    else:
        return jsonify({"reply": "Falta OPENAI_API_KEY."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
