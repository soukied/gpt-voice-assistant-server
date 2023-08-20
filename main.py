from flask import Flask, request, jsonify, Response
from flask_cors import CORS, cross_origin
from pyngrok import ngrok
import time
import requests
import json
import uuid
import os
import whisper

PORT = 3000

data = """
This is a request for ChatGPT.

"""

MODEL_NAME = "small"
app = Flask(__name__)
cors = CORS(app)
model = whisper.load_model(MODEL_NAME)
app.config['CORS_HEADERS'] = 'Content-Type'

def generate_data():
    for i in range(1, 11):
        time.sleep(1)
        yield f"Data point {i}\n"
        # Simulate some processing time

@app.route('/stream')
def stream_data():
    return Response(generate_data(), mimetype='text/plain')

def gpt_chunk_iterator(response):
    for chunk in response.iter_content(chunk_size=1024):
        chunk_str = chunk.decode('utf-8')
        yield chunk_str

def gpt_request(req_chat):
    url = 'https://free.churchless.tech/v1/chat/completions'
    data_request = {
        "model":"gpt-3.5-turbo",
        "messages":[{"role":"user","content":req_chat}],
        "stream":True
    }

    response = requests.post(url, data=json.dumps(data_request), headers= {'Content-Type': 'application/javascript'}, stream=True)

    if response.status_code == 200:
        return gpt_chunk_iterator(response), 200
#        for data in response.text.replace('\n\n', '\n').strip().split('\n')[:-2]:
#            data_obj = json.loads(data[6:])
#            delta = data_obj['choices'][0]['delta']
#            if 'content' in delta:
#                response_chat += delta['content']
    else:
        print(f"Gagal mengambil request dengan kode {response.status_code}, mengulang kembali. ")
        def test():
            yield "Error"
        return test() ,response.status_code

def whisper_transcribe(file_name):
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

        print("[Server] Transcribing Audio...")
        transcribed_text = whisper_transcribe(new_file_name)
        
        os.remove(new_file_name)

        response_chat, status_code = gpt_request(transcribed_text)
        
        print("[Server] Writing response...")

        return Response(response_chat, mimetype="text/plain"), status_code
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/chat', methods=["POST"])
@cross_origin()
def chat_request():
    chat_request = request.form['content']
    response, error_code = gpt_request(chat_request)
    return Response(response, mimetype="text/plain"), error_code

@app.route('/')
@cross_origin()
def index():
    index_html = ""
    with open('test.html') as file:
        index_html = file.read()
    return index_html
if __name__ == '__main__':
    ngrok_key = os.getenv("NGROK")
    if ngrok_key:
        ngrok.set_auth_token(ngrok_key)
        tunnel = ngrok.connect(PORT).public_url
        print (f"Ingress established at {tunnel}")
    app.run(debug=True, port=PORT)
