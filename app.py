import os
import base64
import asyncio
from flask import Flask, request, jsonify
import google.generativeai as genai
import edge_tts

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

async def text_to_speech_base64(text, voice="it-IT-DiegoNeural"):
    communicate = edge_tts.Communicate(text, voice)
    audio_data = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data.extend(chunk["data"])
    return base64.b64encode(audio_data).decode("utf-8")

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

        model = genai.GenerativeModel("gemini-3.5-flash")
        response = model.generate_content(full_prompt)
        text_response = response.text.strip()

        # Genera l'audio Base64
        audio_b64 = asyncio.run(text_to_speech_base64(text_response))

        return jsonify({
            "response": text_response,
            "audio": audio_b64
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
