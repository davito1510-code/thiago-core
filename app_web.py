# -*- coding: utf-8 -*-
"""
Núcleo Central de Thiago - Interfaz Web con Corrección Fonética.
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
    <title>Núcleo de Thiago - Interfaz Web</title>
    <style>
        body { background-color: #121212; color: #e0e0e0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; margin-top: 40px; }
        .container { max-width: 650px; margin: auto; background: #1e1e1e; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        h1 { color: #4CAF50; font-size: 24px; }
        .btn { display: block; width: 100%; margin: 10px 0; padding: 12px; background: #333; color: #fff; border: 1px solid #444; border-radius: 6px; cursor: pointer; font-size: 16px; text-align: left; }
        .btn:hover { background: #4CAF50; color: #000; font-weight: bold; }
        #output { margin-top: 20px; font-size: 18px; color: #ffeb3b; background: #252525; padding: 15px; border-radius: 6px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>NÚCLEO DE THIAGO - MENÚ ACTIVO</h1>
        <p>Seleccione un perfil profesional para activar el núcleo:</p>
        
        <button class="btn" onclick="activarPerfil('1', 'secretario', 'secretario')">[1] SECRETARIO: Gestión administrativa, correos y flujos de Google Workspace</button>
        <button class="btn" onclick="activarPerfil('2', 'abogado', 'abogado')">[2] ABOGADO: Derecho, jurisprudencia, fallos y normas APA</button>
        <button class="btn" onclick="activarPerfil('3', 'masoneria', 'masonería')">[3] MASONERIA: Organización estratégica y principios masónicos</button>
        <button class="btn" onclick="activarPerfil('4', 'religion', 'religión')">[4] RELIGION: Ifa tradicional yoruba y Batuque Isesa</button>
        <button class="btn" onclick="activarPerfil('5', 'investigacion', 'investigación')">[5] INVESTIGACION: Relaciones internacionales, doctorado e investigación</button>
        <button class="btn" onclick="activarPerfil('6', 'docencia ingles', 'docencia en inglés')">[6] DOCENCIA INGLES: Material didáctico interactivo y enseñanza de inglés</button>
        <button class="btn" onclick="activarPerfil('7', 'docencia derecho', 'docencia en derecho')">[7] DOCENCIA DERECHO: Pedagogía jurídica y contenidos especializados</button>
        
        <div id="output">Estado del sistema: En espera de selección.</div>
    </div>

    <script>
        function hablarTexto(texto) {
            if ('speechSynthesis' in window) {
                window.speechSynthesis.cancel();
                let utterance = new SpeechSynthesisUtterance(texto);
                utterance.lang = 'es-AR';
                utterance.rate = 0.95;
                
                let voces = window.speechSynthesis.getVoices();
                let vozEspanol = voces.find(v => v.lang === 'es-AR' || v.lang === 'es-ES' || v.lang.startsWith('es'));
                if (vozEspanol) {
                    utterance.voice = vozEspanol;
                }
                
                window.speechSynthesis.speak(utterance);
            }
        }

        if ('speechSynthesis' in window) {
            window.speechSynthesis.onvoiceschanged = function() {
                window.speechSynthesis.getVoices();
            };
        }

        function activarPerfil(opcion, nombrePerfil, foneticaVoz) {
            let mensajeVoz = "Perfil activado: " + foneticaVoz;
            document.getElementById('output').innerHTML = "<strong>[OK] Perfil activado con éxito:</strong> " + nombrePerfil.toUpperCase();
            hablarTexto(mensajeVoz);
            
            fetch('/activar', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({opcion: opcion})
            })
            .then(response => response.json())
            .then(data => {
                console.log("Registro guardado para:", data.perfil);
            });
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/activar", methods=["POST"])
def activar():
    data = request.get_json()
    if not data:
        return jsonify({"perfil": "error", "descripcion": "No se recibieron datos"})
    opcion = data.get("opcion")
    if opcion in PILARES_THIAGO:
        perfil, descripcion, _ = PILARES_THIAGO[opcion]
        return jsonify({"perfil": perfil, "descripcion": descripcion})
    return jsonify({"perfil": "error", "descripcion": "Opción no válida"})

if __name__ == "__main__":
    app.run(debug=False, port=5000)
