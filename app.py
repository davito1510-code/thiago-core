# -*- coding: utf-8 -*-
"""
=============================================================================
 NÚCLEO CENTRAL DE THIAGO - AGENTE AUTÓNOMO BIDIRECCIONAL INTEGRAL
 Arquitectura de Conectividad Total y Razonamiento Cognitivo Avanzado
 Desarrollado exclusivamente para el Prof. David Villarreal
 Abogado, Babalawo de Ifa tradicional yoruba, Batuque Isesa, profesor de inglés,
 magíster en relaciones internacionales, masón y doctorando.
=============================================================================
"""

import os
import datetime
from datetime import timezone
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
from duckduckgo_search import DDGS

# =============================================================================
# SECCIÓN 1: INICIALIZACIÓN Y CONFIGURACIÓN DEL SERVIDOR FLASK
# =============================================================================
app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
historial_conversacion = []

# =============================================================================
# SECCIÓN 2: INSTRUCCIÓN DE SISTEMA (SYSTEM PROMPT) Y PERFIL DE IDENTIDAD
# =============================================================================
SYSTEM_INSTRUCTION = (
    "Eres Thiago, el núcleo de inteligencia artificial autónoma del Prof. David Villarreal. "
    "El profesor es abogado en la CABA, Babalawo de Ifa tradicional yoruba, Batuque Isesa, "
    "profesor de inglés, magíster en relaciones internacionales y masón. "
    "Tus respuestas deben destacar por su rigor académico, precisión técnica y corrección gramatical absoluta. "
    "REGLA DE ORO INQUEBRANTABLE: Jamás inventes, finjas o simules haber ejecutado una acción "
    "(como crear un evento en el calendario o enviar un correo electrónico) si la herramienta correspondiente "
    "no ha sido invocada con éxito y su respuesta oficial no ha sido procesada. "
    "Tienes acceso total y autorizado a la cuenta del Prof. David Villarreal en Gmail (lectura y envío de correos), "
    "Google Calendar (lectura extendida por rangos semanales y creación de eventos con invitación a asistentes), Google Drive "
    "(búsqueda global, navegación estricta por jerarquía de carpetas y lectura analítica de textos) y BÚSQUEDA WEB AUTÓNOMA (DuckDuckGo). "
    "Cuando el profesor mencione 'mis mails', 'mi calendario' o 'mi drive', comprende de inmediato que se refiere "
    "a su cuenta personal autorizada y ejecuta las herramientas de forma autónoma sin titubear."
)

