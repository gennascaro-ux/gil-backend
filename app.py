import os
import asyncio
import traceback
from flask import Flask, request, jsonify, Response
import edge_tts
from google import genai

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

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
    return jsonify({"status": "Gil Backend Online!", "key_present": bool(GEMINI_API_KEY)}), 200

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True) or {}
        user_prompt = data.get("prompt", "Ciao!")

        if not client:
            return jsonify({"response": "Chiave API mancante."}), 500

        full_prompt = (
            "Sei Gil, un robottino simpatico e iperattivo. "
            "Rispondi in una sola frase breve e colloquiale in italiano, senza formattazione.\n\n"
            f"Utente: {user_prompt}"
        )

        # Chiamata pulita senza oggetti di configurazione complessi
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_prompt
        )
        
        text_response = response.text.strip() if response and response.text else "Ciao Genna!"
        print(f"✅ Risposta generata: {text_response}")
        return jsonify({"response": text_response}), 200

    except Exception as e:
        print("❌ Errore interno al server:")
        traceback.print_exc()
        return jsonify({"response": "Ehi Genna, ho i circuiti in tilt!"}), 200

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
