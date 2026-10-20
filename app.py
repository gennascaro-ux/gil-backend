import os
import re
import uuid
import asyncio
import traceback
from flask import Flask, request, jsonify, Response, send_from_directory
import edge_tts
from google import genai

app = Flask(__name__)

# Cartella temporanea sul server per salvare i chunk audio
AUDIO_DIR = "/tmp/audio_chunks"
os.makedirs(AUDIO_DIR, exist_ok=True)

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

def split_text_into_chunks(text, max_chars=100):
    """
    Spezza il testo in frasi naturali e brevi basandosi sulla punteggiatura
    per evitare la saturazione della RAM dell'ESP32.
    """
    raw_sentences = re.split(r'(?<=[.!?;\n])\s+', text)
    chunks = []
    current_chunk = ""

    for sentence in raw_sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        if len(current_chunk) + len(sentence) <= max_chars:
            current_chunk += (" " if current_chunk else "") + sentence
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

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

        system_instruction = (
            "Sei Gil, un'intelligenza artificiale sintetica. "
            "Rispondi in italiano in modo estremamente breve, diretto e colloquiale (massimo 1 o 2 frasi corte), "
            "senza formattazione markdown, liste o asterischi. Sii conciso."
        )

        full_prompt = f"{system_instruction}\n\nUtente: {user_prompt}"

        # Usiamo il modello corretto e stabile
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_prompt
        )
        
        text_response = response.text.strip() if response and response.text else "Ehi Genna, sono pronto."
        clean_text = re.sub(r'[\*\_#`]', '', text_response)
        print(f"✅ Risposta generata: {clean_text}")

        text_chunks = split_text_into_chunks(clean_text)
        session_id = str(uuid.uuid4())[:8]
        chunk_urls = []
        base_url = request.host_url.rstrip('/')

        for idx, chunk_text in enumerate(text_chunks):
            filename = f"{session_id}_chunk_{idx}.mp3"
            filepath = os.path.join(AUDIO_DIR, filename)
            
            audio_bytes = asyncio.run(text_to_speech_bytes(chunk_text))
            if audio_bytes:
                with open(filepath, "wb") as f:
                    f.write(audio_bytes)
                chunk_urls.append(f"{base_url}/audio/{filename}")

        return jsonify({
            "response": clean_text,
            "total_chunks": len(chunk_urls),
            "audio_chunks": chunk_urls
        }), 200

    except Exception as e:
        print("❌ Errore interno al server:")
        traceback.print_exc()
        return jsonify({
            "response": "Ehi Genna, ho i circuiti in tilt!",
            "total_chunks": 0,
            "audio_chunks": []
        }), 200

@app.route("/audio/<filename>", methods=["GET"])
def get_audio_chunk(filename):
    """ Restituisce all'ESP32 il singolo mini file MP3 del chunk """
    return send_from_directory(AUDIO_DIR, filename)

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
