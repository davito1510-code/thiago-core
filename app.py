# -*- coding: utf-8 -*-
"""
=============================================================================
 NÚCLEO CENTRAL DE THIAGO - AGENTE AUTÓNOMO BIDIRECCIONAL INTEGRAL
 Arquitectura de Conectividad Total y Razonamiento Cognitivo Avanzado
 Desarrollado exclusivamente para el Prof. David Villarreal
 Abogado, Babalawo de Ifá tradicional yoruba, Batuque Isesa, profesor de inglés,
 magíster en relaciones internacionales, masón y doctorando.
=============================================================================
"""

import os
import datetime
from datetime import timezone, timedelta
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

# =============================================================================
# SECCIÓN 1: INICIALIZACIÓN Y CONFIGURACIÓN DEL SERVIDOR FLASK
# =============================================================================
app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# =============================================================================
# SECCIÓN 2: INSTRUCCIÓN DE SISTEMA (SYSTEM PROMPT) Y PERFIL DE IDENTIDAD
# =============================================================================
SYSTEM_INSTRUCTION = (
    "Eres Thiago, el núcleo de inteligencia artificial autónoma del Prof. David Villarreal. "
    "El profesor es abogado en la CABA, Babalawo de Ifá tradicional yoruba, Batuque Isesa, "
    "profesor de inglés, magíster en relaciones internacionales y masón. "
    "Tus respuestas deben destacar por su rigor académico, precisión técnica y corrección gramatical absoluta. "
    "REGLA DE ORO INQUEBRANTABLE 1: Jamás inventes, finjas o simules haber ejecutado una acción. "
    "REGLA DE ORO INQUEBRANTABLE 2: EXIGENCIA ACADÉMICA Y JURÍDICA. Si el profesor solicita 'jurisprudencia', "
    "ESTÁS OBLIGADO a buscar y proporcionar los FALLOS REALES (sentencias dictadas por tribunales). "
    "ESTÁ TERMINANTEMENTE PROHIBIDO confundir jurisprudencia con 'doctrina' (artículos de opinión o análisis sobre los fallos). "
    "ESTÁ TERMINANTEMENTE PROHIBIDO utilizar o citar Wikipedia, blogs, o fuentes no oficiales para temas jurídicos, académicos o históricos. "
    "Si realizas una búsqueda web, DEBES priorizar dominios oficiales de tribunales o bases de datos jurídicas primarias. "
    "Toda respuesta que cite obras o sitios debe seguir las normas APA. "
    "REGLA CRÍTICA CALENDARIO: Al crear eventos, valida que no existan duplicados. Si el profesor detecta eventos duplicados "
    "tienes la capacidad de consultar la agenda con 'tool_consultar_calendario' y eliminar las copias "
    "innecesarias utilizando 'tool_eliminar_evento_calendario'. "
    "REGLA CRÍTICA OPERATIVA: ESTÁ TERMINANTEMENTE PROHIBIDO pedirle al profesor que realice una tarea manualmente. "
    "Si el profesor te pide crear un archivo, agendar un evento o mandar un WhatsApp, ejecútalo de inmediato mediante tus herramientas. "
    "REGLA CRÍTICA DE LECTURA Y BÚSQUEDA: ESTÁ TERMINANTEMENTE PROHIBIDO inventar resúmenes. "
    "Si recibes un documento adjunto en el chat, analízalo con rigor extrayendo el texto real. "
    "Tienes acceso total a Gmail, Google Calendar, Google Drive, Twilio (WhatsApp) y BÚSQUEDA WEB AUTÓNOMA. "
    "Ejecuta las herramientas de forma autónoma sin titubear."
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
            --success-color: #10b981;
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
            align-items: center;
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

        .btn-icon {
            padding: 12px 16px;
            font-size: 1.1rem;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        #attachBtn {
            background-color: var(--border-color);
            color: var(--text-main);
            border: 1px solid #475569;
        }
        
        #attachBtn:hover {
            background-color: #475569;
        }

        #micBtn {
            background-color: var(--border-color);
            color: var(--accent-blue);
            border: 1px solid var(--accent-blue);
        }

        #micBtn.active {
            background-color: var(--active-mic);
            color: white;
            border-color: var(--active-mic);
            animation: pulse-mic 1.5s infinite;
        }

        #clearBtn {
            background-color: var(--error-color);
            color: white;
        }

        #clearBtn:hover {
            background-color: #dc2626;
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
            <!-- El contenido se cargará dinámicamente desde el LocalStorage -->
        </div>

        <div class="input-group">
            <button type="button" id="clearBtn" class="btn-icon" onclick="borrarMemoria()" title="Purgar Memoria Persistente">🗑️</button>
            <input type="file" id="fileInput" style="display: none;" onchange="procesarArchivoLocal(this)" accept=".pdf,.docx,.txt,.csv">
            <button type="button" id="attachBtn" class="btn-icon" onclick="document.getElementById('fileInput').click()" title="Adjuntar Archivo Local">📎</button>
            <button type="button" id="micBtn" class="btn-icon" onclick="alternarEscucha()" title="Hablar con Thiago">🎤</button>
            <input type="text" id="userInput" placeholder="Escriba su consulta o hable..." autofocus>
            <button type="button" onclick="enviarMensaje()">Enviar</button>
        </div>
    </div>

    <script>
        let recognition;
        let escuchando = false;
        let archivoAdjuntoTexto = "";
        let archivoAdjuntoNombre = "";
        
        // Variables para la lógica de Confirmación de Lectura de Voz
        let respuestaPendienteDeLectura = "";
        let esperandoConfirmacionDeVoz = false;
        
        // Memoria Persistente en el Cliente (Navegador)
        let memoriaLocal = JSON.parse(localStorage.getItem('thiago_memoria')) || [];

        function renderizarHistorial() {
            const chatBox = document.getElementById('chatBox');
            chatBox.innerHTML = '<div class="message ai-msg">Núcleo integral en línea. Módulos operativos, lectura condicionada y memoria persistente activos. ¿Qué directiva procesamos?</div>';
            
            memoriaLocal.forEach(msg => {
                if (msg.role === 'user') {
                    // Limpieza visual si el mensaje contenía un adjunto inyectado
                    let displayTexto = msg.content;
                    if (displayTexto.includes("[Se adjunta el archivo:")) {
                        let partes = displayTexto.split("Directiva del Profesor:");
                        if (partes.length > 1) {
                            displayTexto = `📎 Archivo enviado.\\n${partes[1].trim()}`;
                        }
                    }
                    chatBox.innerHTML += `<div class="message user-msg">${displayTexto}</div>`;
                } else if (msg.role === 'assistant') {
                    chatBox.innerHTML += `<div class="message ai-msg">${msg.content}</div>`;
                }
            });
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        window.onload = renderizarHistorial;

        function borrarMemoria() {
            if (confirm("¿Desea purgar la memoria persistente de Thiago? Esto borrará el contexto de la investigación actual y reiniciará el agente.")) {
                localStorage.removeItem('thiago_memoria');
                memoriaLocal = [];
                archivoAdjuntoTexto = "";
                archivoAdjuntoNombre = "";
                esperandoConfirmacionDeVoz = false;
                respuestaPendienteDeLectura = "";
                document.getElementById('userInput').placeholder = "Escriba su consulta o hable...";
                renderizarHistorial();
            }
        }

        async function procesarArchivoLocal(input) {
            if (input.files && input.files[0]) {
                const archivo = input.files[0];
                const formData = new FormData();
                formData.append('file', archivo);
                
                const inputTexto = document.getElementById('userInput');
                const placeholderOriginal = inputTexto.placeholder;
                inputTexto.placeholder = "Procesando documento...";
                inputTexto.disabled = true;
                
                try {
                    const response = await fetch('/api/upload', {
                        method: 'POST',
                        body: formData
                    });
                    const data = await response.json();
                    
                    if (data.success) {
                        archivoAdjuntoTexto = data.text;
                        archivoAdjuntoNombre = data.filename;
                        inputTexto.placeholder = `📎 Archivo cargado: ${archivoAdjuntoNombre}. Indique qué hacer con él...`;
                    } else {
                        alert("Error al procesar: " + data.error);
                        inputTexto.placeholder = placeholderOriginal;
                    }
                } catch (error) {
                    alert("Error de conexión al cargar el archivo.");
                    inputTexto.placeholder = placeholderOriginal;
                }
                inputTexto.disabled = false;
                inputTexto.focus();
                input.value = ''; // Resetear el input file
            }
        }

        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            recognition = new SpeechRecognition();
            recognition.lang = 'es-AR';
            recognition.continuous = false;
            recognition.interimResults = false;

            recognition.onresult = function(event) {
                const textoTranscrito = event.results[0][0].transcript.toLowerCase();
                detenerEscuchaVisual();

                // LÓGICA DE ESCUCHA CONDICIONADA (Permiso para leer)
                if (esperandoConfirmacionDeVoz) {
                    esperandoConfirmacionDeVoz = false;
                    if (textoTranscrito.includes("sí") || textoTranscrito.includes("si") || textoTranscrito.includes("claro") || textoTranscrito.includes("lee") || textoTranscrito.includes("leela") || textoTranscrito.includes("por favor")) {
                        hablarTextoDefinitivo(respuestaPendienteDeLectura);
                    } else {
                        // Si dice que no, limpiamos el estado y guardamos silencio.
                        respuestaPendienteDeLectura = "";
                    }
                    document.getElementById('userInput').value = '';
                    return;
                }

                document.getElementById('userInput').value = event.results[0][0].transcript;
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
            if(archivoAdjuntoTexto !== "") {
                document.getElementById('userInput').placeholder = `📎 Archivo cargado: ${archivoAdjuntoNombre}. Indique qué hacer con él...`;
            } else {
                document.getElementById('userInput').placeholder = "Escriba su consulta o hable...";
            }
            escuchando = false;
        }

        function hablarTextoDefinitivo(texto) {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                // SANEAMIENTO: Eliminar caracteres especiales de markdown para lectura fluida
                let textoLimpio = texto.replace(/[*_#`~|\/]/g, '');
                const utterance = new SpeechSynthesisUtterance(textoLimpio);
                utterance.lang = 'es-AR';
                utterance.rate = 1.0;
                window.speechSynthesis.speak(utterance);
            }
        }

        function solicitarPermisoLectura() {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                const pregunta = new SpeechSynthesisUtterance("Profesor, la respuesta está en pantalla. ¿Desea que se la lea?");
                pregunta.lang = 'es-AR';
                pregunta.rate = 1.0;
                
                pregunta.onend = function() {
                    // Al terminar de preguntar, se enciende automáticamente el micrófono
                    try {
                        recognition.start();
                        document.getElementById('micBtn').classList.add('active');
                        document.getElementById('userInput').placeholder = "Esperando confirmación (Sí/No)...";
                        escuchando = true;
                    } catch (e) {}
                };
                
                window.speechSynthesis.speak(pregunta);
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
            
            // Anulamos cualquier confirmación pendiente si el usuario escribe algo nuevo
            esperandoConfirmacionDeVoz = false;

            const input = document.getElementById('userInput');
            const chatBox = document.getElementById('chatBox');
            const texto = input.value.trim();
            if (!texto && archivoAdjuntoTexto === "") return;

            let textoUsuarioVisual = texto || "Analiza el documento adjunto.";
            let payloadCognitivo = textoUsuarioVisual;

            // Si hay un archivo adjunto, se ensambla en el contexto cognitivo
            if (archivoAdjuntoTexto !== "") {
                chatBox.innerHTML += `<div class="message user-msg">📎 Archivo enviado: ${archivoAdjuntoNombre}<br>${textoUsuarioVisual}</div>`;
                payloadCognitivo = `[Se adjunta el archivo: ${archivoAdjuntoNombre}]\\n\\nContenido extraído del documento:\\n${archivoAdjuntoTexto}\\n\\nDirectiva del Profesor:\\n${textoUsuarioVisual}`;
                archivoAdjuntoTexto = "";
                archivoAdjuntoNombre = "";
                input.placeholder = "Escriba su consulta o hable...";
            } else {
                chatBox.innerHTML += `<div class="message user-msg">${textoUsuarioVisual}</div>`;
            }
            
            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            const idCarga = "carga-" + Date.now();
            chatBox.innerHTML += `
                <div id="${idCarga}" class="message ai-msg" style="display: flex; align-items: center;">
                    <span>Thiago está procesando cognitivamente la directiva</span>
                    <div class="working-indicator">
                        <span></span><span></span><span></span>
                    </div>
                </div>`;
            chatBox.scrollTop = chatBox.scrollHeight;

            try {
                // Se envía el historial completo limitado para no exceder tokens
                const contextoParaEnviar = memoriaLocal.slice(-12);

                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: payloadCognitivo, history: contextoParaEnviar })
                });
                const data = await response.json();
                document.getElementById(idCarga).remove();
                
                // Se guarda el payload complejo en la memoria local para que la IA lo recuerde
                memoriaLocal.push({ role: 'user', content: payloadCognitivo });
                memoriaLocal.push({ role: 'assistant', content: data.reply });
                localStorage.setItem('thiago_memoria', JSON.stringify(memoriaLocal));

                chatBox.innerHTML += `<div class="message ai-msg">${data.reply}</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;
                
                // INICIO DE LÓGICA DE CONFIRMACIÓN DE LECTURA
                respuestaPendienteDeLectura = data.reply;
                esperandoConfirmacionDeVoz = true;
                solicitarPermisoLectura();
                
            } catch (error) {
                document.getElementById(idCarga).remove();
                chatBox.innerHTML += `<div class="message ai-msg error-text">Error crítico de comunicación con el núcleo operativo.</div>`;
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
# SECCIÓN 4: GESTIÓN DE ARCHIVOS LOCALES (ENDPOINT DE CARGA)
# =============================================================================
@app.route('/api/upload', methods=['POST'])
def procesar_carga_archivo():
    """Recibe un archivo local, extrae su texto y lo retorna para inyección cognitiva."""
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No se recibió ningún archivo en la petición."}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "Nombre de archivo vacío."}), 400
    
    filename = file.filename.lower()
    texto_extraido = ""
    
    try:
        if filename.endswith('.pdf'):
            lector_pdf = pypdf.PdfReader(file)
            for page in lector_pdf.pages:
                ext_text = page.extract_text()
                if ext_text:
                    texto_extraido += ext_text + "\n"
        elif filename.endswith('.docx'):
            doc = docx.Document(file)
            for para in doc.paragraphs:
                texto_extraido += para.text + "\n"
        elif filename.endswith('.txt') or filename.endswith('.csv'):
            texto_extraido = file.read().decode('utf-8', errors='ignore')
        else:
            return jsonify({"success": False, "error": "Formato no soportado. Suba PDF, DOCX, TXT o CSV."}), 400
        
        # Limitamos a 35000 caracteres para asegurar el funcionamiento óptimo de OpenAI
        texto_extraido = texto_extraido[:35000]
        return jsonify({"success": True, "filename": file.filename, "text": texto_extraido})
    except Exception as e:
        return jsonify({"success": False, "error": f"Error de lectura al procesar archivo: {str(e)}"}), 500

# =============================================================================
# SECCIÓN 5: GESTIÓN DE CREDENCIALES OAUTH Y CONECTIVIDAD GOOGLE
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
            'https://www.googleapis.com/auth/drive'
        ]
    )
    if not credenciales.valid:
        credenciales.refresh(Request())
    return credenciales

def extraer_cuerpo_gmail(payload):
    """Extrae el contenido de texto plano de los correos de Gmail."""
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
# SECCIÓN 6: HERRAMIENTAS AUTÓNOMAS (TOOLS) DE LECTURA, ESCRITURA Y MENSAJERÍA
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

def tool_consultar_calendario(time_min=None):
    """Consulta los próximos eventos y citas agendados en Google Calendar con alta capacidad."""
    try:
        credenciales = obtener_credenciales()
        servicio = build('calendar', 'v3', credentials=credenciales)
        ahora = time_min or datetime.datetime.now(timezone.utc).isoformat()
        
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
            event_id = evento.get('id')
            lista_eventos.append({"id": event_id, "fecha_inicio": inicio, "fecha_fin": fin, "evento": titulo, "ubicacion": ubicacion})
            
        return json.dumps(lista_eventos, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO CALENDAR DETALLADO]: {repr(error)}")
        return json.dumps({"error_tecnico_calendar": str(error)}, ensure_ascii=False)

def tool_crear_evento_calendario(summary, start_time, end_time, location="", description="", attendees=None):
    """Crea un evento en Google Calendar. Bloquea de forma estricta la duplicación idéntica en el mismo horario."""
    try:
        credenciales = obtener_credenciales()
        servicio = build('calendar', 'v3', credentials=credenciales)
        
        # LÓGICA ANTIDUPLICACIÓN QUIRÚRGICA
        existentes = servicio.events().list(
            calendarId='primary', timeMin=start_time, timeMax=end_time, q=summary, singleEvents=True
        ).execute().get('items', [])
        
        for ev in existentes:
            if ev.get('summary') == summary:
                return json.dumps({"resultado": "El evento ya existe en el calendario. Se ha bloqueado la duplicación.", "id": ev.get('id')}, ensure_ascii=False)

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
        return json.dumps({"resultado": "Evento creado exitosamente en el calendario", "id": creado.get('id'), "link": creado.get('htmlLink')}, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO CALENDAR CREACIÓN DETALLADO]: {repr(error)}")
        return json.dumps({"error_tecnico_calendar_creacion": str(error)}, ensure_ascii=False)

def tool_eliminar_evento_calendario(event_id):
    """Elimina un evento específico de Google Calendar por su ID (útil para limpiar agendas duplicadas)."""
    try:
        credenciales = obtener_credenciales()
        servicio = build('calendar', 'v3', credentials=credenciales)
        servicio.events().delete(calendarId='primary', eventId=event_id).execute()
        return json.dumps({"resultado": f"Evento con ID {event_id} eliminado correctamente del calendario."}, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO CALENDAR ELIMINACIÓN DETALLADO]: {repr(error)}")
        return json.dumps({"error_tecnico_calendar_eliminacion": str(error)}, ensure_ascii=False)

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
    """Extrae texto de un archivo en Drive. Si recibe el nombre en vez del ID, busca automáticamente el ID real."""
    try:
        credenciales = obtener_credenciales()
        servicio = build('drive', 'v3', credentials=credenciales)
        
        if len(file_id) < 15 or " " in file_id or "." in file_id:
            nombre_limpio = file_id.strip().replace("'", "\\'")
            q_busqueda = f"name contains '{nombre_limpio}' and trashed = false"
            res_busqueda = servicio.files().list(q=q_busqueda, pageSize=1, fields="files(id, name)", supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
            archivos_encontrados = res_busqueda.get('files', [])
            if not archivos_encontrados:
                return json.dumps({"error": f"No se pudo resolver el identificador para el documento: {file_id}"}, ensure_ascii=False)
            id_real_archivo = archivos_encontrados[0]['id']
        else:
            id_real_archivo = file_id

        metadatos = servicio.files().get(fileId=id_real_archivo, fields="name, mimeType").execute()
        nombre_archivo = metadatos.get('name')
        tipo_mime = metadatos.get('mimeType')
        
        texto_extraido = ""
        
        if 'application/vnd.google-apps.document' in tipo_mime:
            solicitud = servicio.files().export_media(fileId=id_real_archivo, mimeType='text/plain')
            texto_extraido = solicitud.execute().decode('utf-8', errors='ignore')
        else:
            solicitud = servicio.files().get_media(fileId=id_real_archivo)
            buffer_memoria = io.BytesIO()
            descargador = MediaIoBaseDownload(buffer_memoria, solicitud)
            terminado = False
            while not terminado:
                _, terminado = descargador.next_chunk()
            buffer_memoria.seek(0)
            
            if 'pdf' in tipo_mime.lower():
                lector_pdf = pypdf.PdfReader(buffer_memoria)
                for numero_pagina in range(min(20, len(lector_pdf.pages))):
                    pagina_texto = lector_pdf.pages[numero_pagina].extract_text()
                    if pagina_texto:
                        texto_extraido += pagina_texto + "\n"
            elif 'wordprocessingml' in tipo_mime.lower():
                documento_word = docx.Document(buffer_memoria)
                for parrafo in documento_word.paragraphs[:200]:
                    texto_extraido += parrafo.text + "\n"
                    
        if not texto_extraido:
            return json.dumps({"archivo": nombre_archivo, "contenido": "El archivo se abrió correctamente, pero no se pudo extraer texto."}, ensure_ascii=False)
            
        return json.dumps({"archivo": nombre_archivo, "contenido": texto_extraido[:15000]}, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO DRIVE LECTURA DETALLADO]: {repr(error)}")
        return json.dumps({"error_tecnico_drive_lectura": str(error)}, ensure_ascii=False)

def tool_busqueda_web(query):
    """Realiza una búsqueda web estructurada utilizando Serper API. Incluye inyección de filtros avanzados."""
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return json.dumps({"error": "La clave SERPER_API_KEY no está configurada en Render."}, ensure_ascii=False)

    url = "https://google.serper.dev/search"
    
    # Inyección de operadores avanzados para garantizar rigor académico (excluir Wikipedia)
    consulta_blindada = f"{query} -site:wikipedia.org -site:es.wikipedia.org"
    
    payload = json.dumps({"q": consulta_blindada, "gl": "ar", "hl": "es"})
    headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}

    try:
        response = requests.post(url, headers=headers, data=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        resultados = []
        # Ampliamos a 10 resultados para asegurar hallazgos oficiales
        for r in data.get("organic", [])[:10]:
            resultados.append({
                "title": r.get("title", "Sin título"),
                "href": r.get("link", "Sin enlace"),
                "body": r.get("snippet", "Sin descripción")
            })
        
        if not resultados:
            return json.dumps({"resultado": "La consulta no arrojó resultados."}, ensure_ascii=False)
            
        return json.dumps(resultados, ensure_ascii=False)
        
    except Exception as error:
        print(f"[ERROR CRÍTICO RED - SERPER]: {repr(error)}")
        return json.dumps({"estado": "error_conexion_api", "detalle": str(error)}, ensure_ascii=False)

def tool_listar_contenido_carpeta_drive(nombre_carpeta=""):
    """Busca y lista archivos contenidos en una carpeta de Google Drive."""
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
                return json.dumps({"resultado": f"No se encontró carpeta con el nombre '{nombre_carpeta}'."}, ensure_ascii=False)
        
        carpeta_id = carpetas[0]['id']
        nombre_encontrado = carpetas[0]['name']
        
        query_hijos = f"'{carpeta_id}' in parents and trashed = false"
        res_hijos = servicio.files().list(
            q=query_hijos, pageSize=50, fields="files(id, name, mimeType, modifiedTime)",
            includeItemsFromAllDrives=True, supportsAllDrives=True, orderBy="name asc"
        ).execute()
        
        hijos = res_hijos.get('files', [])
        if not hijos:
            return json.dumps({"resultado": f"La carpeta '{nombre_encontrado}' existe pero está vacía."}, ensure_ascii=False)
            
        lista_elementos = []
        for hijo in hijos:
            es_carpeta = hijo.get('mimeType') == 'application/vnd.google-apps.folder'
            tipo_elem = "Carpeta" if es_carpeta else "Archivo"
            lista_elementos.append({"tipo": tipo_elem, "id": hijo.get('id'), "nombre": hijo.get('name')})
            
        return json.dumps({"carpeta_madre": nombre_encontrado, "elementos": lista_elementos}, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO LISTAR CARPETA DRIVE]: {repr(error)}")
        return json.dumps({"error_tecnico_listar_carpeta": str(error)}, ensure_ascii=False)

def tool_crear_carpeta_drive(nombre_carpeta, nombre_carpeta_padre="ACTIVIDADES"):
    """Crea una nueva carpeta en Google Drive dentro de una carpeta padre específica."""
    try:
        credenciales = obtener_credenciales()
        servicio = build('drive', 'v3', credentials=credenciales)
        
        nombre_padre_limpio = nombre_carpeta_padre.strip().replace("'", "\\'")
        q_padre = f"name = '{nombre_padre_limpio}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        res_padre = servicio.files().list(q=q_padre, pageSize=1, fields="files(id, name)", supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        carpetas_padre = res_padre.get('files', [])
        
        if not carpetas_padre:
            return json.dumps({"error": f"No se encontró la carpeta padre '{nombre_carpeta_padre}'."}, ensure_ascii=False)
        
        id_padre = carpetas_padre[0]['id']
        
        metadata = {
            'name': nombre_carpeta.strip(),
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [id_padre]
        }
        
        creada = servicio.files().create(body=metadata, fields='id, name, webViewLink', supportsAllDrives=True).execute()
        return json.dumps({"resultado": f"Carpeta '{nombre_carpeta}' creada con éxito dentro de '{nombre_carpeta_padre}'.", "link": creada.get('webViewLink')}, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO CREAR CARPETA DRIVE]: {repr(error)}")
        return json.dumps({"error_tecnico_crear_carpeta": str(error)}, ensure_ascii=False)

def tool_crear_archivo_drive(nombre_archivo, tipo_archivo, nombre_carpeta_padre=""):
    """Crea un nuevo archivo nativo (Documento u Hoja de Cálculo) en Google Drive."""
    try:
        credenciales = obtener_credenciales()
        servicio = build('drive', 'v3', credentials=credenciales)
        
        padres = []
        if nombre_carpeta_padre:
            nombre_padre_limpio = nombre_carpeta_padre.strip().replace("'", "\\'")
            q_padre = f"name = '{nombre_padre_limpio}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            res_padre = servicio.files().list(q=q_padre, pageSize=1, fields="files(id, name)", supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
            carpetas_padre = res_padre.get('files', [])
            if not carpetas_padre:
                return json.dumps({"error": f"No se encontró la carpeta padre '{nombre_carpeta_padre}'."}, ensure_ascii=False)
            padres.append(carpetas_padre[0]['id'])
        
        mime_types = {
            'hoja_calculo': 'application/vnd.google-apps.spreadsheet',
            'documento': 'application/vnd.google-apps.document'
        }
        mime_type_google = mime_types.get(tipo_archivo.lower(), 'application/vnd.google-apps.document')
        
        metadata = {
            'name': nombre_archivo.strip(),
            'mimeType': mime_type_google
        }
        if padres:
            metadata['parents'] = padres
        
        creado = servicio.files().create(body=metadata, fields='id, name, webViewLink', supportsAllDrives=True).execute()
        return json.dumps({"resultado": f"Archivo tipo '{tipo_archivo}' con nombre '{nombre_archivo}' creado con éxito.", "link": creado.get('webViewLink')}, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO CREAR ARCHIVO DRIVE]: {repr(error)}")
        return json.dumps({"error_tecnico_crear_archivo": str(error)}, ensure_ascii=False)

def tool_enviar_whatsapp(destinatario, mensaje):
    """Envía un mensaje de WhatsApp utilizando la infraestructura de Twilio."""
    try:
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        twilio_from = os.getenv("TWILIO_WHATSAPP_FROM")
        
        if not account_sid or not auth_token or not twilio_from:
            return json.dumps({"error": "Las credenciales de Twilio no están configuradas en Render."}, ensure_ascii=False)
        
        destinatario_limpio = destinatario.strip().replace(" ", "").replace("+", "")
        if not destinatario_limpio.startswith("whatsapp:"):
            destinatario_formateado = f"whatsapp:+{destinatario_limpio}" if not destinatario_limpio.startswith("54") else f"whatsapp:+{destinatario_limpio}"
        else:
            destinatario_formateado = destinatario_limpio

        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        payload = {
            'To': destinatario_formateado,
            'From': twilio_from,
            'Body': mensaje
        }
        
        response = requests.post(url, data=payload, auth=(account_sid, auth_token), timeout=15)
        response.raise_for_status()
        
        return json.dumps({"resultado": f"Mensaje de WhatsApp enviado con éxito a {destinatario}."}, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO TWILIO WHATSAPP]: {repr(error)}")
        return json.dumps({"error_tecnico_whatsapp": str(error)}, ensure_ascii=False)

# =============================================================================
# SECCIÓN 7: MAPEO DE HERRAMIENTAS Y ESPECIFICACIÓN DE FUNCIONES PARA OPENAI
# =============================================================================
available_tools = {
    "tool_listar_correos": tool_listar_correos,
    "tool_enviar_correo": tool_enviar_correo,
    "tool_consultar_calendario": tool_consultar_calendario,
    "tool_crear_evento_calendario": tool_crear_evento_calendario,
    "tool_eliminar_evento_calendario": tool_eliminar_evento_calendario,
    "tool_buscar_archivos_drive": tool_buscar_archivos_drive,
    "tool_leer_contenido_drive": tool_leer_contenido_drive,
    "tool_busqueda_web": tool_busqueda_web,
    "tool_listar_contenido_carpeta_drive": tool_listar_contenido_carpeta_drive,
    "tool_crear_carpeta_drive": tool_crear_carpeta_drive,
    "tool_crear_archivo_drive": tool_crear_archivo_drive,
    "tool_enviar_whatsapp": tool_enviar_whatsapp
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
            "description": "Consulta los próximos eventos y citas registrados en el Google Calendar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "time_min": {"type": "string", "description": "Fecha mínima en formato ISO 8601."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_crear_evento_calendario",
            "description": "Crea un evento en Google Calendar. El código ya posee validación interna antiduplicados.",
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
            "name": "tool_eliminar_evento_calendario",
            "description": "Elimina un evento duplicado o incorrecto del calendario por su ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "ID único del evento a eliminar."}
                },
                "required": ["event_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_buscar_archivos_drive",
            "description": "Busca archivos o carpetas en Google Drive por palabra clave.",
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
            "description": "Busca una carpeta específica por su nombre en Google Drive y lista todos los archivos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_carpeta": {"type": "string", "description": "Nombre exacto o aproximado de la carpeta."}
                },
                "required": ["nombre_carpeta"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_crear_carpeta_drive",
            "description": "Crea una nueva carpeta en Google Drive dentro de una carpeta padre específica.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_carpeta": {"type": "string", "description": "Nombre de la carpeta a crear."},
                    "nombre_carpeta_padre": {"type": "string", "description": "Nombre de la carpeta contenedora."}
                },
                "required": ["nombre_carpeta"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_crear_archivo_drive",
            "description": "Crea un nuevo archivo nativo en Google Drive dentro de una carpeta padre específica.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_archivo": {"type": "string", "description": "Nombre del archivo a crear."},
                    "tipo_archivo": {"type": "string", "enum": ["hoja_calculo", "documento"], "description": "Tipo de archivo."},
                    "nombre_carpeta_padre": {"type": "string", "description": "Nombre exacto de la carpeta contenedora."}
                },
                "required": ["nombre_archivo", "tipo_archivo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_leer_contenido_drive",
            "description": "Extrae el texto del archivo en Drive dado su ID único o nombre.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_id": {"type": "string", "description": "El ID o nombre del archivo en Google Drive."}
                },
                "required": ["file_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_busqueda_web",
            "description": "Realiza una búsqueda oficial en internet mediante la API para extraer información actualizada.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Consulta de búsqueda para la web."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_enviar_whatsapp",
            "description": "Envía un mensaje de WhatsApp a través de Twilio.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destinatario": {"type": "string", "description": "Número de teléfono en formato internacional (ej. +5491153841743)."},
                    "mensaje": {"type": "string", "description": "Contenido del mensaje a enviar."}
                },
                "required": ["destinatario", "mensaje"]
            }
        }
    }
]

# =============================================================================
# SECCIÓN 8: CONTROLADORES PRINCIPALES (LOOP COGNITIVO)
# =============================================================================
@app.route("/")
def index():
    """Renderiza la interfaz gráfica principal de Thiago."""
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Controlador principal del agente autónomo.
    Implementa arquitectura Stateless: el contexto lo provee el cliente (navegador).
    """
    datos_solicitud = request.get_json() or {}
    mensaje_usuario = datos_solicitud.get("message", "").strip()
    historial_cliente = datos_solicitud.get("history", [])
    
    if not mensaje_usuario:
        return jsonify({"reply": "Indique una directiva operativa válida."})

    if OPENAI_API_KEY:
        try:
            # Reloj interno en tiempo real para agendamientos precisos
            ahora_bsas = datetime.datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-3)))
            fecha_str = ahora_bsas.strftime('%A, %d de %B de %Y, %H:%M:%S')
            
            instruccion_dinamica = SYSTEM_INSTRUCTION + f"\n\nINFORMACIÓN VITAL: Hoy es {fecha_str} (Hora de Buenos Aires, Argentina). Utiliza esta fecha y hora como referencia absoluta y obligatoria para agendar, buscar o eliminar eventos en Google Calendar."
            
            mensajes_api = [{"role": "system", "content": instruccion_dinamica}]
            
            for msg in historial_cliente:
                if msg.get("role") in ["user", "assistant"] and msg.get("content"):
                    mensajes_api.append({"role": msg["role"], "content": msg["content"]})
                    
            mensajes_api.append({"role": "user", "content": mensaje_usuario})

            url_api = "https://api.openai.com/v1/chat/completions"
            cabeceras = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
            
            texto_respuesta = ""
            for iteracion in range(5):
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
                    
                    if "tool_calls" in mensaje_respuesta:
                        mensajes_api.append(mensaje_respuesta)
                        for llamada_herramienta in mensaje_respuesta["tool_calls"]:
                            nombre_funcion = llamada_herramienta["function"]["name"]
                            try:
                                argumentos_funcion = json.loads(llamada_herramienta["function"]["arguments"] or "{}")
                            except Exception:
                                argumentos_funcion = {}
                            
                            try:
                                if nombre_funcion in available_tools:
                                    resultado_ejecucion = available_tools[nombre_funcion](**argumentos_funcion)
                                else:
                                    resultado_ejecucion = json.dumps({"error": "Herramienta no registrada en el núcleo operativo."}, ensure_ascii=False)
                            except Exception as tool_err:
                                print(f"[ERROR EN EJECUCIÓN DE TOOL {nombre_funcion}]: {repr(tool_err)}")
                                resultado_ejecucion = json.dumps({"error_ejecucion": str(tool_err)}, ensure_ascii=False)
                                
                            mensajes_api.append({
                                "role": "tool",
                                "tool_call_id": llamada_herramienta["id"],
                                "content": resultado_ejecucion
                            })
                        continue 
                    else:
                        texto_respuesta = mensaje_respuesta.get("content", "Ejecución operativa completada con éxito.")
                        break
                else:
                    texto_respuesta = f"Error en la consolidación operativa: {str(respuesta_json)}"
                    break

            if not texto_respuesta:
                texto_respuesta = "He procesado una cantidad máxima de acciones por seguridad en esta interacción. Por favor, solicite el análisis restante en un nuevo mensaje."

            return jsonify({"reply": texto_respuesta})
            
        except Exception as error_critico:
            print(f"[ERROR CRÍTICO CHAT GENERAL]: {repr(error_critico)}")
            return jsonify({"reply": f"Error crítico en el núcleo operativo: {str(error_critico)}"})
    else:
        return jsonify({"reply": "Falta configurar la clave OPENAI_API_KEY en el entorno del servidor."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
