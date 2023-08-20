from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import ngrok
import requests
import json
import uuid
import os
import whisper

PORT = 3000

data = """
This is a request for ChatGPT.

"""

MODEL_NAME = "base"
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

def gpt_request(req_chat):
    url = 'https://free.churchless.tech/v1/chat/completions'
    data_request = {
        "model":"gpt-3.5-turbo",
        "messages":[{"role":"user","content":req_chat}],
        "stream":True
    }

    response = requests.post(url, data=json.dumps(data_request), headers= {'Content-Type': 'application/json'}, stream=True)

    if response.status_code == 200:
        response_chat = ""
        for data in response.text.replace('\n\n', '\n').strip().split('\n')[:-2]:
            data_obj = json.loads(data[6:])
            delta = data_obj['choices'][0]['delta']
            if 'content' in delta:
                response_chat += delta['content']

        print(response_chat)
        return response_chat
    else:
        print("Failed to retrieve data. Status code:", response.status_code)

def whisper_transcribe(file_name):
    model = whisper.load_model(MODEL_NAME)
    result = model.transcribe(file_name)
    return result["text"]

@app.route('/audiorequest', methods=['POST'])
@cross_origin()
def transcribe_audio():
    new_file_name = str(uuid.uuid4()) + '.wav'
    try:
        audio_file = request.files['audio']
        if not audio_file:
            return jsonify({"error": "No audio file provided"}), 400
        
        audio_content = audio_file.read()

        with open(new_file_name, 'wb') as f:
            f.write(audio_content)

        transcribed_text = whisper_transcribe(new_file_name)
        
        os.remove(new_file_name)

        response_chat = gpt_request(transcribed_text)
        
        return jsonify({"transcription": transcribed_text, "response": response_chat }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/chat', methods=["POST"])
@cross_origin()
def chat_request():
    chat_request = request.form['content']
    response = gpt_request(chat_request)
    return jsonify({"chat": response}), 200

if __name__ == '__main__':
    ngrok_key = os.getenv("NGROK")
    if ngrok_key:
        tunnel = ngrok.connect(PORT, authtoken_from_env=True)
        print (f"Ingress established at {tunnel.url()}")
    app.run(debug=True, port=PORT)
