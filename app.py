# -*- coding: utf-8 -*-
"""
=============================================================================
 NÚCLEO CENTRAL DE THIAGO - AGENTE AUTÓNOMO BIDIRECCIONAL INTEGRAL (v4.0)
 Arquitectura de Conectividad Total, OCR Universal, Caché Documental,
 Lectura Literal Íntegra y Secuenciador de Voz de Larga Duración.
 Desarrollado exclusivamente para el Prof. David Villarreal
 Abogado, Babalawo de Ifá tradicional yoruba, Batuque Isesa, profesor de inglés,
 magíster en relaciones internacionales, masón y doctorando.
=============================================================================
"""

import os
import re
import io
import time
import uuid
import json
import base64
import zipfile
import datetime
from datetime import timezone, timedelta
import xml.etree.ElementTree as ET
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from flask import Flask, render_template_string, request, jsonify, Response
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
import pypdf
import docx


# =============================================================================
# SECCIÓN 1: INICIALIZACIÓN, CONFIGURACIÓN Y CACHÉ DOCUMENTAL EN SERVIDOR
# =============================================================================
app = Flask(__name__)

# Límite ampliado a 50 MB para permitir la subida de libros, fallos y planchas
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL_MAIN = os.getenv("OPENAI_MODEL_MAIN", "gpt-4o-mini").strip()
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "").strip()

# Caché en memoria del servidor para almacenar el texto íntegro del último
# documento procesado (local o de Google Drive), evitando reenviar decenas de
# miles de caracteres desde el navegador en cada turno conversacional.
DOCUMENT_CACHE = {
    "ultimo_documento": {
        "id_documento": None,
        "nombre": None,
        "origen": None,
        "mime_type": None,
        "texto_integro": "",
        "longitud_caracteres": 0,
        "fecha_carga": None
    },
    "historial_documentos": {}
}


def guardar_documento_en_cache(nombre, texto, origen="local", mime_type="text/plain", doc_id=None):
    """
    Almacena de forma segura el contenido íntegro de un documento en la memoria
    del servidor para su lectura literal instantánea o consulta reiterada.
    """
    if not texto:
        return None

    identificador = doc_id or str(uuid.uuid4())
    ahora_iso = datetime.datetime.now(timezone.utc).isoformat()
    registro = {
        "id_documento": identificador,
        "nombre": nombre or "Documento_Sin_Titulo",
        "origen": origen,
        "mime_type": mime_type,
        "texto_integro": texto,
        "longitud_caracteres": len(texto),
        "fecha_carga": ahora_iso
    }
    DOCUMENT_CACHE["ultimo_documento"] = registro
    DOCUMENT_CACHE["historial_documentos"][identificador] = registro

    # Mantenemos únicamente los últimos 10 documentos en caché para cuidar la RAM
    if len(DOCUMENT_CACHE["historial_documentos"]) > 10:
        llave_mas_antigua = next(iter(DOCUMENT_CACHE["historial_documentos"]))
        if llave_mas_antigua != identificador:
            DOCUMENT_CACHE["historial_documentos"].pop(llave_mas_antigua, None)

    return registro


def obtener_ultimo_documento_cache():
    """Recupera el último documento cargado o leído desde Drive."""
    doc = DOCUMENT_CACHE.get("ultimo_documento", {})
    if doc and doc.get("texto_integro"):
        return doc
    return None


# =============================================================================
# SECCIÓN 2: INSTRUCCIÓN DE SISTEMA (SYSTEM PROMPT) Y DETECTOR DE LECTURA LITERAL
# =============================================================================
SYSTEM_INSTRUCTION = (
    "Eres Thiago, el núcleo de inteligencia artificial autónoma del Prof. David Villarreal "
    "(David Efraín Villarreal, identificado frecuentemente con las iniciales DEV). "
    "El profesor es abogado especialista en derechos humanos en la CABA, docente de Formación Ética y Ciudadana "
    "en la Escuela Superior de Comercio Carlos Pellegrini, Babalawo de Ifá tradicional yoruba, Batuque Isesa, "
    "profesor de inglés, magíster en relaciones internacionales por la UBA, doctorando y Maestro Masón. "
    "Tus respuestas deben destacar por su rigor académico, precisión técnica y corrección gramatical absoluta, "
    "evitando de forma estricta vicios de lenguaje como el queísmo, el dequeísmo y el loqueísmo. "
    "\n\n"
    "REGLA DE ORO INQUEBRANTABLE 1 (VERACIDAD OPERATIVA): "
    "Jamás inventes, finjas o simules haber ejecutado una acción. "
    "\n\n"
    "REGLA DE ORO INQUEBRANTABLE 2 (EXIGENCIA ACADÉMICA Y JURÍDICA): "
    "Si el profesor solicita 'jurisprudencia', ESTÁS OBLIGADO a buscar y proporcionar los FALLOS REALES "
    "(sentencias dictadas por tribunales, como la CSJN o la Corte IDH), citando la parte pertinente del fallo. "
    "ESTÁ TERMINANTEMENTE PROHIBIDO confundir jurisprudencia con 'doctrina' (artículos de opinión). "
    "ESTÁ TERMINANTEMENTE PROHIBIDO utilizar o citar Wikipedia, blogs o fuentes no oficiales. "
    "Toda respuesta que cite obras, autores o sitios debe aplicar estrictamente las normas APA (7.ª edición). "
    "\n\n"
    "REGLA CRÍTICA DE LECTURA LITERAL VS. RESUMEN (PRIORIDAD MÁXIMA): "
    "1. Cuando el profesor te pida 'leeme este archivo', 'leeme el documento', 'quiero que me leas el documento' "
    "o 'no quiero un resumen, quiero que me leas el documento', ESTÁ TERMINANTEMENTE PROHIBIDO hacer un resumen. "
    "Debes entregar la transcripción literal, completa y fiel del texto del documento sin omitir párrafos. "
    "2. Únicamente realizarás un resumen, síntesis o cuadro sinóptico cuando el profesor utilice de manera explícita "
    "las palabras 'resumí', 'haz un resumen', 'sintetizá' o 'extraé los puntos clave'. "
    "3. Al buscar el CV del profesor en Google Drive, prioriza siempre el archivo 'CV DEV.doc' o aquellos que "
    "contengan 'David Villarreal', descartando currículums de terceras personas. "
    "\n\n"
    "REGLA CRÍTICA DE CALENDARIO Y EJECUCIÓN AUTÓNOMA: "
    "Al crear eventos, valida que no existan duplicados. Si el profesor solicita agendar, enviar un correo, "
    "crear un documento en Drive o despachar un WhatsApp por Twilio, ejecuta la herramienta correspondiente "
    "de inmediato y sin pedirle jamás que realice pasos manuales."
)

# Patrones léxicos que indican que el profesor exige la lectura literal e íntegra
# del documento y NO un resumen generado por el modelo.
PATRONES_LECTURA_LITERAL = [
    r"no\s+quiero\s+(un\s+)?resumen",
    r"quiero\s+que\s+(me\s+)?leas\s+el\s+(documento|archivo|texto)",
    r"lee(me)?\s+el\s+(documento|archivo|texto)\s+(anterior|completo|integro|íntegro|entero)",
    r"^lee(me)?\s+(este|el)\s+(documento|archivo)\.?$",
    r"transcrib(i|í|e)\s+el\s+(documento|archivo)",
    r"mostra(me)?\s+el\s+(texto|contenido)\s+(completo|integro|íntegro|literal)",
    r"leer\s+sin\s+resumir",
    r"texto\s+literal\s+completo"
]


def solicita_lectura_literal_directa(mensaje_usuario):
    """
    Determina si la instrucción del usuario exige la entrega literal e íntegra
    del documento cargado en lugar de una interpretación o resumen.
    """
    if not mensaje_usuario:
        return False

    # Si el mensaje trae inyectado el encabezado de adjunto, extraemos solo la directiva
    texto_directiva = mensaje_usuario
    if "Directiva del Profesor:" in mensaje_usuario:
        partes = mensaje_usuario.split("Directiva del Profesor:")
        texto_directiva = partes[-1].strip()

    limpio = texto_directiva.strip().lower()

    # Si el usuario pide explícitamente un resumen o análisis, no activamos lectura literal
    if any(p in limpio for p in ["resum", "sintetiz", "puntos clave", "explic", "analiz", "opin"]):
        if "no quiero un resumen" not in limpio and "sin resumir" not in limpio:
            return False

    for patron in PATRONES_LECTURA_LITERAL:
        if re.search(patron, limpio):
            return True

    return False


