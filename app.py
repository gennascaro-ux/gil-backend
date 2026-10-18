import os
import asyncio
import traceback
import requests
from flask import Flask, request, jsonify, Response
import edge_tts

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

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
        if not GEMINI_API_KEY:
            return jsonify({"error": "API Key di Gemini mancante sul server"}), 500

        data = request.get_json(silent=True)
        if not data or "prompt" not in data:
            return jsonify({"error": "Nessun prompt fornito o JSON non valido"}), 400

        user_prompt = data["prompt"]
        full_prompt = (
            "Sei Gil, un assistente robotico simpatico, iperattivo e molto conciso. "
            "Rispondi in massimo 1 o 2 frasi brevi in italiano.\n\n"
            f"Utente: {user_prompt}"
        )

        # Chiamata REST diretta all'API v1beta per gemini-2.0-flash
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": full_prompt}]
            }]
        }

        response = requests.post(url, json=payload, timeout=20)
        
        if response.status_code != 200:
            print(f"❌ Errore API Google ({response.status_code}): {response.text}")
            return jsonify({"error": f"Google API Error: {response.text}"}), 500

        res_data = response.json()
        text_response = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
        
        print(f"Risposta generata: {text_response}")
        return jsonify({"response": text_response}), 200

    except Exception as e:
        print("❌ Errore critico nel backend:")
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