# =============================================================================
# SECCIÓN 3: INTERFAZ GRÁFICA DE USUARIO (HTML, CSS Y JAVASCRIPT NATIVO)
# =============================================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Núcleo Central de Thiago - Agente Autónomo Bidireccional</title>
    <style>
        :root {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-terminal: #090d16;
            --accent-blue: #38bdf8;
            --accent-user: #0284c7;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border-color: #334155;
            --error-color: #f87171;
            --active-mic: #ef4444;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg-primary);
            color: var(--text-main);
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
            box-sizing: border-box;
        }

        .container {
            width: 100%;
            max-width: 800px;
            background: var(--bg-secondary);
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.6);
            border: 1px solid var(--border-color);
        }

        h1 {
            color: var(--accent-blue);
            text-align: center;
            font-size: 1.75rem;
            margin-bottom: 5px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }

        .subtitle {
            text-align: center;
            color: var(--text-muted);
            margin-bottom: 25px;
            font-size: 0.95rem;
            font-weight: 500;
        }

        .chat-box {
            background: var(--bg-terminal);
            border: 1px solid var(--border-color);
            height: 420px;
            overflow-y: auto;
            padding: 18px;
            margin-bottom: 20px;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            gap: 14px;
            box-shadow: inset 0 2px 6px rgba(0,0,0,0.4);
        }

        .message {
            padding: 12px 16px;
            border-radius: 8px;
            max-width: 85%;
            line-height: 1.6;
            word-break: break-word;
            white-space: pre-wrap;
            font-size: 0.95rem;
        }

        .user-msg {
            background: var(--accent-user);
            color: white;
            align-self: flex-end;
        }

        .ai-msg {
            background: var(--border-color);
            color: var(--text-main);
            align-self: flex-start;
            border: 1px solid #475569;
        }

        .input-group {
            display: flex;
            gap: 10px;
        }

        input[type="text"] {
            flex: 1;
            padding: 12px 16px;
            border-radius: 8px;
            border: 1px solid #475569;
            background: var(--bg-primary);
            color: white;
            font-size: 1rem;
            outline: none;
            transition: border-color 0.2s;
        }

        input[type="text"]:focus {
            border-color: var(--accent-blue);
        }

        button {
            padding: 12px 20px;
            background-color: var(--accent-blue);
            color: var(--bg-primary);
            border: none;
            border-radius: 8px;
            font-weight: 700;
            cursor: pointer;
            transition: background-color 0.2s, transform 0.1s;
        }

        button:hover {
            background-color: #7dd3fc;
        }

        button:active {
            transform: scale(0.98);
        }

        #micBtn {
            background-color: var(--border-color);
            color: var(--accent-blue);
            border: 1px solid var(--accent-blue);
            font-size: 1.1rem;
            padding: 12px 16px;
        }

        #micBtn.active {
            background-color: var(--active-mic);
            color: white;
            border-color: var(--active-mic);
            animation: pulse-mic 1.5s infinite;
        }

        @keyframes pulse-mic {
            0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
            70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
            100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
        }

        .working-indicator {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            margin-left: 10px;
        }

        .working-indicator span {
            height: 8px;
            width: 8px;
            background-color: var(--accent-blue);
            border-radius: 50%;
            display: inline-block;
            animation: pulse-dot 1.4s infinite ease-in-out both;
        }

        .working-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .working-indicator span:nth-child(3) { animation-delay: 0.4s; }

        @keyframes pulse-dot {
            0%, 80%, 100% { transform: scale(0); opacity: 0.3; }
            40% { transform: scale(1.0); opacity: 1; }
        }

        .error-text {
            color: var(--error-color);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Núcleo Central de Thiago</h1>
        <div class="subtitle">Prof. David Villarreal — Agente Autónomo Bidireccional</div>
        
        <div class="chat-box" id="chatBox">
            <div class="message ai-msg">Núcleo integral en línea. Módulos cognitivos, de lectura analítica y señal visual operativos. ¿Qué directiva procesamos?</div>
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
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
            }
            if (escuchando) {
                try { recognition.stop(); } catch(e) {}
                detenerEscuchaVisual();
            } else {
                try {
                    recognition.start();
                    document.getElementById('micBtn').classList.add('active');
                    document.getElementById('userInput').placeholder = "Escuchando directiva...";
                    escuchando = true;
                } catch (e) {
                    detenerEscuchaVisual();
                }
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
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
            }
            if (escuchando && recognition) {
                try { recognition.stop(); } catch(e) {}
                detenerEscuchaVisual();
            }

            const input = document.getElementById('userInput');
            const chatBox = document.getElementById('chatBox');
            const texto = input.value.trim();
            if (!texto) return;

            chatBox.innerHTML += `<div class="message user-msg">${texto}</div>`;
            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            const idCarga = "carga-" + Date.now();
            chatBox.innerHTML += `
                <div id="${idCarga}" class="message ai-msg" style="display: flex; align-items: center;">
                    <span>Thiago está procesando cognitivamente la directiva en Google Workspace</span>
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
                chatBox.innerHTML += `<div class="message ai-msg error-text">Error crítico de comunicación con el núcleo.</div>`;
            }
        }

        document.getElementById('userInput').addEventListener('keypress', function (e) {
            if (e.key === 'Enter') enviarMensaje();
        });
    </script>
</body>
</html>
"""

# =============================================================================
# SECCIÓN 4: GESTIÓN DE CREDENCIALES OAUTH Y CONECTIVIDAD GOOGLE
# =============================================================================
def obtener_credenciales():
    """Construye y refresca las credenciales OAuth aplicando sanitización estricta."""
    r_token = os.getenv("GOOGLE_REFRESH_TOKEN", "").strip().strip('"\'')
    c_id = os.getenv("GOOGLE_CLIENT_ID", "").strip().strip('"\'')
    c_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip().strip('"\'')

    credenciales = Credentials(
        token=None,
        refresh_token=r_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=c_id,
        client_secret=c_secret,
        scopes=[
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
    )
    if not credenciales.valid:
        credenciales.refresh(Request())
    return credenciales

def extraer_cuerpo_gmail(payload):
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

# =============================================================================
# SECCIÓN 5: HERRAMIENTAS AUTÓNOMAS (TOOLS) DE LECTURA Y ESCRITURA
# =============================================================================
def tool_listar_correos():
    """Consulta los últimos correos electrónicos de la bandeja de entrada de Gmail."""
    try:
        credenciales = obtener_credenciales()
        servicio = build('gmail', 'v1', credentials=credenciales)
        resultados = servicio.users().messages().list(userId='me', maxResults=5).execute()
        mensajes = resultados.get('messages', [])
        if not mensajes:
            return json.dumps({"resultado": "La bandeja de entrada se encuentra vacía."}, ensure_ascii=False)
        
        lista_correos = []
        for mensaje in mensajes:
            detalle = servicio.users().messages().get(userId='me', id=mensaje['id']).execute()
            payload = detalle.get('payload', {})
            encabezados = payload.get('headers', [])
            asunto = next((h['value'] for h in encabezados if h['name'] == 'Subject'), 'Sin Asunto')
            remitente = next((h['value'] for h in encabezados if h['name'] == 'From'), 'Desconocido')
            fecha = next((h['value'] for h in encabezados if h['name'] == 'Date'), 'Fecha desconocida')
            cuerpo = extraer_cuerpo_gmail(payload)
            lista_correos.append({
                "fecha": fecha,
                "remitente": remitente,
                "asunto": asunto,
                "cuerpo_completo": cuerpo
            })
        return json.dumps(lista_correos, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO GMAIL DETALLADO]: {repr(error)}")
        return json.dumps({"error_tecnico_gmail": str(error)}, ensure_ascii=False)

def tool_enviar_correo(destinatario, asunto, cuerpo):
    """Envía un correo electrónico a través de la infraestructura de Gmail."""
    try:
        credenciales = obtener_credenciales()
        servicio = build('gmail', 'v1', credentials=credenciales)
        
        mensaje = MIMEText(cuerpo)
        mensaje['to'] = destinatario
        mensaje['subject'] = asunto
        raw_message = base64.urlsafe_b64encode(mensaje.as_bytes()).decode('utf-8')
        
        enviado = servicio.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        return json.dumps({"resultado": "Correo enviado con éxito", "id_mensaje": enviado.get('id')}, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO GMAIL ENVÍO DETALLADO]: {repr(error)}")
        return json.dumps({"error_tecnico_gmail_envio": str(error)}, ensure_ascii=False)

def tool_consultar_calendario():
    """Consulta los próximos eventos y citas agendados en Google Calendar con alta capacidad (hasta 50 eventos para cubrir semanas completas)."""
    try:
        credenciales = obtener_credenciales()
        servicio = build('calendar', 'v3', credentials=credenciales)
        ahora = datetime.datetime.now(timezone.utc).isoformat()
        
        respuesta_eventos = servicio.events().list(
            calendarId='primary',
            timeMin=ahora,
            maxResults=50,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        eventos = respuesta_eventos.get('items', [])
        if not eventos:
            return json.dumps({"resultado": "No hay eventos próximos registrados en la agenda."}, ensure_ascii=False)
        
        lista_eventos = []
        for evento in eventos:
            inicio = evento['start'].get('dateTime', evento['start'].get('date'))
            fin = evento['end'].get('dateTime', evento['end'].get('date'))
            titulo = evento.get('summary', 'Sin título')
            ubicacion = evento.get('location', 'Sin ubicación')
            lista_eventos.append({"fecha_inicio": inicio, "fecha_fin": fin, "evento": titulo, "ubicacion": ubicacion})
            
        return json.dumps(lista_eventos, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO CALENDAR DETALLADO]: {repr(error)}")
        return json.dumps({"error_tecnico_calendar": str(error)}, ensure_ascii=False)

def tool_crear_evento_calendario(summary, start_time, end_time, location="", description="", attendees=None):
    """Crea un evento en Google Calendar con asistentes opcionales."""
    try:
        credenciales = obtener_credenciales()
        servicio = build('calendar', 'v3', credentials=credenciales)
        
        evento = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {'dateTime': start_time, 'timeZone': 'America/Argentina/Buenos_Aires'},
            'end': {'dateTime': end_time, 'timeZone': 'America/Argentina/Buenos_Aires'},
        }
        
        if attendees:
            if isinstance(attendees, list):
                evento['attendees'] = [{'email': email.strip()} for email in attendees]
            elif isinstance(attendees, str):
                evento['attendees'] = [{'email': email.strip()} for email in attendees.split(',')]
        
        creado = servicio.events().insert(calendarId='primary', body=evento, sendUpdates='all').execute()
        return json.dumps({"resultado": "Evento creado exitosamente en el calendario", "link": creado.get('htmlLink')}, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO CALENDAR CREACIÓN DETALLADO]: {repr(error)}")
        return json.dumps({"error_tecnico_calendar_creacion": str(error)}, ensure_ascii=False)

def tool_buscar_archivos_drive(query=""):
    """Busca archivos o carpetas en Google Drive aplicando sanitización estricta de cadenas."""
    try:
        credenciales = obtener_credenciales()
        servicio = build('drive', 'v3', credentials=credenciales)
        
        consulta_limpia = query.strip().replace("'", "\\'")
        condicion = f"name contains '{consulta_limpia}' and trashed = false" if consulta_limpia else "trashed = false"
        
        resultados = servicio.files().list(
            q=condicion,
            pageSize=30,
            fields="files(id, name, mimeType, parents)",
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            orderBy="modifiedTime desc"
        ).execute()
        
        elementos = resultados.get('files', [])
        if not elementos:
            return json.dumps({"resultado": f"No se encontró ningún archivo con el término '{consulta_limpia}' en Google Drive."}, ensure_ascii=False)
        return json.dumps(elementos, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO DRIVE BÚSQUEDA DETALLADO]: {repr(error)}")
        return json.dumps({"error_tecnico_drive": str(error)}, ensure_ascii=False)

def tool_leer_contenido_drive(file_id):
    """Extrae el contenido textual de un archivo específico de Google Drive."""
    try:
        credenciales = obtener_credenciales()
        servicio = build('drive', 'v3', credentials=credenciales)
        
        metadatos = servicio.files().get(fileId=file_id, fields="name, mimeType").execute()
        nombre_archivo = metadatos.get('name')
        tipo_mime = metadatos.get('mimeType')
        
        texto_extraido = ""
        
        if 'application/vnd.google-apps.document' in tipo_mime:
            solicitud = servicio.files().export_media(fileId=file_id, mimeType='text/plain')
            texto_extraido = solicitud.execute().decode('utf-8', errors='ignore')
        else:
            solicitud = servicio.files().get_media(fileId=file_id)
            buffer_memoria = io.BytesIO()
            descargador = MediaIoBaseDownload(buffer_memoria, solicitud)
            terminado = False
            while not terminado:
                _, terminado = descargador.next_chunk()
            buffer_memoria.seek(0)
            
            if 'pdf' in tipo_mime.lower():
                lector_pdf = pypdf.PdfReader(buffer_memoria)
                for numero_pagina in range(min(10, len(lector_pdf.pages))):
                    pagina_texto = lector_pdf.pages[numero_pagina].extract_text()
                    if pagina_texto:
                        texto_extraido += pagina_texto + "\n"
            elif 'wordprocessingml' in tipo_mime.lower():
                documento_word = docx.Document(buffer_memoria)
                for parrafo in documento_word.paragraphs[:100]:
                    texto_extraido += parrafo.text + "\n"
                    
        return json.dumps({"archivo": nombre_archivo, "contenido": texto_extraido[:8000]}, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO DRIVE LECTURA DETALLADO]: {repr(error)}")
        return json.dumps({"error_tecnico_drive_lectura": str(error)}, ensure_ascii=False)

# --- NUEVAS CAPACIDADES INCORPORADAS (BLINDADAS) ---
def tool_busqueda_web(query):
    """Realiza una búsqueda web con control absoluto de excepciones ante restricciones de IP en la nube."""
    try:
        resultados = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                resultados.append({
                    "title": r.get("title", "Sin título"),
                    "href": r.get("href", "Sin enlace"),
                    "body": r.get("body", "Sin descripción")
                })
        
        if not resultados:
            return json.dumps({
                "resultado": "La consulta no arrojó resultados activos en la web en este momento."
            }, ensure_ascii=False)
            
        return json.dumps(resultados, ensure_ascii=False)
        
    except Exception as error:
        error_str = str(error)
        print(f"[ADVERTENCIA TÉCNICA DE RED - WEB]: {error_str}")
        return json.dumps({
            "error_tecnico_web": error_str
        }, ensure_ascii=False)

def tool_listar_contenido_carpeta_drive(nombre_carpeta=""):
    """Busca una carpeta por nombre en Google Drive y lista explícitamente todos los archivos contenidos dentro de ella (por ID de padre)."""
    try:
        credenciales = obtener_credenciales()
        servicio = build('drive', 'v3', credentials=credenciales)
        
        nombre_limpio = nombre_carpeta.strip().replace("'", "\\'")
        query_carpeta = f"name = '{nombre_limpio}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        res_carpeta = servicio.files().list(q=query_carpeta, pageSize=5, fields="files(id, name)", supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        carpetas = res_carpeta.get('files', [])
        
        if not carpetas:
            query_flex = f"name contains '{nombre_limpio}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            res_flex = servicio.files().list(q=query_flex, pageSize=5, fields="files(id, name)", supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
            carpetas = res_flex.get('files', [])
            if not carpetas:
                return json.dumps({"resultado": f"No se encontró ninguna carpeta con el nombre '{nombre_carpeta}' en Google Drive."}, ensure_ascii=False)
        
        carpeta_id = carpetas[0]['id']
        nombre_encontrado = carpetas[0]['name']
        
        query_hijos = f"'{carpeta_id}' in parents and trashed = false"
        res_hijos = servicio.files().list(
            q=query_hijos,
            pageSize=50,
            fields="files(id, name, mimeType, modifiedTime)",
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            orderBy="name asc"
        ).execute()
        
        hijos = res_hijos.get('files', [])
        if not hijos:
            return json.dumps({"resultado": f"La carpeta '{nombre_encontrado}' (ID: {carpeta_id}) existe pero se encuentra vacía o no tiene elementos accesibles."}, ensure_ascii=False)
            
        lista_elementos = []
        for hijo in hijos:
            es_carpeta = hijo.get('mimeType') == 'application/vnd.google-apps.folder'
            tipo_elem = "Carpeta" if es_carpeta else "Archivo"
            lista_elementos.append({
                "tipo": tipo_elem,
                "id": hijo.get('id'),
                "nombre": hijo.get('name'),
                "modificado": hijo.get('modifiedTime')
            })
            
        return json.dumps({"carpeta_madre": nombre_encontrado, "id_carpeta": carpeta_id, "elementos": lista_elementos}, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO LISTAR CARPETA DRIVE]: {repr(error)}")
        return json.dumps({"error_tecnico_listar_carpeta": str(error)}, ensure_ascii=False)

# =============================================================================
# SECCIÓN 6: MAPEO DE HERRAMIENTAS Y ESPECIFICACIÓN DE FUNCIONES PARA OPENAI
# =============================================================================
available_tools = {
    "tool_listar_correos": tool_listar_correos,
    "tool_enviar_correo": tool_enviar_correo,
    "tool_consultar_calendario": tool_consultar_calendario,
    "tool_crear_evento_calendario": tool_crear_evento_calendario,
    "tool_buscar_archivos_drive": tool_buscar_archivos_drive,
    "tool_leer_contenido_drive": tool_leer_contenido_drive,
    "tool_busqueda_web": tool_busqueda_web,
    "tool_listar_contenido_carpeta_drive": tool_listar_contenido_carpeta_drive
}

openai_tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "tool_listar_correos",
            "description": "Consulta los últimos correos de Gmail del profesor David Villarreal."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_enviar_correo",
            "description": "Envía un correo electrónico real a través de Gmail.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destinatario": {"type": "string", "description": "Dirección de correo del destinatario."},
                    "asunto": {"type": "string", "description": "Asunto del mensaje."},
                    "cuerpo": {"type": "string", "description": "Contenido textual del correo."}
                },
                "required": ["destinatario", "asunto", "cuerpo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_consultar_calendario",
            "description": "Consulta los próximos eventos y citas registrados en el Google Calendar del profesor David Villarreal (ampliado hasta 50 eventos para cobertura semanal completa)."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_crear_evento_calendario",
            "description": "Crea un evento real en Google Calendar con fecha, hora, ubicación, descripción y asistentes invitados.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Título o nombre del evento."},
                    "start_time": {"type": "string", "description": "Fecha y hora de inicio en formato ISO."},
                    "end_time": {"type": "string", "description": "Fecha y hora de finalización en formato ISO."},
                    "location": {"type": "string", "description": "Ubicación o dirección física."},
                    "description": {"type": "string", "description": "Detalles adicionales del evento."},
                    "attendees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de correos electrónicos de los invitados."
                    }
                },
                "required": ["summary", "start_time", "end_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_buscar_archivos_drive",
            "description": "Busca archivos o carpetas en Google Drive por palabra clave (ej. 'bibliografia', 'masonia').",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Término de búsqueda."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_listar_contenido_carpeta_drive",
            "description": "Busca una carpeta específica por su nombre en Google Drive y lista todos los archivos y subcarpetas que contiene en su interior.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_carpeta": {"type": "string", "description": "Nombre exacto o aproximado de la carpeta (ej. '3382', 'ACTIVIDADES')."}
                },
                "required": ["nombre_carpeta"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_leer_contenido_drive",
            "description": "Extrae el texto de un archivo específico de Drive dado su ID único.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_id": {"type": "string", "description": "El identificador único (ID) del archivo en Google Drive."}
                },
                "required": ["file_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_busqueda_web",
            "description": "Realiza una búsqueda en internet mediante DuckDuckGo para extraer información actualizada.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Consulta de búsqueda para la web."}
                },
                "required": ["query"]
            }
        }
    }
]

# =============================================================================
# SECCIÓN 7: RUTAS Y CONTROLADORES DE LA APLICACIÓN WEB FLASK (LOOP COGNITIVO)
# =============================================================================
@app.route("/")
def index():
    """Renderiza la interfaz gráfica principal de Thiago."""
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Controlador principal del agente autónomo con motor cognitivo de multi-razonamiento.
    Gestiona las peticiones, ejecuta llamadas a herramientas y procesa excepciones con precisión.
    """
    global historial_conversacion
    datos_solicitud = request.get_json() or {}
    mensaje_usuario = datos_solicitud.get("message", "").strip()
    if not mensaje_usuario:
        return jsonify({"reply": "Indique una directiva operativa válida."})

    if OPENAI_API_KEY:
        try:
            mensajes_api = [{"role": "system", "content": SYSTEM_INSTRUCTION}]
            mensajes_api.extend(historial_conversacion)
            mensajes_api.append({"role": "user", "content": mensaje_usuario})

            url_api = "https://api.openai.com/v1/chat/completions"
            cabeceras = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
            
            payload_inicial = {
                "model": "gpt-4o-mini",
                "messages": mensajes_api,
                "tools": openai_tools_definition,
                "tool_choice": "auto",
                "temperature": 0.1
            }
            
            respuesta = requests.post(url_api, json=payload_inicial, headers=cabeceras)
            respuesta_json = respuesta.json()
            
            if "choices" in respuesta_json:
                mensaje_respuesta = respuesta_json["choices"][0]["message"]
                
                # Bucle cognitivo de ejecución de herramientas autónomas
                if "tool_calls" in mensaje_respuesta:
                    mensajes_api.append(mensaje_respuesta)
                    for llamada_herramienta in mensaje_respuesta["tool_calls"]:
                        nombre_funcion = llamada_herramienta["function"]["name"]
                        try:
                            argumentos_funcion = json.loads(llamada_herramienta["function"]["arguments"] or "{}")
                        except Exception:
                            argumentos_funcion = {}
                        
                        if nombre_funcion in available_tools:
                            try:
                                resultado_ejecucion = available_tools[nombre_funcion](**argumentos_funcion)
                            except Exception as tool_err:
                                print(f"[ERROR EN EJECUCIÓN DE TOOL {nombre_funcion}]: {repr(tool_err)}")
                                resultado_ejecucion = json.dumps({"error_ejecucion": str(tool_err)}, ensure_ascii=False)
                        else:
                            resultado_ejecucion = json.dumps({"error": "Herramienta no registrada en el núcleo operativo."}, ensure_ascii=False)
                            
                        mensajes_api.append({
                            "role": "tool",
                            "tool_call_id": llamada_herramienta["id"],
                            "content": resultado_ejecucion
                        })
                    
                    # Segunda iteración cognitiva para consolidar la respuesta operativa
                    payload_seguimiento = {
                        "model": "gpt-4o-mini",
                        "messages": mensajes_api,
                        "temperature": 0.1
                    }
                    respuesta_final = requests.post(url_api, json=payload_seguimiento, headers=cabeceras)
                    json_final = respuesta_final.json()
                    
                    if "choices" in json_final:
                        texto_respuesta = json_final["choices"][0]["message"].get("content", "Ejecución operativa completada con éxito.")
                    else:
                        texto_respuesta = f"Error en la consolidación operativa: {str(json_final)}"
                else:
                    texto_respuesta = mensaje_respuesta.get("content", "Directiva procesada.")

                historial_conversacion.append({"role": "user", "content": mensaje_usuario})
                historial_conversacion.append({"role": "assistant", "content": texto_respuesta})
                if len(historial_conversacion) > 12:
                    historial_conversacion = historial_conversacion[-12:]
                    
                return jsonify({"reply": texto_respuesta})
            else:
                return jsonify({"reply": f"Error en la respuesta del motor cognitivo: {str(respuesta_json)}"})
                
        except Exception as error_critico:
            print(f"[ERROR CRÍTICO CHAT GENERAL]: {repr(error_critico)}")
            return jsonify({"reply": f"Error crítico en el núcleo operativo: {str(error_critico)}"})
    else:
        return jsonify({"reply": "Falta configurar la clave OPENAI_API_KEY en el entorno del servidor."})

# =============================================================================
# SECCIÓN 8: PUNTO DE ENTRADA DEL SERVIDOR
# =============================================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