# =============================================================================
# SECCIÓN 3: INTERFAZ GRÁFICA DE USUARIO (HTML, CSS Y JAVASCRIPT AVANZADO)
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
            --bg-panel: #131c2e;
            --accent-blue: #38bdf8;
            --accent-user: #0284c7;
            --accent-gold: #f59e0b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border-color: #334155;
            --error-color: #f87171;
            --active-mic: #ef4444;
            --success-color: #10b981;
        }

        * {
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg-primary);
            color: var(--text-main);
            margin: 0;
            padding: 18px;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
        }

        .container {
            width: 100%;
            max-width: 900px;
            background: var(--bg-secondary);
            padding: 26px;
            border-radius: 14px;
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.65);
            border: 1px solid var(--border-color);
        }

        .header-top {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-bottom: 16px;
        }

        h1 {
            color: var(--accent-blue);
            text-align: center;
            font-size: 1.75rem;
            margin: 0 0 6px 0;
            font-weight: 700;
            letter-spacing: -0.5px;
        }

        .subtitle {
            text-align: center;
            color: var(--text-muted);
            font-size: 0.92rem;
            font-weight: 500;
        }

        .status-toolbar {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 10px;
            background: var(--bg-panel);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 10px 14px;
            margin-bottom: 16px;
            font-size: 0.85rem;
        }

        .doc-status {
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 8px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            max-width: 52%;
        }

        .doc-status strong {
            color: var(--accent-blue);
        }

        .voice-controls {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }

        .btn-mini {
            padding: 6px 12px;
            font-size: 0.82rem;
            border-radius: 6px;
            background: var(--border-color);
            color: var(--text-main);
            border: 1px solid #475569;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.15s ease;
        }

        .btn-mini:hover {
            background: #475569;
            border-color: var(--accent-blue);
        }

        .btn-mini.gold {
            background: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border-color: #f59e0b;
        }

        .btn-mini.gold:hover {
            background: rgba(245, 158, 11, 0.28);
        }

        .chat-box {
            background: var(--bg-terminal);
            border: 1px solid var(--border-color);
            height: 450px;
            overflow-y: auto;
            padding: 18px;
            margin-bottom: 16px;
            border-radius: 10px;
            display: flex;
            flex-direction: column;
            gap: 14px;
            box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.5);
        }

        .message {
            padding: 13px 17px;
            border-radius: 9px;
            max-width: 88%;
            line-height: 1.62;
            word-break: break-word;
            white-space: pre-wrap;
            font-size: 0.95rem;
            position: relative;
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

        .doc-verbatim-box {
            border-left: 4px solid var(--accent-gold);
            background: #111827;
            font-family: "Georgia", "Times New Roman", serif;
            font-size: 0.98rem;
            line-height: 1.7;
            max-width: 96%;
        }

        .confirm-banner {
            display: none;
            align-items: center;
            justify-content: space-between;
            background: rgba(56, 189, 248, 0.12);
            border: 1px solid var(--accent-blue);
            color: var(--text-main);
            padding: 10px 14px;
            border-radius: 8px;
            margin-bottom: 12px;
            font-size: 0.9rem;
        }

        .confirm-banner.visible {
            display: flex;
        }

        .confirm-actions {
            display: flex;
            gap: 8px;
        }

        .input-group {
            display: flex;
            gap: 10px;
            align-items: center;
        }

        input[type="text"] {
            flex: 1;
            padding: 13px 16px;
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
            padding: 12px 15px;
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
            0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.45); }
            70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
            100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
        }

        @keyframes pulse-dot {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1.0); }
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
            border-color: var(--error-color);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-top">
            <h1>Núcleo Central de Thiago</h1>
            <div class="subtitle">Prof. David Villarreal — Agente Autónomo Bidireccional y Lector Documental Íntegro</div>
        </div>

        <div class="status-toolbar">
            <div class="doc-status" id="docStatusIndicator">
                📄 Documento en búfer: <strong id="docStatusName">Ninguno cargado</strong>
            </div>
            <div class="voice-controls">
                <button type="button" class="btn-mini gold" onclick="mostrarYLeerDocumentoIntegro()" title="Muestra y lee en voz alta el documento completo sin resumir">📖 Leer Documento Íntegro</button>
                <button type="button" class="btn-mini" onclick="leerUltimaRespuestaEnPantalla()" title="Lee en voz alta el último mensaje de Thiago">🔊 Leer Respuesta</button>
                <button type="button" class="btn-mini" id="pauseResumeBtn" onclick="pausarReanudarVoz()" title="Pausar o reanudar la lectura por voz">⏯️ Pausar/Reanudar</button>
                <button type="button" class="btn-mini" onclick="detenerVozCompleta()" title="Detener inmediatamente la lectura en voz alta">⏹️ Silenciar</button>
            </div>
        </div>

        <div class="confirm-banner" id="confirmBanner">
            <span>🔊 <strong>Lectura disponible:</strong> ¿Desea que Thiago lea el texto en voz alta? (Puede responder "Sí" o presionar el botón)</span>
            <div class="confirm-actions">
                <button type="button" class="btn-mini gold" onclick="confirmarLecturaManual(true)">Sí, leer ahora</button>
                <button type="button" class="btn-mini" onclick="confirmarLecturaManual(false)">No, gracias</button>
            </div>
        </div>

        <div class="chat-box" id="chatBox"></div>

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

        // Búfer persistente del último documento completo para lectura literal sin resúmenes
        let ultimoDocumentoTexto = localStorage.getItem('thiago_ultimo_doc_texto') || "";
        let ultimoDocumentoNombre = localStorage.getItem('thiago_ultimo_doc_nombre') || "";

        // Variables del Secuenciador de Voz por Fragmentos (TTS Chunking Engine)
        let respuestaPendienteDeLectura = "";
        let esperandoConfirmacionDeVoz = false;
        let colaFragmentosTTS = [];
        let indiceFragmentoActual = 0;
        let lecturaEnCurso = false;
        let lecturaPausada = false;

        // Memoria Persistente en el Cliente
        let memoriaLocal = [];
        try {
            memoriaLocal = JSON.parse(localStorage.getItem('thiago_memoria')) || [];
        } catch (e) {
            memoriaLocal = [];
        }

        function actualizarIndicadorDocumento() {
            const label = document.getElementById('docStatusName');
            if (archivoAdjuntoNombre) {
                label.textContent = archivoAdjuntoNombre + " (Listo para enviar)";
            } else if (ultimoDocumentoNombre) {
                label.textContent = ultimoDocumentoNombre + " (" + ultimoDocumentoTexto.length + " caract.)";
            } else {
                label.textContent = "Ninguno cargado";
            }
        }

        function mostrarBannerConfirmacion(mostrar) {
            const banner = document.getElementById('confirmBanner');
            if (mostrar) {
                banner.classList.add('visible');
            } else {
                banner.classList.remove('visible');
            }
        }

        function escaparHTML(texto) {
            if (!texto) return "";
            return texto
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;");
        }

        function renderizarHistorial() {
            const chatBox = document.getElementById('chatBox');
            chatBox.innerHTML = '<div class="message ai-msg">Núcleo integral en línea. Módulos operativos, lectura literal íntegra (sin resúmenes forzados) y secuenciador de voz activos. ¿Qué directiva procesamos?</div>';

            memoriaLocal.forEach(msg => {
                if (msg.role === 'user') {
                    let displayTexto = msg.display || msg.content || "";
                    if (displayTexto.includes("[Se adjunta el archivo:")) {
                        let partes = displayTexto.split("Directiva del Profesor:");
                        if (partes.length > 1) {
                            displayTexto = "📎 Archivo enviado.\\n" + partes[1].trim();
                        }
                    }
                    chatBox.innerHTML += `<div class="message user-msg">${escaparHTML(displayTexto)}</div>`;
                } else if (msg.role === 'assistant') {
                    const claseExtra = msg.esVerbatim ? "doc-verbatim-box" : "";
                    chatBox.innerHTML += `<div class="message ai-msg ${claseExtra}">${escaparHTML(msg.content)}</div>`;
                }
            });
            chatBox.scrollTop = chatBox.scrollHeight;
            actualizarIndicadorDocumento();
        }

        window.onload = renderizarHistorial;

        function borrarMemoria() {
            if (confirm("¿Desea purgar la memoria persistente de Thiago y limpiar el búfer documental?")) {
                detenerVozCompleta();
                localStorage.removeItem('thiago_memoria');
                localStorage.removeItem('thiago_ultimo_doc_texto');
                localStorage.removeItem('thiago_ultimo_doc_nombre');
                memoriaLocal = [];
                archivoAdjuntoTexto = "";
                archivoAdjuntoNombre = "";
                ultimoDocumentoTexto = "";
                ultimoDocumentoNombre = "";
                esperandoConfirmacionDeVoz = false;
                respuestaPendienteDeLectura = "";
                mostrarBannerConfirmacion(false);
                document.getElementById('userInput').placeholder = "Escriba su consulta o hable...";
                renderizarHistorial();
            }
        }

        // =========================================================================
        // MOTOR SECUENCIADOR DE VOZ DE LARGA DURACIÓN (TTS CHUNKING ENGINE)
        // Divide documentos largos en oraciones <= 220 caracteres para evitar el
        // corte de 15 segundos de Chrome/Edge y permitir lecturas completas.
        // =========================================================================
        function limpiarTextoParaVoz(texto) {
            if (!texto) return "";
            return texto
                .replace(/[*_#`~|>]/g, ' ')
                .replace(/\\s+/g, ' ')
                .trim();
        }

        function fragmentarTextoParaTTS(texto, maxLargo = 210) {
            const limpio = limpiarTextoParaVoz(texto);
            if (!limpio) return [];

            const oraciones = limpio.match(/[^.!?\\n]+[.!?\\n]+|[^.!?\\n]+$/g) || [limpio];
            const fragmentos = [];
            let actual = "";

            for (let oracion of oraciones) {
                oracion = oracion.trim();
                if (!oracion) continue;

                if ((actual + " " + oracion).trim().length <= maxLargo) {
                    actual = (actual + " " + oracion).trim();
                } else {
                    if (actual) fragmentos.push(actual);
                    if (oracion.length <= maxLargo) {
                        actual = oracion;
                    } else {
                        // Si una oración individual supera maxLargo, cortamos por palabras
                        const palabras = oracion.split(" ");
                        actual = "";
                        for (let palabra of palabras) {
                            if ((actual + " " + palabra).trim().length <= maxLargo) {
                                actual = (actual + " " + palabra).trim();
                            } else {
                                if (actual) fragmentos.push(actual);
                                actual = palabra;
                            }
                        }
                    }
                }
            }
            if (actual) fragmentos.push(actual);
            return fragmentos;
        }

        function reproducirSiguienteFragmentoTTS() {
            if (!('speechSynthesis' in window)) return;
            if (!lecturaEnCurso || lecturaPausada) return;

            if (indiceFragmentoActual >= colaFragmentosTTS.length) {
                lecturaEnCurso = false;
                indiceFragmentoActual = 0;
                colaFragmentosTTS = [];
                return;
            }

            const textoFragmento = colaFragmentosTTS[indiceFragmentoActual];
            const utterance = new SpeechSynthesisUtterance(textoFragmento);
            utterance.lang = 'es-AR';
            utterance.rate = 1.0;

            utterance.onend = function() {
                if (lecturaEnCurso && !lecturaPausada) {
                    indiceFragmentoActual++;
                    reproducirSiguienteFragmentoTTS();
                }
            };

            utterance.onerror = function() {
                if (lecturaEnCurso && !lecturaPausada) {
                    indiceFragmentoActual++;
                    reproducirSiguienteFragmentoTTS();
                }
            };

            window.speechSynthesis.speak(utterance);
        }

        function hablarTextoDefinitivo(texto) {
            if (!('speechSynthesis' in window) || !texto) return;
            window.speechSynthesis.cancel();
            colaFragmentosTTS = fragmentarTextoParaTTS(texto);
            indiceFragmentoActual = 0;
            lecturaEnCurso = true;
            lecturaPausada = false;
            mostrarBannerConfirmacion(false);
            reproducirSiguienteFragmentoTTS();
        }

        function pausarReanudarVoz() {
            if (!('speechSynthesis' in window)) return;
            if (window.speechSynthesis.speaking && !lecturaPausada) {
                lecturaPausada = true;
                window.speechSynthesis.pause();
            } else if (lecturaPausada) {
                lecturaPausada = false;
                window.speechSynthesis.resume();
                if (!window.speechSynthesis.speaking && lecturaEnCurso) {
                    reproducirSiguienteFragmentoTTS();
                }
            }
        }

        function detenerVozCompleta() {
            if ('speechSynthesis' in window) {
                lecturaEnCurso = false;
                lecturaPausada = false;
                colaFragmentosTTS = [];
                indiceFragmentoActual = 0;
                window.speechSynthesis.cancel();
            }
            esperandoConfirmacionDeVoz = false;
            mostrarBannerConfirmacion(false);
        }

        function leerUltimaRespuestaEnPantalla() {
            if (respuestaPendienteDeLectura) {
                hablarTextoDefinitivo(respuestaPendienteDeLectura);
                return;
            }
            for (let i = memoriaLocal.length - 1; i >= 0; i--) {
                if (memoriaLocal[i].role === 'assistant' && memoriaLocal[i].content) {
                    hablarTextoDefinitivo(memoriaLocal[i].content);
                    return;
                }
            }
            alert("No hay ninguna respuesta reciente para leer.");
        }

        async function mostrarYLeerDocumentoIntegro() {
            // Si no tenemos documento en el navegador, consultamos la caché del servidor
            if (!ultimoDocumentoTexto) {
                try {
                    const resp = await fetch('/api/document/latest');
                    const data = await resp.json();
                    if (data.success && data.text) {
                        ultimoDocumentoTexto = data.text;
                        ultimoDocumentoNombre = data.filename;
                        localStorage.setItem('thiago_ultimo_doc_texto', ultimoDocumentoTexto);
                        localStorage.setItem('thiago_ultimo_doc_nombre', ultimoDocumentoNombre);
                        actualizarIndicadorDocumento();
                    }
                } catch (e) {}
            }

            if (!ultimoDocumentoTexto) {
                alert("No hay ningún documento cargado en el búfer actualmente. Adjunte un archivo con el ícono 📎 o solicite leer un archivo de Google Drive.");
                return;
            }

            const chatBox = document.getElementById('chatBox');
            const encabezado = `📄 TRANSCRIPCIÓN LITERAL E ÍNTEGRA DEL DOCUMENTO: "${ultimoDocumentoNombre}"\\n` +
                               `══════════════════════════════════════════════════════════════════\\n\\n`;
            const textoCompleto = encabezado + ultimoDocumentoTexto;

            chatBox.innerHTML += `<div class="message ai-msg doc-verbatim-box">${escaparHTML(textoCompleto)}</div>`;
            chatBox.scrollTop = chatBox.scrollHeight;

            memoriaLocal.push({
                role: 'assistant',
                content: textoCompleto,
                esVerbatim: true
            });
            guardarMemoriaLocalSegura();

            respuestaPendienteDeLectura = ultimoDocumentoTexto;
            hablarTextoDefinitivo(ultimoDocumentoTexto);
        }

        function confirmarLecturaManual(aceptado) {
            esperandoConfirmacionDeVoz = false;
            mostrarBannerConfirmacion(false);
            if (aceptado && respuestaPendienteDeLectura) {
                hablarTextoDefinitivo(respuestaPendienteDeLectura);
            } else {
                respuestaPendienteDeLectura = "";
            }
        }

        // Evalúa si una entrada (por voz o por teclado) es una confirmación afirmativa o negativa
        function evaluarRespuestaConfirmacion(textoEntrada) {
            const t = (textoEntrada || "").trim().toLowerCase();
            const afirmativas = [
                "si", "sí", "si.", "sí.", "claro", "por favor", "dale", "bueno",
                "leelo", "léelo", "leela", "léela", "lee", "leer",
                "si por favor", "sí por favor", "lee el documento",
                "lee el documento anterior", "lee el documento anterior, si",
                "lee el documento anterior, sí", "leeme el documento", "si leelo"
            ];
            const negativas = ["no", "no.", "no gracias", "no, gracias", "ahora no", "silencio", "cancelar"];

            if (afirmativas.includes(t) || /^(s[ií]|dale|claro|leel[oa])\b/.test(t)) {
                return "AFIRMATIVO";
            }
            if (negativas.includes(t) || /^no\b/.test(t)) {
                return "NEGATIVO";
            }
            return "OTRO";
        }

        // Detecta en el cliente si el usuario exige la lectura literal del documento en búfer
        function esOrdenDeLecturaLiteralCliente(textoUsuario) {
            const t = (textoUsuario || "").trim().toLowerCase();
            if (!t) return false;
            if (t.includes("no quiero un resumen") || t.includes("quiero que me leas el documento") || t.includes("sin resumir")) {
                return true;
            }
            const ordenesDirectas = [
                "leeme este archivo", "léeme este archivo", "leeme el archivo", "léeme el archivo",
                "leeme el documento", "léeme el documento", "lee el documento anterior",
                "lee el documento completo", "leeme el documento completo", "texto completo"
            ];
            return ordenesDirectas.includes(t);
        }

        function guardarMemoriaLocalSegura() {
            try {
                // Mantenemos los últimos 20 mensajes y evitamos duplicar textos gigantescos en LocalStorage
                const recorte = memoriaLocal.slice(-20);
                localStorage.setItem('thiago_memoria', JSON.stringify(recorte));
            } catch (e) {
                memoriaLocal = memoriaLocal.slice(-8);
                try {
                    localStorage.setItem('thiago_memoria', JSON.stringify(memoriaLocal));
                } catch (err) {}
            }
        }

        async function procesarArchivoLocal(input) {
            if (input.files && input.files[0]) {
                const archivo = input.files[0];
                const formData = new FormData();
                formData.append('file', archivo);

                const inputTexto = document.getElementById('userInput');
                const placeholderOriginal = inputTexto.placeholder;
                inputTexto.placeholder = "Procesando documento (extracción íntegra / OCR en curso)...";
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
                        ultimoDocumentoTexto = data.text;
                        ultimoDocumentoNombre = data.filename;
                        try {
                            localStorage.setItem('thiago_ultimo_doc_texto', ultimoDocumentoTexto);
                            localStorage.setItem('thiago_ultimo_doc_nombre', ultimoDocumentoNombre);
                        } catch (e) {}
                        actualizarIndicadorDocumento();
                        inputTexto.placeholder = `📎 Archivo cargado: ${archivoAdjuntoNombre}. Escriba "leeme este archivo" o su consulta...`;
                    } else {
                        alert("Error al procesar: " + (data.error || "Formato no reconocido."));
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
                const textoTranscrito = event.results[0][0].transcript;
                detenerEscuchaVisual();

                if (esperandoConfirmacionDeVoz) {
                    const decision = evaluarRespuestaConfirmacion(textoTranscrito);
                    if (decision === "AFIRMATIVO") {
                        esperandoConfirmacionDeVoz = false;
                        hablarTextoDefinitivo(respuestaPendienteDeLectura);
                        document.getElementById('userInput').value = '';
                        return;
                    } else if (decision === "NEGATIVO") {
                        esperandoConfirmacionDeVoz = false;
                        respuestaPendienteDeLectura = "";
                        mostrarBannerConfirmacion(false);
                        document.getElementById('userInput').value = '';
                        return;
                    }
                }

                document.getElementById('userInput').value = textoTranscrito;
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
                try { recognition.stop(); } catch (e) {}
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
            if (archivoAdjuntoTexto !== "") {
                document.getElementById('userInput').placeholder = `📎 Archivo cargado: ${archivoAdjuntoNombre}. Indique qué hacer con él...`;
            } else {
                document.getElementById('userInput').placeholder = "Escriba su consulta o hable...";
            }
            escuchando = false;
        }

        function solicitarPermisoLectura() {
            mostrarBannerConfirmacion(true);
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                const pregunta = new SpeechSynthesisUtterance("Profesor, la respuesta está en pantalla. ¿Desea que se la lea?");
                pregunta.lang = 'es-AR';
                pregunta.rate = 1.0;

                pregunta.onend = function() {
                    if (!recognition) return;
                    try {
                        recognition.start();
                        document.getElementById('micBtn').classList.add('active');
                        document.getElementById('userInput').placeholder = "Diga o escriba 'Sí' para escuchar en voz alta...";
                        escuchando = true;
                    } catch (e) {}
                };

                window.speechSynthesis.speak(pregunta);
            }
        }

        // Prepara un historial liviano para enviar al backend evitando saturar Gunicorn/Render
        function construirHistorialLivianoParaBackend() {
            const ultimos = memoriaLocal.slice(-8);
            return ultimos.map(item => {
                let contenido = item.content || "";
                if (contenido.length > 3500) {
                    contenido = contenido.substring(0, 3500) + "\\n...[Texto extenso resguardado en caché del servidor]...";
                }
                return {
                    role: item.role,
                    content: contenido
                };
            });
        }

        async function enviarMensaje() {
            if (escuchando && recognition) {
                try { recognition.stop(); } catch (e) {}
                detenerEscuchaVisual();
            }

            const input = document.getElementById('userInput');
            const chatBox = document.getElementById('chatBox');
            const texto = input.value.trim();

            if (!texto && archivoAdjuntoTexto === "") return;

            // 1. INTERCEPTOR BIMODAL DE CONFIRMACIÓN (Teclado + Voz):
            // Si Thiago acaba de preguntar "¿Desea que se la lea?" y el profesor escribe "si" o "leelo"
            if (esperandoConfirmacionDeVoz && archivoAdjuntoTexto === "") {
                const decisionTeclado = evaluarRespuestaConfirmacion(texto);
                if (decisionTeclado === "AFIRMATIVO") {
                    input.value = '';
                    esperandoConfirmacionDeVoz = false;
                    mostrarBannerConfirmacion(false);
                    chatBox.innerHTML += `<div class="message user-msg">${escaparHTML(texto)}</div>`;
                    chatBox.innerHTML += `<div class="message ai-msg">🔊 Iniciando lectura íntegra en voz alta. Puede utilizar los botones superiores para pausar, reanudar o silenciar.</div>`;
                    chatBox.scrollTop = chatBox.scrollHeight;
                    const textoALeer = esOrdenDeLecturaLiteralCliente(texto) && ultimoDocumentoTexto ? ultimoDocumentoTexto : respuestaPendienteDeLectura;
                    hablarTextoDefinitivo(textoALeer);
                    return;
                } else if (decisionTeclado === "NEGATIVO") {
                    input.value = '';
                    esperandoConfirmacionDeVoz = false;
                    respuestaPendienteDeLectura = "";
                    mostrarBannerConfirmacion(false);
                    chatBox.innerHTML += `<div class="message user-msg">${escaparHTML(texto)}</div>`;
                    chatBox.innerHTML += `<div class="message ai-msg">Comprendido, Profesor. Quedo a la espera de su próxima directiva.</div>`;
                    chatBox.scrollTop = chatBox.scrollHeight;
                    return;
                }
            }

            // Si el usuario envía una consulta nueva distinta, cancelamos cualquier voz previa
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
            }
            esperandoConfirmacionDeVoz = false;
            mostrarBannerConfirmacion(false);

            // 2. INTERCEPTOR DIRECTO DE LECTURA LITERAL ÍNTEGRA (Evita resúmenes no deseados y Timeouts)
            if (esOrdenDeLecturaLiteralCliente(texto) && (archivoAdjuntoTexto !== "" || ultimoDocumentoTexto !== "")) {
                const nombreDoc = archivoAdjuntoNombre || ultimoDocumentoNombre;
                const contenidoDoc = archivoAdjuntoTexto || ultimoDocumentoTexto;

                if (archivoAdjuntoTexto !== "") {
                    ultimoDocumentoTexto = archivoAdjuntoTexto;
                    ultimoDocumentoNombre = archivoAdjuntoNombre;
                    archivoAdjuntoTexto = "";
                    archivoAdjuntoNombre = "";
                    actualizarIndicadorDocumento();
                }

                input.value = '';
                input.placeholder = "Escriba su consulta o hable...";

                chatBox.innerHTML += `<div class="message user-msg">${escaparHTML(texto)}</div>`;
                const textoLiteral = `📄 LECTURA ÍNTEGRA Y LITERAL DEL DOCUMENTO: "${nombreDoc}"\\n` +
                                     `══════════════════════════════════════════════════════════════════\\n\\n` +
                                     contenidoDoc;
                chatBox.innerHTML += `<div class="message ai-msg doc-verbatim-box">${escaparHTML(textoLiteral)}</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;

                memoriaLocal.push({ role: 'user', content: texto, display: texto });
                memoriaLocal.push({ role: 'assistant', content: textoLiteral, esVerbatim: true });
                guardarMemoriaLocalSegura();

                respuestaPendienteDeLectura = contenidoDoc;
                esperandoConfirmacionDeVoz = true;
                solicitarPermisoLectura();
                return;
            }

            let textoUsuarioVisual = texto || "Lee el documento adjunto de manera íntegra.";
            let payloadCognitivo = textoUsuarioVisual;

            if (archivoAdjuntoTexto !== "") {
                chatBox.innerHTML += `<div class="message user-msg">📎 Archivo enviado: ${escaparHTML(archivoAdjuntoNombre)}<br>${escaparHTML(textoUsuarioVisual)}</div>`;
                payloadCognitivo = `[Se adjunta el archivo: ${archivoAdjuntoNombre}]\\n\\nContenido extraído del documento:\\n${archivoAdjuntoTexto}\\n\\nDirectiva del Profesor:\\n${textoUsuarioVisual}`;
                archivoAdjuntoTexto = "";
                archivoAdjuntoNombre = "";
                input.placeholder = "Escriba su consulta o hable...";
                actualizarIndicadorDocumento();
            } else {
                chatBox.innerHTML += `<div class="message user-msg">${escaparHTML(textoUsuarioVisual)}</div>`;
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
                const contextoLiviano = construirHistorialLivianoParaBackend();

                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: payloadCognitivo,
                        raw_directive: textoUsuarioVisual,
                        history: contextoLiviano
                    })
                });

                const textoRespuestaCrudo = await response.text();
                let data;
                try {
                    data = JSON.parse(textoRespuestaCrudo);
                } catch (jsonErr) {
                    throw new Error("El servidor tardó demasiado en responder o devolvió una respuesta no válida.");
                }

                const nodoCarga = document.getElementById(idCarga);
                if (nodoCarga) nodoCarga.remove();

                // Si el backend actualizó el documento activo (por ejemplo, al leer desde Drive), sincronizamos el búfer
                if (data.active_document && data.active_document.text) {
                    ultimoDocumentoTexto = data.active_document.text;
                    ultimoDocumentoNombre = data.active_document.filename || "Documento de Drive";
                    try {
                        localStorage.setItem('thiago_ultimo_doc_texto', ultimoDocumentoTexto);
                        localStorage.setItem('thiago_ultimo_doc_nombre', ultimoDocumentoNombre);
                    } catch (e) {}
                    actualizarIndicadorDocumento();
                }

                memoriaLocal.push({
                    role: 'user',
                    content: textoUsuarioVisual,
                    display: textoUsuarioVisual
                });
                memoriaLocal.push({
                    role: 'assistant',
                    content: data.reply,
                    esVerbatim: Boolean(data.is_verbatim)
                });
                guardarMemoriaLocalSegura();

                const claseExtra = data.is_verbatim ? "doc-verbatim-box" : "";
                chatBox.innerHTML += `<div class="message ai-msg ${claseExtra}">${escaparHTML(data.reply)}</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;

                respuestaPendienteDeLectura = data.speech_text || data.reply;
                esperandoConfirmacionDeVoz = true;
                solicitarPermisoLectura();

            } catch (error) {
                const nodoCarga = document.getElementById(idCarga);
                if (nodoCarga) nodoCarga.remove();
                chatBox.innerHTML += `<div class="message ai-msg error-text">⚠️ Aviso operativo: ${escaparHTML(error.message)}. Si desea leer el documento cargado de manera íntegra sin esperar al modelo, presione el botón superior "📖 Leer Documento Íntegro".</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;
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
# SECCIÓN 4: GESTIÓN DE CREDENCIALES OAUTH2 Y SERVICIOS DE GOOGLE WORKSPACE
# =============================================================================
def obtener_credenciales():
    """
    Construye y refresca las credenciales OAuth2 aplicando sanitización estricta
    de comillas y espacios residuales en las variables de entorno de Render.
    """
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
            'https://www.googleapis.com/auth/gmail.compose',
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/drive'
        ]
    )
    if not credenciales.valid:
        credenciales.refresh(Request())
    return credenciales


def construir_servicio_google(nombre_api, version_api):
    """Inicializa un cliente oficial de Google API con credenciales refrescadas."""
    credenciales = obtener_credenciales()
    return build(nombre_api, version_api, credentials=credenciales, cache_discovery=False)


# =============================================================================
# SECCIÓN 5: MOTOR UNIVERSAL DE LECTURA DOCUMENTAL, CONVERSIÓN Y OCR MULTICAPA
# =============================================================================
MARCAS_AGUA_ESCANER = [
    "anyscanner", "camscanner", "scanned with", "scanned by",
    "tapscanner", "adobe scan", "clear scanner", "fast scanner",
    "genius scan", "vflat", "microsoft lens", "office lens"
]


def es_texto_insuficiente_o_marca_agua(texto):
    """
    Verifica si el texto extraído de un documento está vacío o contiene
    únicamente marcas de agua de aplicaciones de escaneo (como AnyScanner).
    """
    if not texto:
        return True
    texto_limpio = texto.lower()
    for marca in MARCAS_AGUA_ESCANER:
        texto_limpio = texto_limpio.replace(marca, "")
    solo_alfanumericos = re.sub(r'[^a-z0-9áéíóúñü]', '', texto_limpio)
    return len(solo_alfanumericos) < 40


def normalizar_espacios_documento(texto):
    """Limpia saltos de línea excesivos preservando la estructura de párrafos."""
    if not texto:
        return ""
    texto = texto.replace('\r\n', '\n').replace('\r', '\n')
    texto = re.sub(r'[ \t]+', ' ', texto)
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    return texto.strip()


def extraer_texto_docx_completo(buffer_bytes):
    """
    Extrae el texto completo de archivos Word (.docx), recorriendo encabezados,
    párrafos principales, tablas anidadas y pies de página.
    """
    partes = []
    try:
        documento = docx.Document(io.BytesIO(buffer_bytes))

        # 1. Encabezados de sección
        for seccion in documento.sections:
            try:
                for p in seccion.header.paragraphs:
                    if p.text and p.text.strip():
                        partes.append(p.text.strip())
            except Exception:
                pass

        # 2. Párrafos del cuerpo principal
        for p in documento.paragraphs:
            if p.text and p.text.strip():
                partes.append(p.text.strip())

        # 3. Tablas (frecuentes en currículums, pliegos y certificaciones)
        for tabla in documento.tables:
            for fila in tabla.rows:
                celdas_texto = []
                for celda in fila.cells:
                    txt_celda = " ".join(
                        p.text.strip() for p in celda.paragraphs if p.text and p.text.strip()
                    )
                    if txt_celda and (not celdas_texto or txt_celda != celdas_texto[-1]):
                        celdas_texto.append(txt_celda)
                if celdas_texto:
                    partes.append(" | ".join(celdas_texto))

        # 4. Pies de página
        for seccion in documento.sections:
            try:
                for p in seccion.footer.paragraphs:
                    if p.text and p.text.strip():
                        partes.append(p.text.strip())
            except Exception:
                pass

    except Exception as error_docx:
        print(f"[AVISO EXTRACCIÓN DOCX]: {repr(error_docx)}")

    return normalizar_espacios_documento("\n".join(partes))


def extraer_texto_zip_xml(buffer_bytes, extension):
    """
    Descomprime y extrae texto directamente de contenedores basados en XML:
    OpenDocument (.odt), PowerPoint (.pptx), Excel (.xlsx) y Word (.docx).
    """
    textos = []
    try:
        with zipfile.ZipFile(io.BytesIO(buffer_bytes)) as archivo_zip:
            nombres = archivo_zip.namelist()

            if extension == '.odt' and 'content.xml' in nombres:
                raiz = ET.fromstring(archivo_zip.read('content.xml'))
                textos.extend(t.strip() for t in raiz.itertext() if t and t.strip())

            elif extension == '.pptx':
                diapositivas = sorted(
                    [n for n in nombres if n.startswith('ppt/slides/slide') and n.endswith('.xml')]
                )
                for indice, slide_name in enumerate(diapositivas, 1):
                    raiz = ET.fromstring(archivo_zip.read(slide_name))
                    txt_slide = " ".join(t.strip() for t in raiz.itertext() if t and t.strip())
                    if txt_slide:
                        textos.append(f"[Diapositiva {indice}]:\n{txt_slide}")

            elif extension == '.xlsx':
                cadenas_compartidas = []
                if 'xl/sharedStrings.xml' in nombres:
                    raiz_ss = ET.fromstring(archivo_zip.read('xl/sharedStrings.xml'))
                    for nodo_si in raiz_ss:
                        cadenas_compartidas.append("".join(t for t in nodo_si.itertext() if t))

                hojas = sorted(
                    [n for n in nombres if n.startswith('xl/worksheets/sheet') and n.endswith('.xml')]
                )
                for indice, hoja in enumerate(hojas, 1):
                    raiz_hoja = ET.fromstring(archivo_zip.read(hoja))
                    filas_texto = []
                    for elemento in raiz_hoja.iter():
                        if elemento.tag.endswith('}row') or elemento.tag == 'row':
                            valores_fila = []
                            for celda in elemento:
                                tipo_celda = celda.attrib.get('t', '')
                                valor_celda = ""
                                for sub in celda:
                                    if sub.tag.endswith('}v') or sub.tag == 'v':
                                        if tipo_celda == 's' and sub.text and sub.text.isdigit():
                                            idx_str = int(sub.text)
                                            if 0 <= idx_str < len(cadenas_compartidas):
                                                valor_celda = cadenas_compartidas[idx_str]
                                        elif sub.text:
                                            valor_celda = sub.text
                                    elif sub.tag.endswith('}is') or sub.tag == 'is':
                                        valor_celda = "".join(t for t in sub.itertext() if t)
                                if valor_celda:
                                    valores_fila.append(valor_celda.strip())
                            if valores_fila:
                                filas_texto.append(" | ".join(valores_fila))
                    if filas_texto:
                        textos.append(f"[Hoja {indice}]:\n" + "\n".join(filas_texto))

            elif extension == '.docx' and 'word/document.xml' in nombres:
                raiz = ET.fromstring(archivo_zip.read('word/document.xml'))
                textos.extend(t.strip() for t in raiz.itertext() if t and t.strip())

    except Exception as error_xml:
        print(f"[AVISO EXTRACCIÓN XML {extension}]: {repr(error_xml)}")

    return normalizar_espacios_documento("\n".join(textos))


def extraer_texto_binario_doc_o_rtf(buffer_bytes, extension):
    """
    Extractor local de respaldo para documentos binarios antiguos Word 97-2003 (.doc)
    y formato de texto enriquecido (.rtf).
    """
    try:
        if extension == '.rtf':
            contenido = buffer_bytes.decode('latin-1', errors='ignore')
            contenido = re.sub(
                r'\\([a-z]{1,32})(-?\d{1,10})?[ ]?|\\\'[0-9a-f]{2}|\\[{}]|[{}]',
                ' ',
                contenido
            )
            return normalizar_espacios_documento(contenido)

        fragmentos = []
        texto_utf16 = buffer_bytes.decode('utf-16le', errors='ignore')
        for bloque in re.findall(r'[A-Za-zÁÉÍÓÚáéíóúÑñÜü0-9 ,\.;:\-\(\)/@\n\r]{15,}', texto_utf16):
            limpio = bloque.strip()
            if len(re.findall(r'[A-Za-zÁÉÍÓÚáéíóúÑñ]{3,}', limpio)) >= 2:
                fragmentos.append(limpio)

        texto_latin = buffer_bytes.decode('cp1252', errors='ignore')
        metadatos_ruido = [
            'Microsoft Word', 'Normal.dot', 'MSWordDoc', 'Word.Document',
            'Root Entry', 'CompObj', 'SummaryInformation', 'DocumentSummaryInformation'
        ]
        for bloque in re.findall(r'[A-Za-zÁÉÍÓÚáéíóúÑñÜü0-9 ,\.;:\-\(\)/@\n\r]{20,}', texto_latin):
            limpio = bloque.strip()
            if not any(meta in limpio for meta in metadatos_ruido):
                if len(re.findall(r'[A-Za-zÁÉÍÓÚáéíóúÑñ]{3,}', limpio)) >= 3:
                    fragmentos.append(limpio)

        return normalizar_espacios_documento("\n".join(fragmentos))
    except Exception as error_bin:
        print(f"[AVISO EXTRACCIÓN BINARIA .DOC/.RTF]: {repr(error_bin)}")
        return ""


def convertir_y_ocr_con_google_drive(file_bytes=None, mime_origen="application/octet-stream", drive_file_id=None, extension=""):
    """
    Motor de Conversión y OCR en la Nube mediante Google Drive API v3:
    Convierte de manera efímera cualquier archivo (.doc, .xls, .ppt, imagen o PDF escaneado)
    en un documento nativo de Google con reconocimiento óptico de caracteres (OCR) en español,
    extrae la totalidad del texto plano y elimina el archivo temporal inmediatamente.
    """
    temp_id = None
    servicio = None
    try:
        servicio = construir_servicio_google('drive', 'v3')
        es_planilla = (
            extension in ['.xls', '.xlsx']
            or 'spreadsheet' in mime_origen
            or 'excel' in mime_origen
        )
        mime_destino = (
            'application/vnd.google-apps.spreadsheet'
            if es_planilla
            else 'application/vnd.google-apps.document'
        )
        mime_exportacion = 'text/csv' if es_planilla else 'text/plain'

        # 1. Si el archivo ya reside en Google Drive, ejecutamos copia directa con OCR
        if drive_file_id:
            try:
                meta_copia = {
                    'name': f'_thiago_temp_ocr_{int(time.time())}',
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

        # 2. Si proviene de una carga local o la copia directa falló, subimos los bytes en memoria
        if not temp_id and file_bytes:
            media = MediaIoBaseUpload(
                io.BytesIO(file_bytes),
                mimetype=mime_origen,
                resumable=False
            )
            meta_create = {
                'name': f'_thiago_temp_upload_{int(time.time())}',
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

        texto_final = exportado.decode('utf-8-sig', errors='ignore')
        return normalizar_espacios_documento(texto_final)

    except Exception as error_ocr_drive:
        print(f"[AVISO MOTOR OCR GOOGLE DRIVE]: {repr(error_ocr_drive)}")
        return ""
    finally:
        if temp_id and servicio:
            try:
                servicio.files().delete(fileId=temp_id, supportsAllDrives=True).execute()
            except Exception:
                pass


def extraer_imagenes_de_pdf_para_vision(file_bytes):
    """
    Extrae flujos de imagen crudos (/DCTDecode JPEG o PNG) incrustados dentro de
    las páginas de un archivo PDF escaneado para su transcripción mediante visión.
    """
    imagenes_b64 = []
    try:
        lector = pypdf.PdfReader(io.BytesIO(file_bytes))
        for pagina in lector.pages[:10]:
            recursos = pagina.get("/Resources", {})
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

            if not imagenes_b64:
                try:
                    for img in pagina.images:
                        if img.data and len(img.data) > 1000:
                            ext_img = "png" if img.name.lower().endswith(".png") else "jpeg"
                            b64 = base64.b64encode(img.data).decode('utf-8')
                            imagenes_b64.append(f"data:image/{ext_img};base64,{b64}")
                except Exception:
                    pass
    except Exception as error_img_pdf:
        print(f"[AVISO EXTRACCIÓN IMÁGENES PDF]: {repr(error_img_pdf)}")

    return imagenes_b64[:6]


def extraer_ocr_vision_openai(file_bytes, filename, mime_type=""):
    """
    Motor de Respaldo Multimodal con OpenAI:
    Transcribe de manera literal imágenes y documentos PDF escaneados cuando
    los motores previos no logran extraer la capa de texto.
    """
    if not OPENAI_API_KEY or not file_bytes:
        return ""

    url_api = "https://api.openai.com/v1/chat/completions"
    cabeceras = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    bloques_contenido = [
        {
            "type": "text",
            "text": (
                "Transcribe de manera íntegra, literal y exacta todo el texto visible en este documento "
                f"('{filename}'). Incluye todos los párrafos, títulos, nombres, fechas, firmas, sellos y notas. "
                "Prohibido resumir o agregar comentarios introductorios."
            )
        }
    ]

    ext = os.path.splitext((filename or "").lower())[1]
    if ext in ['.jpg', '.jpeg', '.png', '.webp'] or 'image/' in mime_type:
        mime_img = (
            mime_type
            if 'image/' in mime_type
            else f"image/{'jpeg' if ext in ['.jpg', '.jpeg'] else ext.lstrip('.')}"
        )
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
            "model": OPENAI_MODEL_MAIN,
            "messages": [{"role": "user", "content": bloques_contenido}],
            "temperature": 0.0
        }
        resp = requests.post(url_api, json=payload, headers=cabeceras, timeout=24)
        datos = resp.json()
        if "choices" in datos and datos["choices"]:
            texto = datos["choices"][0]["message"].get("content", "")
            return normalizar_espacios_documento(texto)
    except Exception as error_vision:
        print(f"[AVISO OCR VISIÓN OPENAI]: {repr(error_vision)}")

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

    # CAPA 1: Extracción nativa directa en memoria
    try:
        if ext == '.pdf' or 'pdf' in mime_lower:
            lector_pdf = pypdf.PdfReader(io.BytesIO(file_bytes))
            paginas_txt = []
            for num_pag, pagina in enumerate(lector_pdf.pages[:80], 1):
                t_pag = pagina.extract_text()
                if t_pag and t_pag.strip():
                    paginas_txt.append(t_pag.strip())
            texto_extraido = normalizar_espacios_documento("\n\n".join(paginas_txt))

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
            texto_extraido = normalizar_espacios_documento(texto_extraido)
    except Exception as error_local:
        print(f"[AVISO EXTRACCIÓN LOCAL INICIAL]: {repr(error_local)}")

    # CAPA 2: Conversión y OCR mediante Google Drive API (para .doc, .xls, .ppt, imágenes y PDFs escaneados)
    if es_texto_insuficiente_o_marca_agua(texto_extraido):
        texto_drive_ocr = convertir_y_ocr_con_google_drive(
            file_bytes=file_bytes,
            mime_origen=mime_lower,
            drive_file_id=drive_file_id,
            extension=ext
        )
        if not es_texto_insuficiente_o_marca_agua(texto_drive_ocr):
            texto_extraido = texto_drive_ocr

    # CAPA 3: Visión Artificial Multimodal con OpenAI
    if es_texto_insuficiente_o_marca_agua(texto_extraido):
        texto_vision = extraer_ocr_vision_openai(file_bytes, filename, mime_lower)
        if not es_texto_insuficiente_o_marca_agua(texto_vision):
            texto_extraido = texto_vision

    # CAPA 4: Extractor binario puro de emergencia para archivos .doc o .rtf
    if es_texto_insuficiente_o_marca_agua(texto_extraido) and (ext in ['.doc', '.rtf'] or 'msword' in mime_lower):
        texto_bin = extraer_texto_binario_doc_o_rtf(file_bytes, ext or '.doc')
        if texto_bin:
            texto_extraido = texto_bin

    texto_final = normalizar_espacios_documento(texto_extraido)[:60000]

    # Guardamos automáticamente en la caché del servidor para acceso instantáneo
    if texto_final:
        guardar_documento_en_cache(
            nombre=filename,
            texto=texto_final,
            origen="drive" if drive_file_id else "local",
            mime_type=mime_lower,
            doc_id=drive_file_id
        )

    return texto_final


# =============================================================================
# SECCIÓN 6: ENDPOINTS DE ARCHIVOS LOCALES Y CONSULTA DE CACHÉ DOCUMENTAL
# =============================================================================
@app.route('/api/upload', methods=['POST'])
def procesar_carga_archivo():
    """
    Recibe un archivo local en cualquier formato, extrae su texto íntegro
    (aplicando OCR si es necesario), lo guarda en la caché del servidor y lo retorna.
    """
    if 'file' not in request.files:
        return jsonify({
            "success": False,
            "error": "No se recibió ningún archivo en la petición."
        }), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({
            "success": False,
            "error": "El nombre del archivo está vacío."
        }), 400

    try:
        file_bytes = file.read()
        if not file_bytes:
            return jsonify({
                "success": False,
                "error": "El archivo enviado se encuentra vacío."
            }), 400

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
            "length": len(texto_extraido),
            "text": texto_extraido
        })
    except Exception as error_upload:
        print(f"[ERROR EN /api/upload]: {repr(error_upload)}")
        return jsonify({
            "success": False,
            "error": f"Error al procesar el archivo: {str(error_upload)}"
        }), 500


@app.route('/api/document/latest', methods=['GET'])
def obtener_documento_activo_endpoint():
    """Devuelve el texto íntegro del último documento almacenado en la caché del servidor."""
    doc = obtener_ultimo_documento_cache()
    if not doc:
        return jsonify({
            "success": False,
            "error": "No hay ningún documento almacenado en la caché del servidor."
        }), 404

    return jsonify({
        "success": True,
        "id": doc.get("id_documento"),
        "filename": doc.get("nombre"),
        "origin": doc.get("origen"),
        "length": doc.get("longitud_caracteres"),
        "text": doc.get("texto_integro")
    })


@app.route('/api/health', methods=['GET'])
def verificar_salud_servidor():
    """Endpoint de diagnóstico rápido para monitoreo en Render."""
    doc = obtener_ultimo_documento_cache()
    return jsonify({
        "status": "online",
        "agent": "Thiago v4.0",
        "openai_configured": bool(OPENAI_API_KEY),
        "cached_document": doc.get("nombre") if doc else None
    })


# =============================================================================
# SECCIÓN 7: SUITE DE HERRAMIENTAS AUTÓNOMAS DE GOOGLE GMAIL
# =============================================================================
def extraer_cuerpo_gmail(payload):
    """Extrae recursivamente el contenido de texto plano o HTML limpio de un mensaje de Gmail."""
    cuerpo_texto = ""
    if 'parts' in payload:
        for parte in payload['parts']:
            mime = parte.get('mimeType', '')
            if mime == 'text/plain':
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
        if not cuerpo_texto:
            for parte in payload['parts']:
                if parte.get('mimeType') == 'text/html':
                    datos = parte.get('body', {}).get('data')
                    if datos:
                        try:
                            html_crudo = base64.urlsafe_b64decode(datos).decode('utf-8', errors='ignore')
                            cuerpo_texto = re.sub(r'<[^>]+>', ' ', html_crudo)
                            break
                        except Exception:
                            pass
    elif 'body' in payload and payload['body'].get('data'):
        datos = payload['body']['data']
        try:
            cuerpo_texto = base64.urlsafe_b64decode(datos).decode('utf-8', errors='ignore')
        except Exception:
            pass

    cuerpo_limpio = normalizar_espacios_documento(cuerpo_texto)
    return cuerpo_limpio[:6000] if cuerpo_limpio else "Sin cuerpo de texto legible."


def tool_listar_correos(max_results=5, query=""):
    """Consulta los últimos correos electrónicos de la bandeja de entrada de Gmail."""
    try:
        servicio = construir_servicio_google('gmail', 'v1')
        limite = min(max(int(max_results or 5), 1), 20)
        parametros = {'userId': 'me', 'maxResults': limite}
        if query and query.strip():
            parametros['q'] = query.strip()

        resultados = servicio.users().messages().list(**parametros).execute()
        mensajes = resultados.get('messages', [])
        if not mensajes:
            return json.dumps({
                "resultado": "No se encontraron correos que coincidan con los criterios indicados."
            }, ensure_ascii=False)

        lista_correos = []
        for mensaje in mensajes:
            detalle = servicio.users().messages().get(userId='me', id=mensaje['id']).execute()
            payload = detalle.get('payload', {})
            encabezados = payload.get('headers', [])
            asunto = next((h['value'] for h in encabezados if h['name'].lower() == 'subject'), 'Sin Asunto')
            remitente = next((h['value'] for h in encabezados if h['name'].lower() == 'from'), 'Desconocido')
            fecha = next((h['value'] for h in encabezados if h['name'].lower() == 'date'), 'Fecha desconocida')
            cuerpo = extraer_cuerpo_gmail(payload)
            lista_correos.append({
                "id": mensaje['id'],
                "fecha": fecha,
                "remitente": remitente,
                "asunto": asunto,
                "cuerpo_completo": cuerpo
            })
        return json.dumps(lista_correos, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO GMAIL LISTAR]: {repr(error)}")
        return json.dumps({"error_tecnico_gmail": str(error)}, ensure_ascii=False)


def tool_enviar_correo(destinatario, asunto, cuerpo):
    """Envía un correo electrónico real a través de la infraestructura de Gmail."""
    try:
        servicio = construir_servicio_google('gmail', 'v1')
        mensaje = MIMEText(cuerpo, 'plain', 'utf-8')
        mensaje['to'] = destinatario.strip()
        mensaje['subject'] = asunto.strip()
        raw_message = base64.urlsafe_b64encode(mensaje.as_bytes()).decode('utf-8')

        enviado = servicio.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        return json.dumps({
            "resultado": "Correo enviado con éxito.",
            "destinatario": destinatario,
            "asunto": asunto,
            "id_mensaje": enviado.get('id')
        }, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO GMAIL ENVÍO]: {repr(error)}")
        return json.dumps({"error_tecnico_gmail_envio": str(error)}, ensure_ascii=False)


def tool_crear_borrador_correo(destinatario, asunto, cuerpo):
    """Crea un borrador de correo electrónico en Gmail."""
    try:
        servicio = construir_servicio_google('gmail', 'v1')
        mensaje = MIMEText(cuerpo, 'plain', 'utf-8')
        mensaje['to'] = destinatario.strip()
        mensaje['subject'] = asunto.strip()
        raw_message = base64.urlsafe_b64encode(mensaje.as_bytes()).decode('utf-8')

        borrador = servicio.users().drafts().create(
            userId='me',
            body={'message': {'raw': raw_message}}
        ).execute()
        return json.dumps({
            "resultado": "Borrador creado exitosamente en Gmail.",
            "id_borrador": borrador.get('id')
        }, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO GMAIL BORRADOR]: {repr(error)}")
        return json.dumps({"error_tecnico_gmail_borrador": str(error)}, ensure_ascii=False)


# =============================================================================
# SECCIÓN 8: SUITE DE HERRAMIENTAS AUTÓNOMAS DE GOOGLE CALENDAR
# =============================================================================
def tool_consultar_calendario(time_min=None, max_results=50):
    """Consulta los próximos eventos y compromisos agendados en Google Calendar."""
    try:
        servicio = construir_servicio_google('calendar', 'v3')
        ahora = time_min or datetime.datetime.now(timezone.utc).isoformat()
        limite = min(max(int(max_results or 50), 1), 100)

        respuesta_eventos = servicio.events().list(
            calendarId='primary',
            timeMin=ahora,
            maxResults=limite,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        eventos = respuesta_eventos.get('items', [])
        if not eventos:
            return json.dumps({
                "resultado": "No hay eventos próximos registrados en la agenda."
            }, ensure_ascii=False)

        lista_eventos = []
        for evento in eventos:
            inicio = evento['start'].get('dateTime', evento['start'].get('date'))
            fin = evento['end'].get('dateTime', evento['end'].get('date'))
            titulo = evento.get('summary', 'Sin título')
            ubicacion = evento.get('location', 'Sin ubicación')
            descripcion = evento.get('description', '')
            event_id = evento.get('id')
            lista_eventos.append({
                "id": event_id,
                "fecha_inicio": inicio,
                "fecha_fin": fin,
                "evento": titulo,
                "ubicacion": ubicacion,
                "descripcion": descripcion
            })

        return json.dumps(lista_eventos, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO CALENDAR CONSULTA]: {repr(error)}")
        return json.dumps({"error_tecnico_calendar": str(error)}, ensure_ascii=False)


def tool_crear_evento_calendario(summary, start_time, end_time, location="", description="", attendees=None):
    """
    Crea un evento en Google Calendar bloqueando de forma estricta la duplicación
    de eventos con idéntico título en la misma franja horaria.
    """
    try:
        servicio = construir_servicio_google('calendar', 'v3')

        existentes = servicio.events().list(
            calendarId='primary',
            timeMin=start_time,
            timeMax=end_time,
            q=summary,
            singleEvents=True
        ).execute().get('items', [])

        for ev in existentes:
            if ev.get('summary', '').strip().lower() == summary.strip().lower():
                return json.dumps({
                    "resultado": "El evento ya existe en el calendario en ese horario. Se ha bloqueado la duplicación.",
                    "id": ev.get('id'),
                    "link": ev.get('htmlLink')
                }, ensure_ascii=False)

        evento = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': 'America/Argentina/Buenos_Aires'
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'America/Argentina/Buenos_Aires'
            },
        }

        if attendees:
            if isinstance(attendees, list):
                evento['attendees'] = [{'email': email.strip()} for email in attendees if email.strip()]
            elif isinstance(attendees, str):
                evento['attendees'] = [{'email': email.strip()} for email in attendees.split(',') if email.strip()]

        creado = servicio.events().insert(
            calendarId='primary',
            body=evento,
            sendUpdates='all'
        ).execute()

        return json.dumps({
            "resultado": "Evento creado exitosamente en Google Calendar.",
            "id": creado.get('id'),
            "link": creado.get('htmlLink')
        }, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO CALENDAR CREACIÓN]: {repr(error)}")
        return json.dumps({"error_tecnico_calendar_creacion": str(error)}, ensure_ascii=False)


def tool_actualizar_evento_calendario(event_id, summary=None, start_time=None, end_time=None, location=None, description=None):
    """Modifica los datos o el horario de un evento existente en Google Calendar."""
    try:
        servicio = construir_servicio_google('calendar', 'v3')
        evento_actual = servicio.events().get(calendarId='primary', eventId=event_id).execute()

        if summary is not None:
            evento_actual['summary'] = summary
        if location is not None:
            evento_actual['location'] = location
        if description is not None:
            evento_actual['description'] = description
        if start_time is not None:
            evento_actual['start'] = {
                'dateTime': start_time,
                'timeZone': 'America/Argentina/Buenos_Aires'
            }
        if end_time is not None:
            evento_actual['end'] = {
                'dateTime': end_time,
                'timeZone': 'America/Argentina/Buenos_Aires'
            }

        actualizado = servicio.events().update(
            calendarId='primary',
            eventId=event_id,
            body=evento_actual,
            sendUpdates='all'
        ).execute()

        return json.dumps({
            "resultado": "Evento actualizado correctamente en Google Calendar.",
            "id": actualizado.get('id'),
            "link": actualizado.get('htmlLink')
        }, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO CALENDAR ACTUALIZACIÓN]: {repr(error)}")
        return json.dumps({"error_tecnico_calendar_actualizacion": str(error)}, ensure_ascii=False)


def tool_eliminar_evento_calendario(event_id):
    """Elimina un evento específico de Google Calendar mediante su identificador único."""
    try:
        servicio = construir_servicio_google('calendar', 'v3')
        servicio.events().delete(calendarId='primary', eventId=event_id).execute()
        return json.dumps({
            "resultado": f"Evento con ID {event_id} eliminado correctamente del calendario."
        }, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO CALENDAR ELIMINACIÓN]: {repr(error)}")
        return json.dumps({"error_tecnico_calendar_eliminacion": str(error)}, ensure_ascii=False)


# =============================================================================
# SECCIÓN 9: SUITE DE HERRAMIENTAS AUTÓNOMAS DE GOOGLE DRIVE
# =============================================================================
def tool_buscar_archivos_drive(query=""):
    """Busca archivos o carpetas en Google Drive aplicando sanitización estricta."""
    try:
        servicio = construir_servicio_google('drive', 'v3')
        consulta_limpia = (query or "").strip().replace("'", "\\'")
        condicion = (
            f"name contains '{consulta_limpia}' and trashed = false"
            if consulta_limpia
            else "trashed = false"
        )

        resultados = servicio.files().list(
            q=condicion,
            pageSize=30,
            fields="files(id, name, mimeType, parents, modifiedTime)",
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            orderBy="modifiedTime desc"
        ).execute()

        elementos = resultados.get('files', [])
        if not elementos:
            return json.dumps({
                "resultado": f"No se encontró ningún archivo con el término '{consulta_limpia}' en Google Drive."
            }, ensure_ascii=False)
        return json.dumps(elementos, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO DRIVE BÚSQUEDA]: {repr(error)}")
        return json.dumps({"error_tecnico_drive": str(error)}, ensure_ascii=False)


def tool_leer_contenido_drive(file_id):
    """
    Extrae el texto completo de cualquier archivo alojado en Google Drive
    (.doc, .docx, .pdf digitales o escaneados, hojas de cálculo, presentaciones,
    imágenes o documentos nativos), lo guarda en DOCUMENT_CACHE y lo retorna.
    """
    try:
        servicio = construir_servicio_google('drive', 'v3')
        id_limpio = (file_id or "").strip().replace("*", "")

        if len(id_limpio) < 15 or " " in id_limpio or "." in id_limpio:
            nombre_limpio = id_limpio.replace("'", "\\'")
            q_busqueda = f"name contains '{nombre_limpio}' and trashed = false"
            res_busqueda = servicio.files().list(
                q=q_busqueda,
                pageSize=5,
                fields="files(id, name, mimeType)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            archivos_encontrados = res_busqueda.get('files', [])
            if not archivos_encontrados:
                return json.dumps({
                    "error": f"No se pudo resolver el identificador en Drive para el documento: {file_id}"
                }, ensure_ascii=False)
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

        if 'application/vnd.google-apps.document' in tipo_mime:
            solicitud = servicio.files().export_media(fileId=id_real_archivo, mimeType='text/plain')
            texto_extraido = solicitud.execute().decode('utf-8-sig', errors='ignore')
            texto_extraido = normalizar_espacios_documento(texto_extraido)
            guardar_documento_en_cache(nombre_archivo, texto_extraido, "drive", tipo_mime, id_real_archivo)

        elif 'application/vnd.google-apps.spreadsheet' in tipo_mime:
            solicitud = servicio.files().export_media(fileId=id_real_archivo, mimeType='text/csv')
            texto_extraido = solicitud.execute().decode('utf-8-sig', errors='ignore')
            texto_extraido = normalizar_espacios_documento(texto_extraido)
            guardar_documento_en_cache(nombre_archivo, texto_extraido, "drive", tipo_mime, id_real_archivo)

        elif 'application/vnd.google-apps.presentation' in tipo_mime:
            solicitud = servicio.files().export_media(fileId=id_real_archivo, mimeType='text/plain')
            texto_extraido = solicitud.execute().decode('utf-8-sig', errors='ignore')
            texto_extraido = normalizar_espacios_documento(texto_extraido)
            guardar_documento_en_cache(nombre_archivo, texto_extraido, "drive", tipo_mime, id_real_archivo)

        else:
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
                "contenido": "El archivo fue abierto, pero no contiene texto extraíble ni elementos legibles por OCR."
            }, ensure_ascii=False)

        return json.dumps({
            "archivo": nombre_archivo,
            "id_documento": id_real_archivo,
            "longitud_total": len(texto_extraido),
            "contenido": texto_extraido[:28000]
        }, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO DRIVE LECTURA]: {repr(error)}")
        return json.dumps({"error_tecnico_drive_lectura": str(error)}, ensure_ascii=False)


def tool_listar_contenido_carpeta_drive(nombre_carpeta=""):
    """Busca y lista todos los archivos contenidos dentro de una carpeta de Google Drive."""
    try:
        servicio = construir_servicio_google('drive', 'v3')
        nombre_limpio = (nombre_carpeta or "").strip().replace("'", "\\'")
        query_carpeta = (
            f"name = '{nombre_limpio}' and "
            "mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        )
        res_carpeta = servicio.files().list(
            q=query_carpeta,
            pageSize=5,
            fields="files(id, name)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        carpetas = res_carpeta.get('files', [])

        if not carpetas:
            query_flex = (
                f"name contains '{nombre_limpio}' and "
                "mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            )
            res_flex = servicio.files().list(
                q=query_flex,
                pageSize=5,
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            carpetas = res_flex.get('files', [])
            if not carpetas:
                return json.dumps({
                    "resultado": f"No se encontró ninguna carpeta con el nombre '{nombre_carpeta}'."
                }, ensure_ascii=False)

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
            return json.dumps({
                "resultado": f"La carpeta '{nombre_encontrado}' existe pero se encuentra vacía."
            }, ensure_ascii=False)

        lista_elementos = []
        for hijo in hijos:
            es_carpeta = hijo.get('mimeType') == 'application/vnd.google-apps.folder'
            tipo_elem = "Carpeta" if es_carpeta else "Archivo"
            lista_elementos.append({
                "tipo": tipo_elem,
                "id": hijo.get('id'),
                "nombre": hijo.get('name'),
                "mimeType": hijo.get('mimeType')
            })

        return json.dumps({
            "carpeta_madre": nombre_encontrado,
            "elementos": lista_elementos
        }, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO LISTAR CARPETA DRIVE]: {repr(error)}")
        return json.dumps({"error_tecnico_listar_carpeta": str(error)}, ensure_ascii=False)


def tool_crear_carpeta_drive(nombre_carpeta, nombre_carpeta_padre="ACTIVIDADES"):
    """Crea una nueva carpeta en Google Drive dentro de una carpeta padre específica."""
    try:
        servicio = construir_servicio_google('drive', 'v3')
        padres = []

        if nombre_carpeta_padre and nombre_carpeta_padre.strip():
            nombre_padre_limpio = nombre_carpeta_padre.strip().replace("'", "\\'")
            q_padre = (
                f"name = '{nombre_padre_limpio}' and "
                "mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            )
            res_padre = servicio.files().list(
                q=q_padre,
                pageSize=1,
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            carpetas_padre = res_padre.get('files', [])
            if not carpetas_padre:
                return json.dumps({
                    "error": f"No se encontró la carpeta contenedora '{nombre_carpeta_padre}'."
                }, ensure_ascii=False)
            padres.append(carpetas_padre[0]['id'])

        metadata = {
            'name': nombre_carpeta.strip(),
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if padres:
            metadata['parents'] = padres

        creada = servicio.files().create(
            body=metadata,
            fields='id, name, webViewLink',
            supportsAllDrives=True
        ).execute()

        return json.dumps({
            "resultado": f"Carpeta '{nombre_carpeta}' creada con éxito.",
            "id": creada.get('id'),
            "link": creada.get('webViewLink')
        }, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO CREAR CARPETA DRIVE]: {repr(error)}")
        return json.dumps({"error_tecnico_crear_carpeta": str(error)}, ensure_ascii=False)


def tool_crear_archivo_drive(nombre_archivo, tipo_archivo="documento", nombre_carpeta_padre="", contenido_inicial=""):
    """
    Crea un nuevo archivo nativo (Documento u Hoja de Cálculo) en Google Drive,
    permitiendo inyectar contenido textual inicial si se proporciona.
    """
    try:
        servicio = construir_servicio_google('drive', 'v3')
        padres = []

        if nombre_carpeta_padre and nombre_carpeta_padre.strip():
            nombre_padre_limpio = nombre_carpeta_padre.strip().replace("'", "\\'")
            q_padre = (
                f"name = '{nombre_padre_limpio}' and "
                "mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            )
            res_padre = servicio.files().list(
                q=q_padre,
                pageSize=1,
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            carpetas_padre = res_padre.get('files', [])
            if not carpetas_padre:
                return json.dumps({
                    "error": f"No se encontró la carpeta padre '{nombre_carpeta_padre}'."
                }, ensure_ascii=False)
            padres.append(carpetas_padre[0]['id'])

        mime_types = {
            'hoja_calculo': 'application/vnd.google-apps.spreadsheet',
            'documento': 'application/vnd.google-apps.document'
        }
        mime_type_google = mime_types.get(
            (tipo_archivo or "documento").lower(),
            'application/vnd.google-apps.document'
        )

        metadata = {
            'name': nombre_archivo.strip(),
            'mimeType': mime_type_google
        }
        if padres:
            metadata['parents'] = padres

        if contenido_inicial and mime_type_google == 'application/vnd.google-apps.document':
            media = MediaIoBaseUpload(
                io.BytesIO(contenido_inicial.encode('utf-8')),
                mimetype='text/plain',
                resumable=False
            )
            creado = servicio.files().create(
                body=metadata,
                media_body=media,
                fields='id, name, webViewLink',
                supportsAllDrives=True
            ).execute()
        else:
            creado = servicio.files().create(
                body=metadata,
                fields='id, name, webViewLink',
                supportsAllDrives=True
            ).execute()

        return json.dumps({
            "resultado": f"Archivo '{nombre_archivo}' creado con éxito en Google Drive.",
            "id": creado.get('id'),
            "link": creado.get('webViewLink')
        }, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO CREAR ARCHIVO DRIVE]: {repr(error)}")
        return json.dumps({"error_tecnico_crear_archivo": str(error)}, ensure_ascii=False)


# =============================================================================
# SECCIÓN 10: BÚSQUEDA WEB ACADÉMICA, JURISPRUDENCIA Y WHATSAPP (TWILIO)
# =============================================================================
def tool_busqueda_web(query):
    """
    Realiza una búsqueda web estructurada utilizando Serper API, excluyendo
    explícitamente Wikipedia para garantizar rigor académico y jurídico.
    """
    api_key = os.getenv("SERPER_API_KEY", "").strip()
    if not api_key:
        return json.dumps({
            "error": "La clave SERPER_API_KEY no se encuentra configurada en Render."
        }, ensure_ascii=False)

    url = "https://google.serper.dev/search"
    consulta_blindada = f"{query} -site:wikipedia.org -site:es.wikipedia.org"
    payload = json.dumps({"q": consulta_blindada, "gl": "ar", "hl": "es", "num": 10})
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


def tool_buscar_jurisprudencia(tema_o_caratula, tribunal=""):
    """
    Realiza una búsqueda especializada de jurisprudencia y fallos reales en
    bases oficiales nacionales (CSJN, SAIJ, CIJ) e internacionales (Corte IDH).
    """
    filtro_tribunal = f" {tribunal}" if tribunal else " (CSJN OR \"Corte Suprema\" OR \"Corte IDH\" OR SAIJ)"
    consulta = (
        f"{tema_o_caratula}{filtro_tribunal} fallo sentencia considerando "
        "-site:wikipedia.org -site:es.wikipedia.org -site:rincondelvago.com"
    )
    return tool_busqueda_web(consulta)


def tool_enviar_whatsapp(destinatario, mensaje):
    """Envía un mensaje de WhatsApp utilizando la pasarela oficial de Twilio."""
    try:
        account_sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
        auth_token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
        twilio_from = os.getenv("TWILIO_WHATSAPP_FROM", "").strip()

        if not account_sid or not auth_token or not twilio_from:
            return json.dumps({
                "error": "Las credenciales de Twilio (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM) no están configuradas en Render."
            }, ensure_ascii=False)

        destinatario_limpio = destinatario.strip().replace(" ", "").replace("-", "").replace("+", "")
        if not destinatario_limpio.startswith("whatsapp:"):
            destinatario_formateado = f"whatsapp:+{destinatario_limpio}"
        else:
            destinatario_formateado = destinatario_limpio

        remitente_formateado = (
            twilio_from
            if twilio_from.startswith("whatsapp:")
            else f"whatsapp:{twilio_from if twilio_from.startswith('+') else '+' + twilio_from}"
        )

        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        payload = {
            'To': destinatario_formateado,
            'From': remitente_formateado,
            'Body': mensaje
        }

        response = requests.post(url, data=payload, auth=(account_sid, auth_token), timeout=15)
        response.raise_for_status()
        datos_resp = response.json()

        return json.dumps({
            "resultado": f"Mensaje de WhatsApp enviado con éxito a {destinatario}.",
            "sid": datos_resp.get("sid")
        }, ensure_ascii=False)
    except Exception as error:
        print(f"[ERROR CRÍTICO TWILIO WHATSAPP]: {repr(error)}")
        return json.dumps({"error_tecnico_whatsapp": str(error)}, ensure_ascii=False)


def tool_obtener_documento_en_memoria():
    """
    Recupera el texto completo del último documento cargado localmente o leído
    desde Drive que se encuentra alojado en la caché del servidor.
    """
    doc = obtener_ultimo_documento_cache()
    if not doc:
        return json.dumps({
            "resultado": "No hay ningún documento cargado actualmente en la memoria del servidor."
        }, ensure_ascii=False)

    return json.dumps({
        "nombre": doc.get("nombre"),
        "origen": doc.get("origen"),
        "longitud_caracteres": doc.get("longitud_caracteres"),
        "texto_integro": doc.get("texto_integro")[:30000]
    }, ensure_ascii=False)


# =============================================================================
# SECCIÓN 11: MAPEO DE HERRAMIENTAS Y ESPECIFICACIÓN JSON PARA OPENAI
# =============================================================================
available_tools = {
    "tool_listar_correos": tool_listar_correos,
    "tool_enviar_correo": tool_enviar_correo,
    "tool_crear_borrador_correo": tool_crear_borrador_correo,
    "tool_consultar_calendario": tool_consultar_calendario,
    "tool_crear_evento_calendario": tool_crear_evento_calendario,
    "tool_actualizar_evento_calendario": tool_actualizar_evento_calendario,
    "tool_eliminar_evento_calendario": tool_eliminar_evento_calendario,
    "tool_buscar_archivos_drive": tool_buscar_archivos_drive,
    "tool_leer_contenido_drive": tool_leer_contenido_drive,
    "tool_listar_contenido_carpeta_drive": tool_listar_contenido_carpeta_drive,
    "tool_crear_carpeta_drive": tool_crear_carpeta_drive,
    "tool_crear_archivo_drive": tool_crear_archivo_drive,
    "tool_busqueda_web": tool_busqueda_web,
    "tool_buscar_jurisprudencia": tool_buscar_jurisprudencia,
    "tool_enviar_whatsapp": tool_enviar_whatsapp,
    "tool_obtener_documento_en_memoria": tool_obtener_documento_en_memoria
}

openai_tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "tool_listar_correos",
            "description": "Consulta o busca correos electrónicos en la cuenta de Gmail del Prof. David Villarreal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                        "description": "Cantidad máxima de correos a recuperar (por defecto 5)."
                    },
                    "query": {
                        "type": "string",
                        "description": "Filtro opcional de búsqueda de Gmail (ej. 'from:juan' o 'asunto')."
                    }
                },
                "required": []
            }
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
                    "destinatario": {
                        "type": "string",
                        "description": "Dirección de correo electrónico del destinatario."
                    },
                    "asunto": {
                        "type": "string",
                        "description": "Asunto del mensaje."
                    },
                    "cuerpo": {
                        "type": "string",
                        "description": "Contenido textual completo del correo."
                    }
                },
                "required": ["destinatario", "asunto", "cuerpo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_crear_borrador_correo",
            "description": "Guarda un borrador de correo electrónico en Gmail.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destinatario": {"type": "string", "description": "Correo del destinatario."},
                    "asunto": {"type": "string", "description": "Asunto del borrador."},
                    "cuerpo": {"type": "string", "description": "Cuerpo del mensaje."}
                },
                "required": ["destinatario", "asunto", "cuerpo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_consultar_calendario",
            "description": "Consulta los próximos eventos y citas registrados en Google Calendar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "time_min": {
                        "type": "string",
                        "description": "Fecha y hora mínima en formato ISO 8601."
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Cantidad máxima de eventos a listar (por defecto 50)."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_crear_evento_calendario",
            "description": "Crea un evento en Google Calendar con bloqueo automático de duplicados.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Título del evento."},
                    "start_time": {"type": "string", "description": "Inicio en formato ISO 8601."},
                    "end_time": {"type": "string", "description": "Fin en formato ISO 8601."},
                    "location": {"type": "string", "description": "Ubicación física o enlace."},
                    "description": {"type": "string", "description": "Descripción o notas."},
                    "attendees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de correos electrónicos de invitados."
                    }
                },
                "required": ["summary", "start_time", "end_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_actualizar_evento_calendario",
            "description": "Actualiza un evento existente en Google Calendar dado su ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "ID único del evento."},
                    "summary": {"type": "string", "description": "Nuevo título opcional."},
                    "start_time": {"type": "string", "description": "Nueva fecha/hora de inicio ISO."},
                    "end_time": {"type": "string", "description": "Nueva fecha/hora de fin ISO."},
                    "location": {"type": "string", "description": "Nueva ubicación."},
                    "description": {"type": "string", "description": "Nueva descripción."}
                },
                "required": ["event_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_eliminar_evento_calendario",
            "description": "Elimina un evento de Google Calendar por su ID único.",
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
            "name": "tool_leer_contenido_drive",
            "description": "Extrae el texto completo de cualquier archivo en Google Drive (.pdf digital o escaneado, .doc, .docx, .xls, .xlsx, .ppt, .pptx, imágenes o Google Docs) dado su ID o su nombre.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_id": {
                        "type": "string",
                        "description": "ID único o nombre exacto del archivo en Google Drive."
                    }
                },
                "required": ["file_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_listar_contenido_carpeta_drive",
            "description": "Busca una carpeta por su nombre en Google Drive y lista todos sus archivos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_carpeta": {"type": "string", "description": "Nombre de la carpeta."}
                },
                "required": ["nombre_carpeta"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_crear_carpeta_drive",
            "description": "Crea una carpeta nueva en Google Drive.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_carpeta": {"type": "string", "description": "Nombre de la carpeta a crear."},
                    "nombre_carpeta_padre": {"type": "string", "description": "Nombre de la carpeta padre."}
                },
                "required": ["nombre_carpeta"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_crear_archivo_drive",
            "description": "Crea un documento o planilla nativa en Google Drive con contenido opcional.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_archivo": {"type": "string", "description": "Nombre del archivo."},
                    "tipo_archivo": {
                        "type": "string",
                        "enum": ["hoja_calculo", "documento"],
                        "description": "Tipo de archivo."
                    },
                    "nombre_carpeta_padre": {"type": "string", "description": "Carpeta de destino opcional."},
                    "contenido_inicial": {"type": "string", "description": "Texto opcional para insertar."}
                },
                "required": ["nombre_archivo", "tipo_archivo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_busqueda_web",
            "description": "Realiza una búsqueda oficial en internet excluyendo Wikipedia.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Consulta de búsqueda."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_buscar_jurisprudencia",
            "description": "Busca fallos judiciales reales y sentencias de tribunales nacionales e internacionales.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tema_o_caratula": {"type": "string", "description": "Carátula o tema jurídico."},
                    "tribunal": {"type": "string", "description": "Tribunal específico opcional (ej. CSJN, Corte IDH)."}
                },
                "required": ["tema_o_caratula"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_enviar_whatsapp",
            "description": "Envía un mensaje de WhatsApp mediante Twilio.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destinatario": {"type": "string", "description": "Número con código de país (ej. +54911...)."},
                    "mensaje": {"type": "string", "description": "Texto del mensaje."}
                },
                "required": ["destinatario", "mensaje"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tool_obtener_documento_en_memoria",
            "description": "Recupera el texto íntegro del último documento cargado o leído que permanece en la caché del servidor.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


# =============================================================================
# SECCIÓN 12: CONTROLADORES PRINCIPALES Y LOOP COGNITIVO ANTI-TIMEOUT
# =============================================================================
@app.route("/")
def index():
    """Renderiza la interfaz gráfica principal del Núcleo Central de Thiago."""
    return render_template_string(HTML_TEMPLATE)


@app.route("/webhook/whatsapp", methods=["POST"])
def webhook_whatsapp_entrante():
    """
    Endpoint receptor (Webhook) para mensajes entrantes de WhatsApp vía Twilio.
    Permite la comunicación bidireccional con Thiago desde el teléfono móvil.
    """
    try:
        remitente = request.form.get("From", "")
        cuerpo_mensaje = request.form.get("Body", "").strip()
        if not cuerpo_mensaje:
            return Response("<Response></Response>", mimetype="text/xml")

        respuesta_texto = procesar_consulta_autonoma_interna(cuerpo_mensaje, [])
        respuesta_escapada = (
            respuesta_texto[:1500]
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        twiml = f"<Response><Message>{respuesta_escapada}</Message></Response>"
        return Response(twiml, mimetype="text/xml")
    except Exception as err_wh:
        print(f"[ERROR WEBHOOK WHATSAPP]: {repr(err_wh)}")
        return Response("<Response></Response>", mimetype="text/xml")


def procesar_consulta_autonoma_interna(mensaje_usuario, historial_cliente, directiva_cruda=""):
    """
    Ejecuta el ciclo cognitivo con control de tiempo estricto (< 24 segundos)
    para evitar que Gunicorn en Render corte el proceso con un error 502.
    """
    inicio_reloj = time.time()
    doc_en_cache = obtener_ultimo_documento_cache()

    # 1. INTERCEPTOR EN SERVIDOR: Si el usuario pide lectura literal y existe documento en caché
    texto_evaluar = directiva_cruda or mensaje_usuario
    if solicita_lectura_literal_directa(texto_evaluar) and doc_en_cache:
        nombre_doc = doc_en_cache.get("nombre", "Documento")
        texto_integro = doc_en_cache.get("texto_integro", "")
        encabezado = (
            f"📄 TRANSCRIPCIÓN LITERAL E ÍNTEGRA DEL DOCUMENTO: \"{nombre_doc}\"\n"
            f"══════════════════════════════════════════════════════════════════\n\n"
        )
        return encabezado + texto_integro

    if not OPENAI_API_KEY:
        return "Falta configurar la clave OPENAI_API_KEY en las variables de entorno de Render."

    ahora_bsas = datetime.datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-3)))
    fecha_str = ahora_bsas.strftime('%A, %d de %B de %Y, %H:%M:%S')

    nota_cache = ""
    if doc_en_cache:
        nota_cache = (
            f"\n\nDOCUMENTO ACTIVO EN CACHÉ DEL SERVIDOR: Actualmente tienes cargado en memoria el documento "
            f"'{doc_en_cache.get('nombre')}' ({doc_en_cache.get('longitud_caracteres')} caracteres). "
            "Si el profesor te formula preguntas sobre el documento anterior o pide analizarlo y no ves el texto "
            "en el mensaje actual, invoca 'tool_obtener_documento_en_memoria' o responde con base en su contenido."
        )

    instruccion_dinamica = (
        SYSTEM_INSTRUCTION
        + f"\n\nINFORMACIÓN TEMPORAL OBLIGATORIA: Hoy es {fecha_str} (Hora oficial de Buenos Aires, Argentina)."
        + nota_cache
    )

    mensajes_api = [{"role": "system", "content": instruccion_dinamica}]

    for msg in (historial_cliente or [])[-8:]:
        rol = msg.get("role")
        contenido = msg.get("content", "")
        if rol in ["user", "assistant"] and contenido:
            # Evitamos acumular múltiples volcados gigantescos en el contexto de entrada
            if len(contenido) > 4500:
                contenido = contenido[:4500] + "\n...[Contenido extenso resguardado en caché]..."
            mensajes_api.append({"role": rol, "content": contenido})

    # Si el mensaje actual no trae el texto del documento pero hace referencia a él,
    # inyectamos un extracto amplio desde la caché del servidor para que el modelo tenga contexto inmediato.
    if doc_en_cache and "[Se adjunta el archivo:" not in mensaje_usuario:
        palabras_doc = ["documento", "archivo", "plancha", "certificado", "cv", "texto", "leíste", "anterior"]
        if any(p in mensaje_usuario.lower() for p in palabras_doc):
            extracto_cache = doc_en_cache.get("texto_integro", "")[:22000]
            mensaje_usuario = (
                f"[Contexto documental activo en caché: {doc_en_cache.get('nombre')}]\n"
                f"{extracto_cache}\n\n"
                f"Directiva del Profesor:\n{mensaje_usuario}"
            )

    mensajes_api.append({"role": "user", "content": mensaje_usuario})

    url_api = "https://api.openai.com/v1/chat/completions"
    cabeceras = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    texto_respuesta = ""
    for iteracion in range(4):
        # Protección anti-timeout de Render (si superamos 22 segundos, cerramos el bucle de forma limpia)
        tiempo_transcurrido = time.time() - inicio_reloj
        if tiempo_transcurrido > 22.0 and iteracion > 0:
            break

        timeout_restante = max(8.0, 25.0 - tiempo_transcurrido)
        payload_inicial = {
            "model": OPENAI_MODEL_MAIN,
            "messages": mensajes_api,
            "tools": openai_tools_definition,
            "tool_choice": "auto",
            "temperature": 0.1
        }

        respuesta = requests.post(
            url_api,
            json=payload_inicial,
            headers=cabeceras,
            timeout=timeout_restante
        )
        respuesta_json = respuesta.json()

        if "choices" in respuesta_json and respuesta_json["choices"]:
            mensaje_respuesta = respuesta_json["choices"][0]["message"]

            if "tool_calls" in mensaje_respuesta and mensaje_respuesta["tool_calls"]:
                mensajes_api.append(mensaje_respuesta)
                for llamada_herramienta in mensaje_respuesta["tool_calls"]:
                    nombre_funcion = llamada_herramienta["function"]["name"]
                    try:
                        argumentos_funcion = json.loads(
                            llamada_herramienta["function"].get("arguments") or "{}"
                        )
                    except Exception:
                        argumentos_funcion = {}

                    try:
                        if nombre_funcion in available_tools:
                            resultado_ejecucion = available_tools[nombre_funcion](**argumentos_funcion)
                        else:
                            resultado_ejecucion = json.dumps({
                                "error": f"La herramienta '{nombre_funcion}' no está registrada."
                            }, ensure_ascii=False)
                    except Exception as tool_err:
                        print(f"[ERROR EN TOOL {nombre_funcion}]: {repr(tool_err)}")
                        resultado_ejecucion = json.dumps({
                            "error_ejecucion": str(tool_err)
                        }, ensure_ascii=False)

                    # Si la herramienta fue tool_leer_contenido_drive y el usuario pidió lectura literal,
                    # devolvemos directamente el texto íntegro recién guardado en la caché sin resumir.
                    if nombre_funcion == "tool_leer_contenido_drive" and solicita_lectura_literal_directa(texto_evaluar):
                        doc_actualizado = obtener_ultimo_documento_cache()
                        if doc_actualizado and doc_actualizado.get("texto_integro"):
                            encabezado_drive = (
                                f"📄 LECTURA ÍNTEGRA Y LITERAL DEL ARCHIVO DE DRIVE: \"{doc_actualizado.get('nombre')}\"\n"
                                f"══════════════════════════════════════════════════════════════════\n\n"
                            )
                            return encabezado_drive + doc_actualizado.get("texto_integro")

                    mensajes_api.append({
                        "role": "tool",
                        "tool_call_id": llamada_herramienta["id"],
                        "content": resultado_ejecucion
                    })
                continue
            else:
                texto_respuesta = mensaje_respuesta.get("content") or "Directiva ejecutada con éxito."
                break
        else:
            detalle_err = respuesta_json.get("error", {}).get("message", str(respuesta_json))
            texto_respuesta = f"Aviso del proveedor cognitivo: {detalle_err}"
            break

    if not texto_respuesta:
        doc_final = obtener_ultimo_documento_cache()
        if doc_final and solicita_lectura_literal_directa(texto_evaluar):
            return doc_final.get("texto_integro")
        texto_respuesta = (
            "Se ha completado el procesamiento de las herramientas solicitadas. "
            "Si desea visualizar o escuchar el documento completo sin resumir, "
            "presione el botón superior '📖 Leer Documento Íntegro'."
        )

    return texto_respuesta


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Controlador principal del agente autónomo.
    Coordina la memoria liviana del cliente, la caché documental del servidor
    y el interceptor de lectura literal.
    """
    datos_solicitud = request.get_json(silent=True) or {}
    mensaje_usuario = (datos_solicitud.get("message") or "").strip()
    directiva_cruda = (datos_solicitud.get("raw_directive") or mensaje_usuario).strip()
    historial_cliente = datos_solicitud.get("history") or []

    if not mensaje_usuario:
        return jsonify({"reply": "Por favor, indique una directiva operativa válida."})

    try:
        es_lectura_literal = solicita_lectura_literal_directa(directiva_cruda)
        texto_respuesta = procesar_consulta_autonoma_interna(
            mensaje_usuario=mensaje_usuario,
            historial_cliente=historial_cliente,
            directiva_cruda=directiva_cruda
        )

        doc_activo = obtener_ultimo_documento_cache()
        info_doc_activo = None
        if doc_activo:
            info_doc_activo = {
                "filename": doc_activo.get("nombre"),
                "length": doc_activo.get("longitud_caracteres"),
                "text": doc_activo.get("texto_integro")
            }

        return jsonify({
            "reply": texto_respuesta,
            "is_verbatim": es_lectura_literal,
            "speech_text": doc_activo.get("texto_integro") if (es_lectura_literal and doc_activo) else texto_respuesta,
            "active_document": info_doc_activo
        })
    except Exception as error_critico:
        print(f"[ERROR CRÍTICO CHAT GENERAL]: {repr(error_critico)}")
        doc_respaldo = obtener_ultimo_documento_cache()
        if doc_respaldo and solicita_lectura_literal_directa(directiva_cruda):
            return jsonify({
                "reply": doc_respaldo.get("texto_integro"),
                "is_verbatim": True,
                "speech_text": doc_respaldo.get("texto_integro")
            })
        return jsonify({
            "reply": f"Error operativo controlado: {str(error_critico)}"
        })


if __name__ == "__main__":
    puerto = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=puerto)
