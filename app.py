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
    return jsonify({"status": "Gil Backend Online!", "key_present": bool(GEMINI_API_KEY)}), 200

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True) or {}
        user_prompt = data.get("prompt", "Ciao Gil!")

        if not GEMINI_API_KEY:
            print("❌ GEMINI_API_KEY mancante!")
            return jsonify({"response": "Chiave API mancante nei secret di Render."}), 500

        full_prompt = (
            "Sei Gil, un assistente robotico simpatico, iperattivo e molto conciso. "
            "Rispondi in massimo 1 o 2 frasi brevi in italiano, in modo parlato e naturale senza simboli speciali o formattazione.\n\n"
            f"Utente: {user_prompt}"
        )

        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": full_prompt}]
            }]
        }

        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        response = requests.post(url, json=payload, headers=headers, timeout=15)

        if response.status_code == 200:
            res_data = response.json()
            try:
                text_response = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                print(f"✅ Risposta generata: {text_response}")
                return jsonify({"response": text_response}), 200
            except Exception as parse_err:
                print(f"❌ Errore parsing JSON Google: {res_data}")
                return jsonify({"response": "Ehi Genna, ho avuto un piccolo intoppo nei miei circuiti."}), 200
        else:
            print(f"⚠️ Google API status {response.status_code}: {response.text}")
            return jsonify({"response": "I miei sensori rilevano un piccolo problema con la rete neurale."}), 200

    except Exception as e:
        print("❌ Errore interno al server:")
        traceback.print_exc()
        return jsonify({"response": "Errore interno nei miei circuiti."}), 500

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
