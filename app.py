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

        # Utilizziamo il modello esatto trovato nella tua lista
        model = genai.GenerativeModel("gemini-3.5-flash")
        response = model.generate_content(full_prompt)

        return jsonify({"response": response.text.strip()}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
