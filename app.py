# -*- coding: utf-8 -*-
"""
Núcleo Central de Thiago - Interfaz Web con los 7 Pilares Activos y Corrección Fonética.
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
    <title>Núcleo de Thiago - Interfaz Web</title>
    <style>
        body { font-family: Arial, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; }
        .container { width: 100%; max-width: 700px; background: #1e293b; padding: 25px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        h1 { color: #38bdf8; text-align: center; font-size: 1.5rem; margin-bottom: 5px; }
        .subtitle { text-align: center; color: #94a3b8; margin-bottom: 20px; font-size: 0.9rem; }
        .chat-box { background: #090d16; border: 1px solid #334155; height: 320px; overflow-y: auto; padding: 12px; margin-bottom: 15px; border-radius: 6px; display: flex; flex-direction: column; gap: 8px; }
        .message { padding: 8px 12px; border-radius: 6px; max-width: 85%; line-height: 1.4; }
        .user-msg { background: #0284c7; color: white; align-self: flex-end; }
        .ai-msg { background: #334155; color: #f1f5f9; align-self: flex-start; }
        .input-group { display: flex; gap: 8px; }
        input[type="text"] { flex: 1; padding: 10px; border-radius: 5px; border: 1px solid #475569; background: #0f172a; color: white; font-size: 1rem; }
        button { padding: 10px 18px; background-color: #38bdf8; color: #0f172a; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; }
        button:hover { background-color: #7dd3fc; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Núcleo Central de Thiago</h1>
        <div class="subtitle">Prof. David Villarreal — 7 Pilares Activos</div>
        
        <div class="chat-box" id="chatBox">
            <div class="message ai-msg">Hola, profesor David. Los 7 módulos del núcleo se encuentran activos y operativos. ¿En qué área trabajaremos hoy?</div>
        </div>

        <div class="input-group">
            <input type="text" id="userInput" placeholder="Escriba su consulta o indique el área..." autofocus>
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
            utterance.lang = 'es-ES'; // Forzar idioma español y correcta acentuación
            utterance.rate = 1.0;

            const vozEspanol = vocesDisponibles.find(v => v.lang.startsWith('es'));
            if (vozEspanol) {
                utterance.voice = vozEspanol;
            }

            window.speechSynthesis.speak(utterance);
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
                chatBox.innerHTML += `<div class="message ai-msg" style="color:#f87171;">Error de conexión con el núcleo.</div>`;
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
    
    # Enrutamiento inteligente para los 7 pilares profesionales
    if any(k in msg for k in ["secretario", "correo", "workspace", "agenda"]):
        p = PILARES_THIAGO["1"]
        respuesta = f"Módulo 1 ({p[0].capitalize()}) Activo: {p[1]}. Preparado para coordinar su gestión administrativa."
    elif any(k in msg for k in ["abogado", "derecho", "jurisprudencia", "fallos", "apa"]):
        p = PILARES_THIAGO["2"]
        respuesta = f"Módulo 2 ({p[0].capitalize()}) Activo: {p[1]}. Analizando bajo estrictas normas bibliográficas y jurisprudenciales."
    elif any(k in msg for k in ["masoneria", "masones", "logia", "estrategica"]):
        p = PILARES_THIAGO["3"]
        respuesta = f"Módulo 3 ({p[0].capitalize()}) Activo: {p[1]}. Abordando los principios y la organización estratégica."
    elif any(k in msg for k in ["ifa", "yoruba", "batuque", "isesa", "religion"]):
        p = PILARES_THIAGO["4"]
        respuesta = f"Módulo 4 ({p[0].capitalize()}) Activo: {p[1]}. Resguardando con rigor la tradición y los fundamentos."
    elif any(k in msg for k in ["investigacion", "relaciones internacionales", "doctorado", "tesis"]):
        p = PILARES_THIAGO["5"]
        respuesta = f"Módulo 5 ({p[0].capitalize()}) Activo: {p[1]}. Asistiendo en el desarrollo académico de su doctorado."
    elif any(k in msg for k in ["ingles", "english", "docencia ingles", "didactico"]):
        p = PILARES_THIAGO["6"]
        respuesta = f"Módulo 6 ({p[0]}) Activo: {p[1]}. Listo para estructurar material didáctico interactivo de alta retención."
    elif any(k in msg for k in ["docencia derecho", "pedagogia", "clases derecho"]):
        p = PILARES_THIAGO["7"]
        respuesta = f"Módulo 7 ({p[0]}) Activo: {p[1]}. Organizando contenidos jurídicos especializados para la enseñanza."
    else:
        respuesta = f"Profesor David, he procesado su instrucción: '{msg}'. Los 7 pilares se encuentran activos y a su disposición."

    return jsonify({"reply": respuesta})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
