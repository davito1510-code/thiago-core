# -*- coding: utf-8 -*-
"""
=============================================================================
 NÚCLEO CENTRAL DE THIAGO - AGENTE AUTÓNOMO BIDIRECCIONAL INTEGRAL
 Arquitectura de Conectividad Total, OCR Universal y Razonamiento Cognitivo
 Desarrollado exclusivamente para el Prof. David Villarreal
 Abogado, Babalawo de Ifá tradicional yoruba, Batuque Isesa, profesor de inglés,
 magíster en relaciones internacionales, masón y doctorando.
=============================================================================
"""

import os
import re
import io
import json
import base64
import zipfile
import datetime
from datetime import timezone, timedelta
import xml.etree.ElementTree as ET
import requests
from email.mime.text import MIMEText
from flask import Flask, render_template_string, request, jsonify
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
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
    "Eres Thiago, el núcleo de inteligencia artificial autónoma del Prof. David Villarreal "
    "(David Efraín Villarreal, identificado frecuentemente con las iniciales DEV). "
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
    "Cuando el profesor solicite buscar documentos personales suyos (como su CV o currículum), prioriza aquellos que "
    "contengan su nombre ('David Villarreal') o sus iniciales ('DEV', por ejemplo 'CV DEV.doc'), descartando currículums de terceros. "
    "Posees un motor universal de lectura y OCR capaz de extraer texto de cualquier formato (.pdf digitales o escaneados, .doc, .docx, "
    ".xls, .xlsx, .ppt, .pptx, .odt, .rtf, .txt, .csv e imágenes). "
    "Si recibes un documento adjunto en el chat o lees un archivo de Drive, analízalo con rigor extrayendo el texto real completo. "
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
            <input type="file" id="fileInput" style="display: none;" onchange="procesarArchivoLocal(this)" accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.odt,.rtf,.txt,.csv,.json,.md,.html,.jpg,.jpeg,.png,.webp">
            <button type="button" id="attachBtn" class="btn-icon" onclick="document.getElementById('fileInput').click()" title="Adjuntar Documento o Imagen en Cualquier Formato">📎</button>
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
            chatBox.innerHTML = '<div class="message ai-msg">Núcleo integral en línea. Módulos operativos, lectura universal multiformato (con OCR) y memoria persistente activos. ¿Qué directiva procesamos?</div>';
            
            memoriaLocal.forEach(msg => {
                if (msg.role === 'user') {
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
                inputTexto.placeholder = "Procesando documento (extracción / OCR en curso)...";
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
                input.value = '';
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

                if (esperandoConfirmacionDeVoz) {
                    esperandoConfirmacionDeVoz = false;
                    if (textoTranscrito.includes("sí") || textoTranscrito.includes("si") || textoTranscrito.includes("claro") || textoTranscrito.includes("lee") || textoTranscrito.includes("leela") || textoTranscrito.includes("por favor")) {
                        hablarTextoDefinitivo(respuestaPendienteDeLectura);
                    } else {
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
                let textoLimpio = texto.replace(/[*_#`~|\\/]/g, '');
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
            
            esperandoConfirmacionDeVoz = false;

            const input = document.getElementById('userInput');
            const chatBox = document.getElementById('chatBox');
            const texto = input.value.trim();
            if (!texto && archivoAdjuntoTexto === "") return;

            let textoUsuarioVisual = texto || "Analiza el documento adjunto.";
            let payloadCognitivo = textoUsuarioVisual;

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
                const contextoParaEnviar = memoriaLocal.slice(-12);

                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: payloadCognitivo, history: contextoParaEnviar })
                });
                const data = await response.json();
                document.getElementById(idCarga).remove();
                
                memoriaLocal.push({ role: 'user', content: payloadCognitivo });
                memoriaLocal.push({ role: 'assistant', content: data.reply });
                localStorage.setItem('thiago_memoria', JSON.stringify(memoriaLocal));

                chatBox.innerHTML += `<div class="message ai-msg">${data.reply}</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;
                
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
            'https://www.googleapis.com/auth/drive'
        ]
    )
    if not credenciales.valid:
        credenciales.refresh(Request())
    return credenciales

# =============================================================================
# SECCIÓN 5: MOTOR UNIVERSAL DE LECTURA DOCUMENTAL, CONVERSIÓN Y OCR
# =============================================================================
MARCAS_AGUA_ESCANER = [
    "anyscanner", "camscanner", "scanned with", "scanned by",
    "tapscanner", "adobe scan", "clear scanner", "fast scanner",
    "genius scan", "vflat", "microsoft lens", "office lens"
]

def es_texto_insuficiente_o_marca_agua(texto):
    """
    Detecta si el texto extraído de un documento está vacío o solo contiene
    marcas de agua residuales de aplicaciones de escaneo (como AnyScanner).
    """
    if not texto:
        return True
    texto_limpio = texto.lower()
    for marca in MARCAS_AGUA_ESCANER:
        texto_limpio = texto_limpio.replace(marca, "")
    solo_alfanumericos = re.sub(r'[^a-z0-9áéíóúñü]', '', texto_limpio)
    return len(solo_alfanumericos) < 40

def extraer_texto_docx_completo(buffer_bytes):
    """Extrae texto tanto de párrafos como de tablas e encabezados en archivos .docx."""
    partes = []
    try:
        documento = docx.Document(io.BytesIO(buffer_bytes))
        for p in documento.paragraphs:
            if p.text and p.text.strip():
                partes.append(p.text.strip())
        for tabla in documento.tables:
            for fila in tabla.rows:
                celdas_texto = []
                for celda in fila.cells:
                    txt_celda = " ".join(p.text.strip() for p in celda.paragraphs if p.text.strip())
                    if txt_celda and (not celdas_texto or txt_celda != celdas_texto[-1]):
                        celdas_texto.append(txt_celda)
                if celdas_texto:
                    partes.append(" | ".join(celdas_texto))
    except Exception as e:
        print(f"[AVISO EXTRACCIÓN DOCX]: {repr(e)}")
    return "\n".join(partes)

def extraer_texto_zip_xml(buffer_bytes, extension):
    """Extrae texto directamente del contenedor XML para formatos .xlsx, .pptx, .odt y .docx."""
    textos = []
    try:
        with zipfile.ZipFile(io.BytesIO(buffer_bytes)) as zf:
            nombres = zf.namelist()
            if extension == '.odt' and 'content.xml' in nombres:
                raiz = ET.fromstring(zf.read('content.xml'))
                textos.extend(t.strip() for t in raiz.itertext() if t.strip())
            elif extension == '.pptx':
                slides = sorted([n for n in nombres if n.startswith('ppt/slides/slide') and n.endswith('.xml')])
                for idx, slide_name in enumerate(slides, 1):
                    raiz = ET.fromstring(zf.read(slide_name))
                    txt_slide = " ".join(t.strip() for t in raiz.itertext() if t.strip())
                    if txt_slide:
                        textos.append(f"[Diapositiva {idx}]: {txt_slide}")
            elif extension == '.xlsx':
                shared_strings = []
                if 'xl/sharedStrings.xml' in nombres:
                    raiz_ss = ET.fromstring(zf.read('xl/sharedStrings.xml'))
                    for si in raiz_ss:
                         shared_strings.append("".join(t for t in si.itertext()))
                hojas = sorted([n for n in nombres if n.startswith('xl/worksheets/sheet') and n.endswith('.xml')])
                for idx, hoja in enumerate(hojas, 1):
                    raiz_h = ET.fromstring(zf.read(hoja))
                    filas_txt = []
                    for elem in raiz_h.iter():
                        if elem.tag.endswith('}row') or elem.tag == 'row':
                            valores_fila = []
                            for celda in elem:
                                tipo_c = celda.attrib.get('t', '')
                                val_c = ""
                                for sub in celda:
                                    if sub.tag.endswith('}v') or sub.tag == 'v':
                                        if tipo_c == 's' and sub.text and sub.text.isdigit():
                                            idx_s = int(sub.text)
                                            if 0 <= idx_s < len(shared_strings):
                                                val_c = shared_strings[idx_s]
                                        elif sub.text:
                                            val_c = sub.text
                                    elif sub.tag.endswith('}is') or sub.tag == 'is':
                                        val_c = "".join(t for t in sub.itertext())
                                if val_c:
                                    valores_fila.append(val_c.strip())
                            if valores_fila:
                                filas_txt.append(" | ".join(valores_fila))
                    if filas_txt:
                        textos.append(f"[Hoja {idx}]:\n" + "\n".join(filas_txt))
            elif extension == '.docx' and 'word/document.xml' in nombres:
                raiz = ET.fromstring(zf.read('word/document.xml'))
                textos.extend(t.strip() for t in raiz.itertext() if t.strip())
    except Exception as e:
        print(f"[AVISO EXTRACCIÓN XML {extension}]: {repr(e)}")
    return "\n".join(textos)

def extraer_texto_binario_doc_o_rtf(buffer_bytes, extension):
    """Extractor local de respaldo para archivos binarios antiguos .doc (OLE2) y .rtf."""
    try:
        if extension == '.rtf':
            contenido = buffer_bytes.decode('latin-1', errors='ignore')
            contenido = re.sub(r'\\([a-z]{1,32})(-?\d{1,10})?[ ]?|\\\'[0-9a-f]{2}|\\[{}]|[{}]', ' ', contenido)
            return re.sub(r'\s+', ' ', contenido).strip()

        # Extracción híbrida UTF-16LE y CP1252 para bloques de texto en Word 97-2003 (.doc)
        fragmentos = []
        texto_utf16 = buffer_bytes.decode('utf-16le', errors='ignore')
        for bloque in re.findall(r'[A-Za-zÁÉÍÓÚáéíóúÑñÜü0-9 ,\.;:\-\(\)/@\n\r]{15,}', texto_utf16):
            limpio = bloque.strip()
            if len(re.findall(r'[A-Za-zÁÉÍÓÚáéíóúÑñ]{3,}', limpio)) >= 2:
                fragmentos.append(limpio)

        texto_latin = buffer_bytes.decode('cp1252', errors='ignore')
        for bloque in re.findall(r'[A-Za-zÁÉÍÓÚáéíóúÑñÜü0-9 ,\.;:\-\(\)/@\n\r]{20,}', texto_latin):
            limpio = bloque.strip()
            if not any(meta in limpio for meta in ['Microsoft Word', 'Normal.dot', 'MSWordDoc', 'Word.Document', 'Root Entry']):
                if len(re.findall(r'[A-Za-zÁÉÍÓÚáéíóúÑñ]{3,}', limpio)) >= 3:
                    fragmentos.append(limpio)

        return "\n".join(fragmentos)
    except Exception as e:
        print(f"[AVISO EXTRACCIÓN BINARIA .DOC]: {repr(e)}")
        return ""

def convertir_y_ocr_con_google_drive(file_bytes=None, mime_origen="application/octet-stream", drive_file_id=None, extension=""):
    """
    Motor de Conversión y OCR en la Nube:
    Utiliza Google Drive API para convertir cualquier archivo (.doc, .xls, .ppt, imagen o PDF escaneado)
    en un documento nativo temporal de Google con OCR en español, extrae el texto y elimina el temporal.
    """
    temp_id = None
    servicio = None
    try:
        credenciales = obtener_credenciales()
        servicio = build('drive', 'v3', credentials=credenciales)

        es_planilla = extension in ['.xls', '.xlsx'] or 'spreadsheet' in mime_origen or 'excel' in mime_origen
        mime_destino = 'application/vnd.google-apps.spreadsheet' if es_planilla else 'application/vnd.google-apps.document'
        mime_exportacion = 'text/csv' if es_planilla else 'text/plain'

        # Si el archivo ya existe en Drive, intentamos copia directa con conversión
        if drive_file_id:
            try:
                meta_copia = {
                    'name': f'_thiago_temp_ocr_{datetime.datetime.now().timestamp()}',
                    'mimeType': mime_destino
                }
                copia = servicio.files().copy(
                    fileId=drive_file_id,
                    body=meta_copia,
                    fields='id',
                    ocrLanguage='es',
                    supportsAllDrives=True
                ).execute()
                temp_id = copia.get('id')
            except Exception as err_copy:
                print(f"[AVISO COPIA DRIVE OCR, USANDO SUBIDA DE BYTES]: {repr(err_copy)}")
                temp_id = None

        # Si es un archivo local o si la copia directa requirió subida por stream
        if not temp_id and file_bytes:
            media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype=mime_origen, resumable=False)
            meta_create = {
                'name': f'_thiago_temp_upload_{datetime.datetime.now().timestamp()}',
                'mimeType': mime_destino
            }
            creado = servicio.files().create(
                body=meta_create,
                media_body=media,
                fields='id',
                ocrLanguage='es',
                supportsAllDrives=True
            ).execute()
            temp_id = creado.get('id')

        if not temp_id:
            return ""

        exportado = servicio.files().export_media(
            fileId=temp_id,
            mimeType=mime_exportacion
        ).execute()

        texto_final = exportado.decode('utf-8-sig', errors='ignore').strip()
        return texto_final
    except Exception as e:
        print(f"[AVISO MOTOR OCR GOOGLE DRIVE]: {repr(e)}")
        return ""
    finally:
        if temp_id and servicio:
            try:
                servicio.files().delete(fileId=temp_id, supportsAllDrives=True).execute()
            except Exception:
                pass

def extraer_imagenes_de_pdf_para_vision(file_bytes):
    """Extrae flujos de imágenes (JPEG/PNG) incrustados en páginas de un PDF escaneado."""
    imagenes_b64 = []
    try:
        lector = pypdf.PdfReader(io.BytesIO(file_bytes))
        for page in lector.pages[:8]:
            # Intento 1: Recorrer XObjects directamente para extraer flujos JPEG (/DCTDecode) sin requerir Pillow
            recursos = page.get("/Resources", {})
            if hasattr(recursos, "get_object"):
                recursos = recursos.get_object()
            xobjects = recursos.get("/XObject", {}) if isinstance(recursos, dict) else {}
            if hasattr(xobjects, "get_object"):
                xobjects = xobjects.get_object()

            for nombre_obj in xobjects:
                try:
                    xobj = xobjects[nombre_obj].get_object()
                    if xobj.get("/Subtype") == "/Image":
                        filtro = str(xobj.get("/Filter", ""))
                        if "DCTDecode" in filtro:
                            raw_jpeg = xobj._data
                            if raw_jpeg and len(raw_jpeg) > 1000:
                                b64 = base64.b64encode(raw_jpeg).decode('utf-8')
                                imagenes_b64.append(f"data:image/jpeg;base64,{b64}")
                except Exception:
                    continue

            # Intento 2: Usar page.images si Pillow está disponible en el entorno
            if not imagenes_b64:
                try:
                    for img in page.images:
                        if img.data and len(img.data) > 1000:
                            ext_img = "png" if img.name.lower().endswith(".png") else "jpeg"
                            b64 = base64.b64encode(img.data).decode('utf-8')
                            imagenes_b64.append(f"data:image/{ext_img};base64,{b64}")
                except Exception:
                    pass
    except Exception as e:
        print(f"[AVISO EXTRACCIÓN IMÁGENES PDF]: {repr(e)}")
    return imagenes_b64[:6]

def extraer_ocr_vision_openai(file_bytes, filename, mime_type=""):
    """
    Motor de Respaldo Multimodal con OpenAI (gpt-4o-mini):
    Transcribe imágenes y documentos PDF escaneados mediante visión artificial.
    """
    if not OPENAI_API_KEY or not file_bytes:
        return ""

    url_api = "https://api.openai.com/v1/chat/completions"
    cabeceras = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    bloques_contenido = [
        {
            "type": "text",
            "text": (
                "Transcribe de manera íntegra, literal y exacta todo el texto visible en este documento "
                f"('{filename}'). Incluye nombres, cargos, fechas, firmas, sellos, tablas y encabezados. "
                "No inventes datos ni agregues comentarios introductorios."
            )
        }
    ]

    ext = os.path.splitext(filename.lower())[1]
    if ext in ['.jpg', '.jpeg', '.png', '.webp'] or 'image/' in mime_type:
        mime_img = mime_type if 'image/' in mime_type else f"image/{'jpeg' if ext in ['.jpg', '.jpeg'] else ext.lstrip('.')}"
        b64_img = base64.b64encode(file_bytes).decode('utf-8')
        bloques_contenido.append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime_img};base64,{b64_img}"}
        })
    elif ext == '.pdf' or 'pdf' in mime_type:
        imagenes_pdf = extraer_imagenes_de_pdf_para_vision(file_bytes)
        if imagenes_pdf:
            for data_url in imagenes_pdf:
                bloques_contenido.append({
                    "type": "image_url",
                    "image_url": {"url": data_url}
                })
        else:
            b64_pdf = base64.b64encode(file_bytes).decode('utf-8')
            bloques_contenido.append({
                "type": "file",
                "file": {
                    "filename": filename,
                    "file_data": f"data:application/pdf;base64,{b64_pdf}"
                }
            })
    else:
        return ""

    try:
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": bloques_contenido}],
            "temperature": 0.0
        }
        resp = requests.post(url_api, json=payload, headers=cabeceras, timeout=45)
        datos = resp.json()
        if "choices" in datos and datos["choices"]:
            return datos["choices"][0]["message"].get("content", "").strip()
    except Exception as e:
        print(f"[AVISO OCR VISIÓN OPENAI]: {repr(e)}")
    return ""

def procesar_bytes_documento_universal(file_bytes, filename, mime_type="", drive_file_id=None):
    """
    Orquestador Universal de Lectura Documental:
    Soporta .pdf (digitales o escaneados), .doc, .docx, .xls, .xlsx, .ppt, .pptx,
    .odt, .rtf, .txt, .csv, .json, .md, .html e imágenes (.jpg, .jpeg, .png, .webp).
    """
    nombre_lower = (filename or "").lower()
    ext = os.path.splitext(nombre_lower)[1]
    mime_lower = (mime_type or "").lower()
    texto_extraido = ""

    # 1. Determinación de MIME por extensión si no viene informado
    mapa_mimes = {
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xls': 'application/vnd.ms-excel',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.ppt': 'application/vnd.ms-powerpoint',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.odt': 'application/vnd.oasis.opendocument.text',
        '.rtf': 'application/rtf',
        '.txt': 'text/plain',
        '.csv': 'text/csv',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.webp': 'image/webp'
    }
    if not mime_lower or mime_lower == 'application/octet-stream':
        mime_lower = mapa_mimes.get(ext, 'application/octet-stream')

    # 2. Intento de extracción local rápida según formato
    try:
        if ext == '.pdf' or 'pdf' in mime_lower:
            lector_pdf = pypdf.PdfReader(io.BytesIO(file_bytes))
            paginas_txt = []
            for pagina in lector_pdf.pages[:40]:
                t_pag = pagina.extract_text()
                if t_pag and t_pag.strip():
                    paginas_txt.append(t_pag.strip())
            texto_extraido = "\n".join(paginas_txt)

        elif ext == '.docx' or 'wordprocessingml' in mime_lower:
            texto_extraido = extraer_texto_docx_completo(file_bytes)
            if es_texto_insuficiente_o_marca_agua(texto_extraido):
                texto_extraido = extraer_texto_zip_xml(file_bytes, '.docx')

        elif ext in ['.xlsx', '.pptx', '.odt']:
            texto_extraido = extraer_texto_zip_xml(file_bytes, ext)

        elif ext in ['.txt', '.csv', '.json', '.md', '.html'] or mime_lower.startswith('text/'):
            try:
                texto_extraido = file_bytes.decode('utf-8-sig')
            except UnicodeDecodeError:
                texto_extraido = file_bytes.decode('cp1252', errors='ignore')
    except Exception as e:
        print(f"[AVISO EXTRACCIÓN LOCAL INICIAL]: {repr(e)}")

    # 3. Si es un PDF escaneado (ej. AnyScanner), un .doc antiguo, .xls, .ppt o imagen,
    #    o si la extracción local arrojó texto insuficiente, activamos Conversión y OCR en Google Drive
    if es_texto_insuficiente_o_marca_agua(texto_extraido):
        texto_drive_ocr = convertir_y_ocr_con_google_drive(
            file_bytes=file_bytes,
            mime_origen=mime_lower,
            drive_file_id=drive_file_id,
            extension=ext
        )
        if not es_texto_insuficiente_o_marca_agua(texto_drive_ocr):
            texto_extraido = texto_drive_ocr

    # 4. Si continúa siendo insuficiente (ej. PDF escaneado complejo o imagen), activamos Visión Artificial OpenAI
    if es_texto_insuficiente_o_marca_agua(texto_extraido):
        texto_vision = extraer_ocr_vision_openai(file_bytes, filename, mime_lower)
        if not es_texto_insuficiente_o_marca_agua(texto_vision):
            texto_extraido = texto_vision

    # 5. Respaldo final binario puro para archivos .doc o .rtf
    if es_texto_insuficiente_o_marca_agua(texto_extraido) and (ext in ['.doc', '.rtf'] or 'msword' in mime_lower):
        texto_bin = extraer_texto_binario_doc_o_rtf(file_bytes, ext or '.doc')
        if texto_bin:
            texto_extraido = texto_bin

    return texto_extraido.strip()[:35000]

# =============================================================================
# SECCIÓN 6: ENDPOINT DE CARGA DE ARCHIVOS LOCALES (/api/upload)
# =============================================================================
@app.route('/api/upload', methods=['POST'])
def procesar_carga_archivo():
    """Recibe un archivo local en cualquier formato, extrae su texto (con OCR si es necesario) y lo retorna."""
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No se recibió ningún archivo en la petición."}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "Nombre de archivo vacío."}), 400
    
    try:
        file_bytes = file.read()
        if not file_bytes:
            return jsonify({"success": False, "error": "El archivo enviado está vacío."}), 400

        texto_extraido = procesar_bytes_documento_universal(
            file_bytes=file_bytes,
            filename=file.filename,
            mime_type=file.mimetype or ""
        )

        if not texto_extraido:
            return jsonify({
                "success": False,
                "error": "No se pudo extraer texto legible del documento tras aplicar lectura nativa y OCR."
            }), 422

        return jsonify({
            "success": True,
            "filename": file.filename,
            "text": texto_extraido
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"Error al procesar el archivo: {str(e)}"}), 500

# =============================================================================
# SECCIÓN 7: HERRAMIENTAS AUTÓNOMAS (TOOLS) DE LECTURA, ESCRITURA Y MENSAJERÍA
# =============================================================================
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
    """
    Extrae texto de cualquier archivo en Google Drive (.doc, .docx, .pdf digitales o escaneados,
    hojas de cálculo, presentaciones, imágenes o documentos nativos).
    Si recibe el nombre en vez del ID, resuelve automáticamente el ID real.
    """
    try:
        credenciales = obtener_credenciales()
        servicio = build('drive', 'v3', credentials=credenciales)
        
        id_limpio = file_id.strip().replace("*", "")
        if len(id_limpio) < 15 or " " in id_limpio or "." in id_limpio:
            nombre_limpio = id_limpio.replace("'", "\\'")
            q_busqueda = f"name contains '{nombre_limpio}' and trashed = false"
            res_busqueda = servicio.files().list(
                q=q_busqueda,
                pageSize=1,
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            archivos_encontrados = res_busqueda.get('files', [])
            if not archivos_encontrados:
                return json.dumps({"error": f"No se pudo resolver el identificador para el documento: {file_id}"}, ensure_ascii=False)
            id_real_archivo = archivos_encontrados[0]['id']
        else:
            id_real_archivo = id_limpio

        metadatos = servicio.files().get(
            fileId=id_real_archivo,
            fields="name, mimeType",
            supportsAllDrives=True
        ).execute()
        nombre_archivo = metadatos.get('name', 'documento')
        tipo_mime = metadatos.get('mimeType', '')
        
        texto_extraido = ""
        
        # Caso 1: Archivos nativos de Google Workspace (Google Docs, Sheets, Slides)
        if 'application/vnd.google-apps.document' in tipo_mime:
            solicitud = servicio.files().export_media(fileId=id_real_archivo, mimeType='text/plain')
            texto_extraido = solicitud.execute().decode('utf-8-sig', errors='ignore')
        elif 'application/vnd.google-apps.spreadsheet' in tipo_mime:
            solicitud = servicio.files().export_media(fileId=id_real_archivo, mimeType='text/csv')
            texto_extraido = solicitud.execute().decode('utf-8-sig', errors='ignore')
        elif 'application/vnd.google-apps.presentation' in tipo_mime:
            solicitud = servicio.files().export_media(fileId=id_real_archivo, mimeType='text/plain')
            texto_extraido = solicitud.execute().decode('utf-8-sig', errors='ignore')
        else:
            # Caso 2: Archivos binarios o externos (.pdf, .doc, .docx, .xls, .xlsx, .ppt, .pptx, imágenes, etc.)
            solicitud = servicio.files().get_media(fileId=id_real_archivo, supportsAllDrives=True)
            buffer_memoria = io.BytesIO()
            descargador = MediaIoBaseDownload(buffer_memoria, solicitud)
            terminado = False
            while not terminado:
                _, terminado = descargador.next_chunk()
            
            bytes_archivo = buffer_memoria.getvalue()
            texto_extraido = procesar_bytes_documento_universal(
                file_bytes=bytes_archivo,
                filename=nombre_archivo,
                mime_type=tipo_mime,
                drive_file_id=id_real_archivo
            )
                    
        if not texto_extraido or not texto_extraido.strip():
            return json.dumps({
                "archivo": nombre_archivo,
                "contenido": "El archivo fue procesado, pero no contiene texto extraíble ni elementos legibles por OCR."
            }, ensure_ascii=False)
            
        return json.dumps({
            "archivo": nombre_archivo,
            "contenido": texto_extraido[:25000]
        }, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO DRIVE LECTURA DETALLADO]: {repr(error)}")
        return json.dumps({"error_tecnico_drive_lectura": str(error)}, ensure_ascii=False)

def tool_busqueda_web(query):
    """Realiza una búsqueda web estructurada utilizando Serper API. Incluye inyección de filtros avanzados."""
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return json.dumps({"error": "La clave SERPER_API_KEY no está configurada en Render."}, ensure_ascii=False)

    url = "https://google.serper.dev/search"
    consulta_blindada = f"{query} -site:wikipedia.org -site:es.wikipedia.org"
    
    payload = json.dumps({"q": consulta_blindada, "gl": "ar", "hl": "es"})
    headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}

    try:
        response = requests.post(url, headers=headers, data=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        resultados = []
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
            destinatario_formateado = f"whatsapp:+{destinatario_limpio}"
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
# SECCIÓN 8: MAPEO DE HERRAMIENTAS Y ESPECIFICACIÓN DE FUNCIONES PARA OPENAI
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
            "description": "Extrae el texto completo de cualquier archivo en Google Drive (.pdf digital o escaneado, .doc, .docx, .xls, .xlsx, .ppt, .pptx, imágenes o Google Docs) dado su ID único o su nombre.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_id": {"type": "string", "description": "El ID único o el nombre exacto del archivo en Google Drive."}
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
# SECCIÓN 9: CONTROLADORES PRINCIPALES (LOOP COGNITIVO)
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
            ahora_bsas = datetime.datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-3)))
            fecha_str = ahora_bsas.strftime('%A, %d de %B de %Y, %H:%M:%S')
            
            instruccion_dinamica = (
                SYSTEM_INSTRUCTION +
                f"\n\nINFORMACIÓN VITAL: Hoy es {fecha_str} (Hora de Buenos Aires, Argentina). "
                "Utiliza esta fecha y hora como referencia absoluta y obligatoria para agendar, buscar o eliminar eventos en Google Calendar."
            )
            
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
                
                respuesta = requests.post(url_api, json=payload_inicial, headers=cabeceras, timeout=60)
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
