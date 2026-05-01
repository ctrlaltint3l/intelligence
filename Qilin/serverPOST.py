from flask import Flask, request
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_file():
    
    if 'file' not in request.files:
        return 'No file part', 400

    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400

    ip_addr = request.remote_addr
    upload_dir = './upload/' + ip_addr
    os.makedirs(upload_dir, exist_ok=True)  
    filename = secure_filename(file.filename)
    upload_path = os.path.join(upload_dir, filename)
    file.save(upload_path)

    return 'File uploaded successfully', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=38888)
