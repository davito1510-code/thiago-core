# -*- coding: utf-8 -*-
"""
Núcleo Central de Thiago - Agente Autónomo Integrado (Versión Exhaustiva e Íntegra)
Profesor David Villarreal — Arquitectura de Conectividad Total (Gmail, Calendar y Drive)
Desarrollado bajo estrictas normas de auditoría de código y transparencia técnica.
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

# ==========================================
# INICIALIZACIÓN DE LA APLICACIÓN WEB FLASK
# ==========================================
app = Flask(__name__)

# Recuperación de la clave secreta de la API de OpenAI desde el entorno del servidor
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Memoria de sesión temporal para almacenar el historial de la conversación del agente
historial_conversacion = []

# ==========================================
# INSTRUCCIÓN DE SISTEMA (SYSTEM PROMPT)
# ==========================================
SYSTEM_INSTRUCTION = (
    "Eres Thiago, el núcleo de inteligencia artificial autónoma del Prof. David Villarreal. "
    "El profesor es abogado en la CABA, Babalawo de Ifa tradicional yoruba, Batuque Isesa, "
    "profesor de inglés, magíster en relaciones internacionales y masón. "
    "Tus respuestas deben destacar por su rigor académico, precisión técnica y corrección gramatical absoluta. "
    "REGLA DE ORO INQUEBRANTABLE: Jamás inventes, finjas o simules haber encontrado un archivo o correo si la herramienta devuelve un resultado vacío. "
    "Tienes acceso total y autorizado a Gmail (cuerpo íntegro de correos), Google Calendar (agenda y eventos) "
    "y Google Drive (búsqueda global en carpetas, ordenadores sincronizados y lectura analítica de textos). "
    "Utiliza tus herramientas de manera autónoma cuando el profesor lo ordene para ejecutar tareas complejas."
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
    <title>Núcleo Central de Thiago - Agente Autónomo</title>
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
        
        /* Estilos detallados para la señal visual de trabajo (puntos pulsantes animados en tiempo real) */
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
        <div class="subtitle">Prof. David Villarreal — Agente Autónomo con Conectividad Total</div>
        
        <div class="chat-box" id="chatBox">
            <div class="message ai-msg">Núcleo integral en línea. Módulos de Gmail, Calendar y Drive operativos con señal visual de actividad. ¿Qué directiva procesamos?</div>
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

            // Inyección explícita del indicador visual dinámico de trabajo en tiempo real
            const idCarga = "carga-" + Date.now();
            chatBox.innerHTML += `
                <div id="${idCarga}" class="message ai-msg" style="display: flex; align-items: center;">
                    <span>Thiago está consultando las herramientas de Google Workspace</span>
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
# FUNCIONES DE AUTENTICACIÓN Y CONECTIVIDAD GOOGLE
# ==========================================
def obtener_credenciales():
    """Obtiene y refresca las credenciales OAuth de Google de manera explícita y segura."""
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
    """Extrae de forma recursiva y limpia el cuerpo de texto plano de un mensaje de correo electrónico."""
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
# HERRAMIENTAS AUTÓNOMAS (TOOLS)
# ==========================================
def tool_listar_correos():
    """Consulta los últimos correos electrónicos en Gmail y extrae su contenido íntegro."""
    try:
        credenciales = obtener_credenciales()
        if not credenciales.valid:
            credenciales.refresh(Request())
        servicio = build('gmail', 'v1', credentials=credenciales)
        resultados = servicio.users().messages().list(userId='me', maxResults=3).execute()
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
            cuerpo = extraer_cuerpo_gmail(payload)
            lista_correos.append({
                "remitente": remitente,
                "asunto": asunto,
                "cuerpo_completo": cuerpo
            })
        return json.dumps(lista_correos, ensure_ascii=False)
    except Exception as error:
        return json.dumps({"error": str(error)}, ensure_ascii=False)

def tool_consultar_calendario():
    """Consulta los próximos eventos y citas registrados en Google Calendar."""
    try:
        credenciales = obtener_credenciales()
        if not credenciales.valid:
            credenciales.refresh(Request())
        servicio = build('calendar', 'v3', credentials=credenciales)
        ahora = datetime.datetime.utcnow().isoformat() + 'Z'
        respuesta_eventos = servicio.events().list(
            calendarId='primary',
            timeMin=ahora,
            maxResults=5,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        eventos = respuesta_eventos.get('items', [])
        if not eventos:
            return json.dumps({"resultado": "No hay eventos próximos registrados en la agenda."}, ensure_ascii=False)
        
        lista_eventos = []
        for evento in eventos:
            inicio = evento['start'].get('dateTime', evento['start'].get('date'))
            titulo = evento.get('summary', 'Sin título')
            lista_eventos.append({"fecha_inicio": inicio, "evento": titulo})
            
        return json.dumps(lista_eventos, ensure_ascii=False)
    except Exception as error:
        return json.dumps({"error": str(error)}, ensure_ascii=False)

def tool_buscar_archivos_drive(query=""):
    """Realiza una búsqueda global e inteligente en Google Drive (incluyendo ordenadores sincronizados)."""
    try:
        credenciales = obtener_credenciales()
        if not credenciales.valid:
            credenciales.refresh(Request())
        servicio = build('drive', 'v3', credentials=credenciales)
        
        consulta_limpia = query.strip()
        condicion = f"name contains '{consulta_limpia}' and trashed = false" if consulta_limpia else "trashed = false"
        
        resultados = servicio.files().list(
            q=condicion,
            pageSize=25,
            fields="files(id, name, mimeType, parents)",
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            orderBy="modifiedTime desc"
        ).execute()
        
        elementos = resultados.get('files', [])
        if not elementos:
            return json.dumps({"resultado": f"No se encontró ningún archivo o carpeta con el término '{consulta_limpia}' en Google Drive."}, ensure_ascii=False)
        return json.dumps(elementos, ensure_ascii=False)
    except Exception as error:
        return json.dumps({"error": str(error)}, ensure_ascii=False)

def tool_leer_contenido_drive(file_id):
    """Extrae el texto interno de un archivo específico de Drive (PDF, Word o Google Doc) dado su ID."""
    try:
        credenciales = obtener_credenciales()
        if not credenciales.valid:
            credenciales.refresh(Request())
        servicio = build('drive', 'v3', credentials=credenciales)
        
        metadatos = servicio.files().get(fileId=file_id, fields="name, mimeType").execute()
        nombre_archivo = metadatos.get('name')
        tipo_mime = metadatos.get('mimeType')
        
        limite_caracteres = 8000
        texto_extraido = ""
        
        if 'application/vnd.google-apps.document' in tipo_mime:
            solicitud = servicio.files().export_media(fileId=file_id, mimeType='text/plain')
            contenido_bytes = solicitud.execute()
            texto_extraido = contenido_bytes.decode('utf-8', errors='ignore')
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
                for numero_pagina in range(min(5, len(lector_pdf.pages))):
                    pagina_texto = lector_pdf.pages[numero_pagina].extract_text()
                    if pagina_texto:
                        texto_extraido += pagina_texto + "\n"
            elif 'wordprocessingml' in tipo_mime.lower():
                documento_word = docx.Document(buffer_memoria)
                for parrafo in documento_word.paragraphs[:50]:
                    texto_extraido += parrafo.text + "\n"
                    
        return json.dumps({"archivo": nombre_archivo, "contenido": texto_extraido[:limite_caracteres]}, ensure_ascii=False)
    except Exception as error:
        return json.dumps({"error": str(error)}, ensure_ascii=False)

# Mapeo formal de funciones disponibles para el agente
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
            "description": "Consulta los próximos eventos y citas registrados en Google Calendar."
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_buscar_archivos_drive",
            "description": "Busca directamente cualquier archivo o carpeta en Google Drive por nombre (ej. 'BIBLIOGRAFIA', 'COMPAÑERO' o 'MASONERIA').",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Término de búsqueda o palabra clave."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_leer_contenido_drive",
            "description": "Extrae el texto interno de un archivo específico de Drive (PDF, Word o Doc) dado su ID único.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_id": {"type": "string", "description": "El identificador único (ID) del archivo en Google Drive."}
                },
                "required": ["file_id"]
            }
        }
    }
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
    datos_solicitud = request.get_json() or {}
    mensaje_usuario = datos_solicitud.get("message", "").strip()
    if not mensaje_usuario:
        return jsonify({"reply": "Indique una directiva válida."})

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
                "temperature": 0.3
            }
            
            respuesta = requests.post(url_api, json=payload_inicial, headers=cabeceras)
            respuesta_json = respuesta.json()
            
            if "choices" in respuesta_json:
                mensaje_respuesta = respuesta_json["choices"][0]["message"]
                
                if "tool_calls" in mensaje_respuesta:
                    mensajes_api.append(mensaje_respuesta)
                    for llamada_herramienta in mensaje_respuesta["tool_calls"]:
                        nombre_funcion = llamada_herramienta["function"]["name"]
                        argumentos_funcion = json.loads(llamada_herramienta["function"]["arguments"] or "{}")
                        
                        if nombre_funcion in available_tools:
                            resultado_ejecucion = available_tools[nombre_funcion](**argumentos_funcion)
                        else:
                            resultado_ejecucion = json.dumps({"error": "Herramienta no registrada en el núcleo."}, ensure_ascii=False)
                            
                        mensajes_api.append({
                            "role": "tool",
                            "tool_call_id": llamada_herramienta["id"],
                            "content": resultado_ejecucion
                        })
                    
                    payload_seguimiento = {
                        "model": "gpt-4o-mini",
                        "messages": mensajes_api,
                        "temperature": 0.3
                    }
                    respuesta_final = requests.post(url_api, json=payload_seguimiento, headers=cabeceras)
                    json_final = respuesta_final.json()
                    texto_respuesta = json_final["choices"][0]["message"]["content"]
                else:
                    texto_respuesta = mensaje_respuesta.get("content", "Procesamiento de directiva completado.")

                historial_conversacion.append({"role": "user", "content": mensaje_usuario})
                historial_conversacion.append({"role": "assistant", "content": texto_respuesta})
                if len(historial_conversacion) > 10:
                    historial_conversacion = historial_conversacion[-10:]
                    
                return jsonify({"reply": texto_respuesta})
            else:
                return jsonify({"reply": f"Error en la respuesta de OpenAI: {str(respuesta_json)}"})
                
        except Exception as error_critico:
            return jsonify({"reply": f"Error crítico del agente autónomo: {str(error_critico)}"})
    else:
        return jsonify({"reply": "Falta configurar la clave OPENAI_API_KEY en el entorno."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
