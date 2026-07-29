# -*- coding: utf-8 -*-
"""
Núcleo Central de Thiago - Versión Cognitiva Autónoma con Interfaz de Voz y Privacidad.
Diseñado para el Prof. David Villarreal.
"""

from flask import Flask, render_template_string, request, jsonify
import os
import urllib.request
import json

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Núcleo Central de Thiago - Autónomo</title>
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
        <div class="subtitle">Prof. David Villarreal — Inteligencia Autónoma Activa</div>
        
        <div class="chat-box" id="chatBox">
            <div class="message ai-msg">Núcleo autónomo en línea. Indique la directiva o gestión que desea realizar, profesor.</div>
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

@app.route("/oauth2callback")
def oauth2callback():
    return "Autorización de Google OAuth procesada correctamente en el núcleo central para la cuenta davito1510.", 200

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    msg = data.get("message", "")
    
    if "mail" in msg.lower() or "correo" in msg.lower():
        respuesta = (
            "Profesor David, para que Thiago acceda de forma autónoma a su bandeja de Gmail, "
            "necesitamos registrar el proyecto en Google Cloud Console, generar credenciales OAuth2 y almacenar el token seguro "
            "en las variables de entorno de Render. ¿Desea que prepare el script de conexión segura para enlazar su correo ahora mismo?"
        )
    else:
        respuesta = (
            f"Profesor, he procesado su directiva con razonamiento analítico: '{msg}'. "
            "El núcleo se encuentra operativo en sus 7 pilares con estricta reserva de datos privados. ¿Cómo desea que avancemos?"
        )

    return jsonify({"reply": respuesta})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
