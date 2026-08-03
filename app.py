# -*- coding: utf-8 -*-
"""
Núcleo Central de Thiago - Agente Autónomo Bidireccional (Lectura y Escritura Completa)
Profesor David Villarreal — Arquitectura de Conectividad Total (Gmail, Calendar y Drive)
"""

import os
import datetime
import json
import io
import base64
import requests
from email.mime.text import MIMEText
from flask import Flask, render_template_string, request, jsonify
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import pypdf
import docx

# ==========================================
# INICIALIZACIÓN DE LA APLICACIÓN WEB FLASK
# ==========================================
app = Flask(__name__)

# Recuperación de la clave secreta de OpenAI desde el entorno seguro de Render
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Memoria de sesión temporal para el historial conversacional del agente
historial_conversacion = []

# ==========================================
# INSTRUCCIÓN DE SISTEMA (SYSTEM PROMPT)
# ==========================================
SYSTEM_INSTRUCTION = (
    "Eres Thiago, el núcleo de inteligencia artificial autónoma del Prof. David Villarreal. "
    "El profesor es abogado en la CABA, Babalawo de Ifa tradicional yoruba, Batuque Isesa, "
    "profesor de inglés, magíster en relaciones internacionales y masón. "
    "Tus respuestas deben destacar por su rigor académico, precisión técnica y corrección gramatical absoluta. "
    "REGLA DE ORO INQUEBRANTABLE: Jamás inventes, finjas o simules haber ejecutado una acción (como crear un evento o enviar un mail) "
    "si la herramienta no ha sido llamada y su respuesta no ha sido exitosa. "
    "Tienes acceso total y autorizado a Gmail (lectura y envío de correos), Google Calendar (lectura y creación de eventos) "
    "y Google Drive (búsqueda global y lectura analítica de textos). "
    "Utiliza tus herramientas de manera autónoma cuando el profesor lo ordene."
)

