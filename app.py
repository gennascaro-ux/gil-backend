import os
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Configura l'SDK ufficiale di Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Gil Backend Online!"}), 200

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        if not data or "prompt" not in data:
            return jsonify({"error": "Nessun prompt fornito"}), 400

        user_prompt = data["prompt"]

        full_prompt = (
            "Sei Gil, un assistente robotico simpatico, brillante e conciso. "
            "Rispondi sempre in italiano in modo breve e diretto.\n\n"
            f"Utente: {user_prompt}"
        )

        # Prova con i modelli più comuni
        model_names = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp", "gemini-pro"]
        
        last_error = None
        for name in model_names:
            try:
                model = genai.GenerativeModel(name)
                response = model.generate_content(full_prompt)
                return jsonify({"response": response.text.strip()}), 200
            except Exception as e:
                last_error = str(e)
                continue

        # Se nessuno dei modelli sopra funziona, recuperiamo la lista dei modelli abilitati sulla tua chiave
        available_models = []
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
        except Exception as list_err:
            available_models = [f"Errore lista modelli: {str(list_err)}"]

        return jsonify({
            "error": "Nessun modello valido trovato",
            "last_error": last_error,
            "modelli_disponibili_sulla_tua_key": available_models
        }), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
