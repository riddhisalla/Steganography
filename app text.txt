from flask import Flask, request, jsonify, abort, send_from_directory
from werkzeug.utils import secure_filename
from flask_pymongo import PyMongo
from jose import jwt
import requests
import os
from bson import ObjectId
from datetime import datetime
from dotenv import load_dotenv
from StegoHandler import ImageLSBSteganography, AudioLSBSteganography
from flask_cors import CORS

# -------------------- INIT --------------------
load_dotenv()
app = Flask(__name__)  # Corrected from _name_ to __name__
CORS(app)

app.config['UPLOAD_FOLDER'] = './uploads'
app.config['MONGO_URI'] = os.getenv("MONGO_URI")
mongo = PyMongo(app)

CLERK_ISSUER = os.getenv("CLERK_ISSUER")
JWKS_URL = f"{CLERK_ISSUER}/.well-known/jwks.json"

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

image_handler = ImageLSBSteganography()
audio_handler = AudioLSBSteganography()

# -------------------- AUTH --------------------
def get_current_user_id():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        abort(401, description="Missing token")

    token = auth_header.split(" ")[1]
    jwks = requests.get(JWKS_URL).json()

    try:
        payload = jwt.decode(token, jwks, algorithms=["RS256"], issuer=CLERK_ISSUER)
        return payload["sub"]  # Clerk user ID
    except Exception as e:
        print("Token verification failed:", e)
        abort(401, description="Invalid or expired token")

# -------------------- ROUTES --------------------

@app.route('/')
def index():
    return "Welcome to the Steganography API!"

@app.route('/Output/<path:filepath>')
def serve_output_file(filepath):
    return send_from_directory('Output', filepath)


# -------------------- IMAGE IN IMAGE --------------------
@app.route('/embed/image', methods=['POST'])
def embed_image():
    user_id = get_current_user_id()
    cover_image = request.files.get('cover')
    secret_image = request.files.get('secret')
    if not cover_image or not secret_image:
        return jsonify({'error': 'Both cover and secret images are required'}), 400

    cover_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(cover_image.filename))
    secret_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(secret_image.filename))
    cover_image.save(cover_path)
    secret_image.save(secret_path)

    output_path = image_handler.embedImage(cover_path, secret_path)

    mongo.db.userHistory.insert_one({
        "user_id": user_id,
        "action": "embed_image",
        "inputs": {
            "cover": cover_image.filename,
            "secret": secret_image.filename
        },
        "output_path": output_path,
        "timestamp": datetime.utcnow().isoformat()
    })

    return jsonify({'output_path': output_path})

@app.route('/extract/image', methods=['POST'])
def extract_image():
    user_id = get_current_user_id()
    stegano_image = request.files.get('image')
    if not stegano_image:
        return jsonify({'error': 'Stegano image is required'}), 400

    stegano_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(stegano_image.filename))
    stegano_image.save(stegano_path)

    output_path = image_handler.extractImage(stegano_path)

    mongo.db.userHistory.insert_one({
        "user_id": user_id,
        "action": "extract_image",
        "inputs": {
            "stegano_image": stegano_image.filename
        },
        "output_path": output_path,
        "timestamp": datetime.utcnow().isoformat()
    })

    return jsonify({'output_path': output_path})

# -------------------- MESSAGE IN IMAGE --------------------
@app.route('/embed/message/image', methods=['POST'])
def embed_message_image():
    user_id = get_current_user_id()
    cover_image = request.files.get('cover')
    message = request.form.get('message')
    if not cover_image or not message:
        return jsonify({'error': 'Cover image and message are required'}), 400

    cover_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(cover_image.filename))
    cover_image.save(cover_path)

    output_path = image_handler.embedMessage(cover_path, message)

    mongo.db.userHistory.insert_one({
        "user_id": user_id,
        "action": "embed_message_image",
        "inputs": {
            "cover": cover_image.filename,
            "message": message
        },
        "output_path": output_path,
        "timestamp": datetime.utcnow().isoformat()
    })

    return jsonify({'output_path': output_path})

@app.route('/extract/message/image', methods=['POST'])
def extract_message_image():
    user_id = get_current_user_id()
    stegano_image = request.files.get('image')
    if not stegano_image:
        return jsonify({'error': 'Stegano image is required'}), 400

    stegano_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(stegano_image.filename))
    stegano_image.save(stegano_path)

    message = image_handler.extractMessage(stegano_path)

    mongo.db.userHistory.insert_one({
        "user_id": user_id,
        "action": "extract_message_image",
        "inputs": {
            "image": stegano_image.filename
        },
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    })

    return jsonify({'message': message})

# -------------------- MESSAGE IN AUDIO --------------------
@app.route('/embed/message/audio', methods=['POST'])
def embed_message_audio():
    user_id = get_current_user_id()
    cover_audio = request.files.get('audio')
    message = request.form.get('message')
    if not cover_audio or not message:
        return jsonify({'error': 'Audio file and message are required'}), 400

    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(cover_audio.filename))
    cover_audio.save(audio_path)

    output_path = audio_handler.embedMessage(audio_path, message)

    mongo.db.userHistory.insert_one({
        "user_id": user_id,
        "action": "embed_message_audio",
        "inputs": {
            "audio": cover_audio.filename,
            "message": message
        },
        "output_path": output_path,
        "timestamp": datetime.utcnow().isoformat()
    })

    return jsonify({'output_path': output_path})

@app.route('/extract/message/audio', methods=['POST'])
def extract_message_audio():
    user_id = get_current_user_id()
    stegano_audio = request.files.get('audio')
    if not stegano_audio:
        return jsonify({'error': 'Audio file is required'}), 400

    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(stegano_audio.filename))
    stegano_audio.save(audio_path)

    message = audio_handler.extractMessage(audio_path)

    mongo.db.userHistory.insert_one({
        "user_id": user_id,
        "action": "extract_message_audio",
        "inputs": {
            "audio": stegano_audio.filename
        },
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    })

    return jsonify({'message': message})

# -------------------- USER HISTORY --------------------
@app.route('/history', methods=['GET'])
def get_history():
    user_id = get_current_user_id()
    history_cursor = mongo.db.userHistory.find(
        {"user_id": user_id},
        {"user_id": 0}  # Exclude user_id
    )
    history = []
    for doc in history_cursor:
        doc['_id'] = str(doc['_id'])  # Convert ObjectId to string
        history.append(doc)

    return jsonify({"history": history})

@app.route('/history/clear', methods=['POST'])
def clear_history():
    user_id = get_current_user_id()
    result = mongo.db.userHistory.delete_many({"user_id": user_id})
    return jsonify({"message": "History cleared.", "deleted_count": result.deleted_count})

@app.route('/history/<entry_id>', methods=['DELETE'])
def delete_history_entry(entry_id):
    user_id = get_current_user_id()
    try:
        result = mongo.db.userHistory.delete_one({
            "_id": ObjectId(entry_id),
            "user_id": user_id
        })
        if result.deleted_count == 1:
            return jsonify({"message": "Entry deleted."})
        else:
            return jsonify({"error": "Entry not found or unauthorized."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# -------------------- MAIN --------------------
if __name__ == '__main__':  # Corrected from _name_ == '_main_' to __name__ == '__main__'
    try:
        mongo.db.command("ping")
        print("✅ Connected to MongoDB")
    except Exception as e:
        print("❌ Failed to connect to MongoDB:", e)
        exit(1)

    app.run(host='0.0.0.0', port=5000, debug=True)
