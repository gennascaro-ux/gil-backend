import os
import asyncio
import traceback
from flask import Flask, request, jsonify, Response
from google import genai
import edge_tts

app = Flask(__name__)

# Inizializzazione del client ufficiale Google GenAI
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = None

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    print("⚠️ ATTENZIONE: GEMINI_API_KEY non trovata nelle variabili d'ambiente!")

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
        if not client:
            return jsonify({"error": "API Key di Gemini mancante sul server"}), 500

        data = request.get_json()
        if not data or "prompt" not in data:
            return jsonify({"error": "Nessun prompt fornito"}), 400

        user_prompt = data["prompt"]
        full_prompt = (
            "Sei Gil, un assistente robotico simpatico e molto conciso. "
            "Rispondi in massimo 1 o 2 frasi brevi in italiano.\n\n"
            f"Utente: {user_prompt}"
        )

        # Generazione tramite SDK ufficiale aggiornato
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt,
        )

        if not response or not response.text:
            return jsonify({"error": "Risposta vuota da Gemini"}), 500

        text_response = response.text.strip()
        print(f"Risposta generata: {text_response}")

        return jsonify({"response": text_response}), 200

    except Exception as e:
        print("❌ Errore durante la richiesta a Gemini:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/speak", methods=["GET"])
def speak():
    text = request.args.get("text", "")
    if not text:
        return "No text provided", 400
    try:
        audio_bytes = asyncio.run(text_to_speech_bytes(text))
        return Response(audio_bytes, mimetype="audio/mpeg")
    except Exception as e:
        print(f"Errore endpoint speak: {e}")
        return str(e), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
