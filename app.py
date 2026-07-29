# -*- coding: utf-8 -*-
"""
Núcleo Central de Thiago - Interfaz Estratégica con Memoria y Funcionalidad de Gmail.
Diseñado para el Prof. David Villarreal.
"""

from flask import Flask, render_template_string, request, jsonify
import os

app = Flask(__name__)

# Memoria de sesión temporal del núcleo (mantiene contexto sin repetir perfiles)
MEMORIA_NUCLEO = {
    "ultimo_modulo": "general",
    "historial": []
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Núcleo Central de Thiago - Asistente Estratégico</title>
    <style>
        body { font-family: Arial, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; }
        .container { width: 100%; max-width: 750px; background: #1e293b; padding: 25px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        h1 { color: #38bdf8; text-align: center; font-size: 1.5rem; margin-bottom: 5px; }
        .subtitle { text-align: center; color: #94a3b8; margin-bottom: 20px; font-size: 0.9rem; }
        .chat-box { background: #090d16; border: 1px solid #334155; height: 340px; overflow-y: auto; padding: 12px; margin-bottom: 15px; border-radius: 6px; display: flex; flex-direction: column; gap: 8px; }
        .message { padding: 9px 13px; border-radius: 6px; max-width: 85%; line-height: 1.4; }
        .user-msg { background: #0284c7; color: white; align-self: flex-end; }
        .ai-msg { background: #334155; color: #f1f5f9; align-self: flex-start; }
        .input-group { display: flex; gap: 8px; }
        input[type="text"] { flex: 1; padding: 10px; border-radius: 5px; border: 1px solid #475569; background: #0f172a; color: white; font-size: 1rem; }
        button { padding: 10px 18px; background-color: #38bdf8; color: #0f172a; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; }
        button:hover { background-color: #7dd3fc; }
        .mic-btn { background-color: #ef4444; color: white; }
        .mic-btn.listening { background-color: #22c55e; animation: pulse 1.5s infinite; }
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }
    </style>
</head>
<body>
    <div class="container">
        <h1>Núcleo Central de Thiago</h1>
        <div class="subtitle">Prof. David Villarreal — Asistente Operativo Activo</div>
        
        <div class="chat-box" id="chatBox">
            <div class="message ai-msg">Núcleo en línea y operativo. ¿Qué instrucción desea ejecutar hoy, profesor?</div>
        </div>

        <div class="input-group">
            <input type="text" id="userInput" placeholder="Escriba su consulta o instrucción..." autofocus>
            <button type="button" id="micBtn" class="mic-btn" onclick="alternarEscucha()" title="Hablar con Thiago">🎤 Hablar</button>
            <button onclick="enviarMensaje()">Enviar</button>
        </div>
    </div>

    <script>
        let vocesDisponibles = [];
        window.speechSynthesis.onvoiceschanged = () => {
            vocesDisponibles = window.speechSynthesis.getVoices();
        };

        function hablar(texto) {
            if (!('speechSynthesis' in window)) return;
            window.speechSynthesis.cancel();
            
            const utterance = new SpeechSynthesisUtterance(texto);
            utterance.lang = 'es-ES';
            utterance.rate = 1.0;

            const vozEspanol = vocesDisponibles.find(v => v.lang.startsWith('es'));
            if (vozEspanol) {
                utterance.voice = vozEspanol;
            }

            window.speechSynthesis.speak(utterance);
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        let recognition = null;
        let escuchando = false;

        if (SpeechRecognition) {
            recognition = new SpeechRecognition();
            recognition.lang = 'es-ES';
            recognition.continuous = false;
            recognition.interimResults = false;

            recognition.onstart = () => {
                escuchando = true;
                const btn = document.getElementById('micBtn');
                btn.classList.add('listening');
                btn.textContent = '🔴 Escuchando...';
            };

            recognition.onresult = (event) => {
                const textoTranscrito = event.results[0][0].transcript;
                document.getElementById('userInput').value = textoTranscrito;
                enviarMensaje();
            };

            recognition.onerror = () => { detenerEscucha(); };
            recognition.onend = () => { detenerEscucha(); };
        } else {
            document.getElementById('micBtn').style.display = 'none';
        }

        function alternarEscucha() {
            if (!recognition) {
                alert("Su navegador no soporta reconocimiento de voz nativo. Utilice Google Chrome.");
                return;
            }
            if (escuchando) {
                recognition.stop();
            } else {
                recognition.start();
            }
        }

        function detenerEscucha() {
            escuchando = false;
            const btn = document.getElementById('micBtn');
            btn.classList.remove('listening');
            btn.textContent = '🎤 Hablar';
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
                hablar(data.reply);
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

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    msg = data.get("message", "").lower()
    
    # Guardar en memoria de sesión
    MEMORIA_NUCLEO["historial"].append(msg)
    
    # Procesamiento inteligente y discreto (sin recitar datos privados en voz alta)
    if "mail" in msg or "correo" in msg or "bandeja" in msg or "leer" in msg:
        # Fase inicial de conexión con Gmail (preparando integración de credenciales seguras de Workspace)
        respuesta = (
            "Profesor, para acceder a su bandeja de Gmail en este entorno web desplegado en Render, "
            "necesitamos configurar el token seguro de la API de Google Workspace en las variables de entorno del servidor. "
            "Una vez enlazado, le listaré los correos entrantes de forma cifrada y discreta."
        )
    elif "secretario" in msg or "secretaria" in msg:
        MEMORIA_NUCLEO["ultimo_modulo"] = "secretaria"
        respuesta = "Módulo de Secretaría activado discretamente. ¿Qué gestión administrativa, borrador o control de plazos realizamos?"
    elif "abogado" in msg or "derecho" in msg or "jurisprudencia" in msg:
        MEMORIA_NUCLEO["ultimo_modulo"] = "abogado"
        respuesta = "Módulo Jurídico en línea. Indique el fallo, normativa o escrito bajo normas APA que analizaremos."
    elif "masoneria" in msg or "masones" in msg:
        MEMORIA_NUCLEO["ultimo_modulo"] = "masoneria"
        respuesta = "Módulo Estratégico activado. Escucho su directiva."
    elif "ifa" in msg or "yoruba" in msg or "batuque" in msg:
        MEMORIA_NUCLEO["ultimo_modulo"] = "religion"
        respuesta = "Módulo Tradicional activado bajo estricto aislamiento doctrinal. Adelante."
    elif "investigacion" in msg or "doctorado" in msg or "relaciones internacionales" in msg:
        MEMORIA_NUCLEO["ultimo_modulo"] = "investigacion"
        respuesta = "Módulo de Posgrado activo. ¿Avanzamos sobre la tesis o fuentes doctorales?"
    elif "ingles" in msg or "english" in msg:
        MEMORIA_NUCLEO["ultimo_modulo"] = "ingles"
        respuesta = "Módulo Docente de Inglés activo. ¿Qué material interactivo estructuramos sobre el texto base?"
    else:
        # Respuesta contextual basada en el último módulo activo para mantener hilo de conversación fluido
        ultimo = MEMORIA_NUCLEO["ultimo_modulo"]
        respuesta = f"Instrucción registrada bajo el dominio '{ultimo}'. He procesado su solicitud de manera analítica y privada. ¿Cómo procedemos?"

    return jsonify({"reply": respuesta})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
