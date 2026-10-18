import os
import asyncio
from flask import Flask, request, jsonify, Response
import google.generativeai as genai
import edge_tts

app = Flask(__name__)

# Configurazione API Key di Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

async def text_to_speech_bytes(text, voice="it-IT-DiegoNeural"):
    try:
        communicate = edge_tts.Communicate(text, voice)
        audio_data = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.extend(chunk["data"])
        return bytes(audio_data)
    except Exception as e:
        print(f"Errore TTS: {e}")
        return b""

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
            "Sei Gil, un assistente robotico simpatico e molto conciso. "
            "Rispondi in massimo 1 o 2 frasi brevi in italiano.\n\n"
            f"Utente: {user_prompt}"
        )

        # Inizializzazione corretta e stabile del modello
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(full_prompt)
        
        if not response or not response.text:
            return jsonify({"error": "Risposta vuota da Gemini"}), 500

        text_response = response.text.strip()

        return jsonify({
            "response": text_response
        }), 200

    except Exception as e:
        print(f"Errore Chat: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/speak", methods=["GET"])
def speak():
    text = request.args.get("text", "")
    if not text:
        return "No text provided", 400
    audio_bytes = asyncio.run(text_to_speech_bytes(text))
    return Response(audio_bytes, mimetype="audio/mpeg")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
