# -*- coding: utf-8 -*-
"""
Núcleo Central de Thiago - Interfaz Web con Corrección Fonética y Síntesis en Español.
Diseñado para el Prof. David Villarreal.
"""

from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

PILARES_THIAGO = {
    "1": ("secretario", "Gestión administrativa, correos y flujos de Google Workspace", "secretario"),
    "2": ("abogado", "Derecho, jurisprudencia, fallos y normas APA", "abogado"),
    "3": ("masoneria", "Organización estratégica y principios masónicos", "masonería"),
    "4": ("religion", "Ifa tradicional yoruba y Batuque Isesa", "religión"),
    "5": ("investigacion", "Relaciones internacionales, doctorado e investigación", "investigación"),
    "6": ("docencia ingles", "Material didáctico interactivo y enseñanza de inglés", "docencia en inglés"),
    "7": ("docencia derecho", "Pedagogía jurídica y contenidos especializados", "docencia en derecho")
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Núcleo de Thiago - Asistente Estratégico</title>
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --accent: #38bdf8;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
        }
        .container {
            width: 100%;
            max-width: 800px;
            background: var(--card-bg);
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        }
        h1 {
            color: var(--accent);
            text-align: center;
            font-size: 1.8rem;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            color: var(--text-muted);
            margin-bottom: 25px;
            font-size: 0.95rem;
        }
        .chat-box {
            background: #090d16;
            border: 1px solid #334155;
            border-radius: 8px;
            height: 350px;
            overflow-y: auto;
            padding: 15px;
            margin-bottom: 20px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .message {
            padding: 10px 14px;
            border-radius: 8px;
            max-width: 80%;
            line-height: 1.4;
        }
        .user-msg {
            background: #0284c7;
            color: white;
            align-self: flex-end;
        }
        .ai-msg {
            background: #334155;
            color: #f1f5f9;
            align-self: flex-start;
        }
        .input-group {
            display: flex;
            gap: 10px;
        }
        input[type="text"] {
            flex: 1;
            padding: 12px;
            border-radius: 6px;
            border: 1px solid #475569;
            background: #0f172a;
            color: white;
            font-size: 1rem;
        }
        button {
            padding: 12px 20px;
            background-color: var(--accent);
            color: #0f172a;
            border: none;
            border-radius: 6px;
            font-weight: bold;
            cursor: pointer;
            transition: background 0.2s;
        }
        button:hover {
            background-color: #7dd3fc;
        }
        .status {
            text-align: center;
            margin-top: 15px;
            font-size: 0.85rem;
            color: var(--text-muted);
        }
    </style>
</head>
<body>

    <div class="container">
        <h1>Núcleo Central de Thiago</h1>
        <div class="subtitle">Prof. David Villarreal — Interfaz Estratégica Multidisciplinaria</div>
        
        <div class="chat-box" id="chatBox">
            <div class="message ai-msg">Hola, profesor David. El núcleo se encuentra operativo. ¿En qué área estratégica trabajaremos hoy?</div>
        </div>

        <div class="input-group">
            <input type="text" id="userInput" placeholder="Escriba su consulta o instrucción..." autofocus>
            <button onclick="enviarMensaje()">Enviar</button>
        </div>
        
        <div class="status">Sistema Activo | Motor Fonético en Español (es-ES) Configurado</div>
    </div>

    <script>
        // Carga previa de voces del navegador para asegurar compatibilidad de síntesis en español
        let synthVoices = [];
        function cargarVoces() {
            synthVoices = window.speechSynthesis.getVoices();
        }
        cargarVoces();
        if (window.speechSynthesis.onvoiceschanged !== undefined) {
            window.speechSynthesis.onvoiceschanged = cargarVoces;
        }

        function hablarTexto(texto) {
            if (!('speechSynthesis' in window)) return;
            
            window.speechSynthesis.cancel(); // Detiene cualquier audio previo
            const utterance = new SpeechSynthesisUtterance(texto);
            
            // Configuración estricta para español y acentos correctos
            utterance.lang = 'es-ES';
            utterance.rate = 1.0;
            utterance.pitch = 1.0;

            // Busca una voz nativa en español disponible en el sistema del usuario
            const voiceEs = synthVoices.find(v => v.lang.startsWith('es') || v.lang.includes('ES'));
            if (voiceEs) {
                utterance.voice = voiceEs;
            }

            window.speechSynthesis.speak(utterance);
        }

        async function enviarMensaje() {
            const input = document.getElementById('userInput');
            const chatBox = document.getElementById('chatBox');
            const texto = input.value.trim();

            if (!texto) return;

            // Mostrar mensaje del usuario
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
                
                // Mostrar respuesta de la IA
                chatBox.innerHTML += `<div class="message ai-msg">${data.reply}</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;

                // Ejecutar síntesis de voz corregida en español
                hablarTexto(data.reply);

            } catch (error) {
                chatBox.innerHTML += `<div class="message ai-msg" style="color:#f87171;">Error de comunicación con el núcleo.</div>`;
            }
        }

        document.getElementById('userInput').addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                enviarMensaje();
            }
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
    user_message = data.get("message", "").lower()
    
    # Procesamiento inteligente básico basado en los pilares del profesor
    respuesta = f"Profesor David, he procesado su directiva: '{user_message}'. El sistema opera con normalidad y los parámetros académicos y fonéticos se encuentran listos."
    
    if "abogado" in user_message or "derecho" in user_message:
        respuesta = "Módulo Jurídico Activo: Analizando bajo normativas de rigor, jurisprudencia y directrices APA solicitadas."
    elif "ingles" in user_message or "english" in user_message:
        respuesta = "Módulo Docente de Inglés Activo: Preparado para estructurar material interactivo de alta retención."
    elif "ifa" in user_message or "yoruba" in user_message or "religión" in user_message:
        respuesta = "Módulo Tradicional Activo: Resguardando los principios y fundamentos de Ifá tradicional yoruba y Batuque Isesa."

    return jsonify({"reply": respuesta})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