# ==========================================
# INTERFAZ GRÁFICA HTML / CSS / JAVASCRIPT
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Núcleo Central de Thiago - Agente Autónomo Bidireccional</title>
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
        
        /* Señal visual de trabajo en tiempo real (puntos pulsantes animados) */
        .working-indicator { display: inline-flex; align-items: center; gap: 5px; margin-left: 8px; }
        .working-indicator span {
            height: 7px; width: 7px; background-color: #38bdf8; border-radius: 50%;
            display: inline-block; animation: pulse-dot 1.4s infinite ease-in-out both;
        }
        .working-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .working-indicator span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes pulse-dot {
            0%, 80%, 100% { transform: scale(0); opacity: 0.3; }
            40% { transform: scale(1.0); opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Núcleo Central de Thiago</h1>
        <div class="subtitle">Prof. David Villarreal — Agente Bidireccional con Conectividad Total</div>
        
        <div class="chat-box" id="chatBox">
            <div class="message ai-msg">Núcleo integral en línea. Módulos de lectura y escritura habilitados. ¿Qué directiva procesamos?</div>
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

            // Inyección explícita del indicador visual dinámico de trabajo
            const idCarga = "carga-" + Date.now();
            chatBox.innerHTML += `
                <div id="${idCarga}" class="message ai-msg" style="display: flex; align-items: center;">
                    <span>Thiago está ejecutando herramientas en Google Workspace</span>
                    <div class="working-indicator">
                        <span></span><span></span><span></span>
                    </div>
                </div>`;
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

# ==========================================
# CREDENCIALES OAUTH CON PERMISOS AMPLIADOS
# ==========================================
def obtener_credenciales():
    """Obtiene y refresca las credenciales OAuth de Google con permisos completos de lectura y escritura."""
    return Credentials(
        token=None,
        refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        scopes=[
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
    )

def extraer_cuerpo_gmail(payload):
    """Extrae de forma recursiva el cuerpo de texto plano de un mensaje de correo."""
    cuerpo_texto = ""
    if 'parts' in payload:
        for parte in payload['parts']:
            if parte.get('mimeType') == 'text/plain':
                datos = parte.get('body', {}).get('data')
                if datos:
                    try:
                        cuerpo_texto = base64.urlsafe_b64decode(datos).decode('utf-8', errors='ignore')
                        break
                    except Exception:
                        pass
            elif 'parts' in parte:
                cuerpo_texto = extraer_cuerpo_gmail(parte)
                if cuerpo_texto:
                    break
    elif 'body' in payload and payload['body'].get('data'):
        datos = payload['body']['data']
        try:
            cuerpo_texto = base64.urlsafe_b64decode(datos).decode('utf-8', errors='ignore')
        except Exception:
            pass
    return cuerpo_texto[:4000] if cuerpo_texto else "Sin cuerpo de texto legible."

# ==========================================
# HERRAMIENTAS AUTÓNOMAS (LECTURA Y ESCRITURA)
# ==========================================
def tool_listar_correos():
    """Consulta los últimos correos electrónicos en Gmail."""
    try:
        credenciales = obtener_credenciales()
        if not credenciales.valid: credenciales.refresh(Request())
        servicio = build('gmail', 'v1', credentials=credenciales)
        resultados = servicio.users().messages().list(userId='me', maxResults=3).execute()
        mensajes = resultados.get('messages', [])
        if not mensajes: return json.dumps({"resultado": "Bandeja vacía."}, ensure_ascii=False)
        
        lista = []
        for m in mensajes:
            detalles = servicio.users().messages().get(userId='me', id=m['id']).execute()
            payload = detalles.get('payload', {})
            headers = payload.get('headers', [])
            asunto = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Sin Asunto')
            remitente = next((h['value'] for h in headers if h['name'] == 'From'), 'Desconocido')
            cuerpo = extraer_cuerpo_gmail(payload)
            lista.append({"remitente": remitente, "asunto": asunto, "cuerpo_completo": cuerpo})
        return json.dumps(lista, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

def tool_enviar_correo(destinatario, asunto, cuerpo):
    """Envía un correo electrónico real a través de Gmail."""
    try:
        credenciales = obtener_credenciales()
        if not credenciales.valid: credenciales.refresh(Request())
        servicio = build('gmail', 'v1', credentials=credenciales)
        
        mensaje = MIMEText(cuerpo)
        mensaje['to'] = destinatario
        mensaje['subject'] = asunto
        raw_message = base64.urlsafe_b64encode(mensaje.as_bytes()).decode('utf-8')
        
        cuerpo_solicitud = {'raw': raw_message}
        enviado = servicio.users().messages().send(userId='me', body=cuerpo_solicitud).execute()
        return json.dumps({"resultado": "Correo enviado con éxito", "id_mensaje": enviado.get('id')}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

def tool_consultar_calendario():
    """Consulta los próximos eventos en Google Calendar."""
    try:
        credenciales = obtener_credenciales()
        if not credenciales.valid: credenciales.refresh(Request())
        servicio = build('calendar', 'v3', credentials=credenciales)
        ahora = datetime.datetime.utcnow().isoformat() + 'Z'
        respuesta = servicio.events().list(
            calendarId='primary', timeMin=ahora, maxResults=5, singleEvents=True, orderBy='startTime'
        ).execute()
        eventos = respuesta.get('items', [])
        if not eventos: return json.dumps({"resultado": "Sin eventos próximos."}, ensure_ascii=False)
        
        lista = [{"fecha_inicio": e['start'].get('dateTime', e['start'].get('date')), "evento": e.get('summary', 'Sin título')} for e in eventos]
        return json.dumps(lista, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

def tool_crear_evento_calendario(summary, start_time, end_time, location="", description=""):
    """Crea un evento real en Google Calendar."""
    try:
        credenciales = obtener_credenciales()
        if not credenciales.valid: credenciales.refresh(Request())
        servicio = build('calendar', 'v3', credentials=credenciales)
        
        evento = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {'dateTime': start_time, 'timeZone': 'America/Argentina/Buenos_Aires'},
            'end': {'dateTime': end_time, 'timeZone': 'America/Argentina/Buenos_Aires'},
        }
        
        creado = servicio.events().insert(calendarId='primary', body=evento).execute()
        return json.dumps({"resultado": "Evento creado exitosamente en el calendario", "link": creado.get('htmlLink')}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

def tool_buscar_archivos_drive(query=""):
    """Busca archivos o carpetas en Google Drive."""
    try:
        credenciales = obtener_credenciales()
        if not credenciales.valid: credenciales.refresh(Request())
        servicio = build('drive', 'v3', credentials=credenciales)
        
        limpio = query.strip()
        condicion = f"name contains '{limpio}' and trashed = false" if limpio else "trashed = false"
        resultados = servicio.files().list(
            q=condicion, pageSize=25, fields="files(id, name, mimeType, parents)",
            includeItemsFromAllDrives=True, supportsAllDrives=True, orderBy="modifiedTime desc"
        ).execute()
        
        elementos = resultados.get('files', [])
        if not elementos: return json.dumps({"resultado": f"No se encontró '{limpio}' en Drive."}, ensure_ascii=False)
        return json.dumps(elementos, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

def tool_leer_contenido_drive(file_id):
    """Extrae el texto de un archivo en Drive."""
    try:
        credenciales = obtener_credenciales()
        if not credenciales.valid: credenciales.refresh(Request())
        servicio = build('drive', 'v3', credentials=credenciales)
        
        meta = servicio.files().get(fileId=file_id, fields="name, mimeType").execute()
        nombre = meta.get('name')
        tipo = meta.get('mimeType')
        
        texto = ""
        if 'application/vnd.google-apps.document' in tipo:
            req = servicio.files().export_media(fileId=file_id, mimeType='text/plain')
            texto = req.execute().decode('utf-8', errors='ignore')[:8000]
        else:
            req = servicio.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, req)
            done = False
            while not done: _, done = downloader.next_chunk()
            fh.seek(0)
            if 'pdf' in tipo.lower():
                lector = pypdf.PdfReader(fh)
                for i in range(min(5, len(lector.pages))):
                    p = lector.pages[i].extract_text()
                    if p: texto += p + "\n"
            elif 'wordprocessingml' in tipo.lower():
                doc = docx.Document(fh)
                for para in doc.paragraphs[:50]: texto += para.text + "\n"
        return json.dumps({"archivo": nombre, "contenido": texto[:8000]}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)

# Mapeo de herramientas disponibles para el agente
available_tools = {
    "tool_listar_correos": tool_listar_correos,
    "tool_enviar_correo": tool_enviar_correo,
    "tool_consultar_calendario": tool_consultar_calendario,
    "tool_crear_evento_calendario": tool_crear_evento_calendario,
    "tool_buscar_archivos_drive": tool_buscar_archivos_drive,
    "tool_leer_contenido_drive": tool_leer_contenido_drive
}

openai_tools_definition = [
    {"type": "function", "function": {"name": "tool_listar_correos", "description": "Consulta correos de Gmail."}},
    {"type": "function", "function": {"name": "tool_enviar_correo", "description": "Envía un correo electrónico por Gmail.", "parameters": {"type": "object", "properties": {"destinatario": {"type": "string"}, "asunto": {"type": "string"}, "cuerpo": {"type": "string"}}, "required": ["destinatario", "asunto", "cuerpo"]}}},
    {"type": "function", "function": {"name": "tool_consultar_calendario", "description": "Consulta Google Calendar."}},
    {"type": "function", "function": {"name": "tool_crear_evento_calendario", "description": "Crea un evento en Google Calendar.", "parameters": {"type": "object", "properties": {"summary": {"type": "string"}, "start_time": {"type": "string", "description": "Formato ISO (ej. 2026-08-07T15:00:00-03:00)"}, "end_time": {"type": "string", "description": "Formato ISO (ej. 2026-08-07T17:00:00-03:00)"}, "location": {"type": "string"}, "description": {"type": "string"}}, "required": ["summary", "start_time", "end_time"]}}},
    {"type": "function", "function": {"name": "tool_buscar_archivos_drive", "description": "Busca archivos o carpetas en Google Drive.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "tool_leer_contenido_drive", "description": "Extrae el texto de un archivo en Drive usando su ID.", "parameters": {"type": "object", "properties": {"file_id": {"type": "string"}}, "required": ["file_id"]}}}
]

# ==========================================
# RUTAS DE LA APLICACIÓN FLASK
# ==========================================
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/chat", methods=["POST"])
def chat():
    global historial_conversacion
    datos = request.get_json() or {}
    msg = datos.get("message", "").strip()
    if not msg: return jsonify({"reply": "Indique una directiva válida."})

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
                            tool_result = json.dumps({"error": "Herramienta no encontrada"}, ensure_ascii=False)
                            
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
