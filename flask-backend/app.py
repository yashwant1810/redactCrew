# app.py

import os
import shutil
import json
from flask import Flask, request, jsonify, send_from_directory, abort, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
from checkpoint_alpha import process_folder
import boto3
import mimetypes

app = Flask(__name__)

# Allow CORS for requests from localhost:3000
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

# Define the folders for input and output
INPUT_FOLDER = '/Users/yashwantbalaji/Library/Mobile Documents/com~apple~CloudDocs/Documents/PII_SIH/Present/flask-backend/Input'
OUTPUT_FOLDER = '/Users/yashwantbalaji/Library/Mobile Documents/com~apple~CloudDocs/Documents/PII_SIH/Present/flask-backend/Output'

# Create folders if they don't exist
os.makedirs(INPUT_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Allowed file extensions for upload
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def clear_input_folder():
    for filename in os.listdir(INPUT_FOLDER):
        file_path = os.path.join(INPUT_FOLDER, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f'Error deleting file {file_path}: {e}')

def clear_output_folder():
    for filename in os.listdir(OUTPUT_FOLDER):
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f'Error deleting file {file_path}: {e}')

@app.route('/upload', methods=['POST'])
def upload_files():
    # Clear output folder at the start of each new upload to remove old files
    clear_output_folder()

    if 'files' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400

    files = request.files.getlist('files')
    pii_options = request.form.get('piiOptions')

    if not pii_options:
        return jsonify({'error': 'No PII options provided'}), 400

    try:
        pii_flags = json.loads(pii_options)
        print(f"Received PII Options: {pii_flags}")

        # Initialize default pii_types
        pii_types = {
            'person': False,
            'address': False,
            'org': False,
            'aadhar': False,
            'pan': False,
            'dob': False,
            'dl': False,
            'voter': False,
            'ration_card': False,
            'birth_certificate': False,
            'passport': False,
        }

        # Update pii_types
        for key in pii_flags:
            if key in pii_types:
                pii_types[key] = pii_flags[key]
                print(f"Updated pii_types[{key}] to {pii_flags[key]}")
            else:
                print(f"Received unknown PII type: {key}")
    except json.JSONDecodeError as e:
        return jsonify({'error': f'Error parsing PII options: {e}'}), 400
    except Exception as e:
        return jsonify({'error': f'Unexpected error: {e}'}), 400

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            input_filepath = os.path.join(INPUT_FOLDER, filename)
            file.save(input_filepath)
            print(f"Saved uploaded file to {input_filepath}")
        else:
            print(f"Skipped unsupported or empty file: {file.filename}")

    # Process all files
    try:
        process_folder(INPUT_FOLDER, OUTPUT_FOLDER, pii_types)
    except Exception as e:
        print(f"Error during processing: {e}")
        return jsonify({'error': f'Error during processing: {e}'}), 500

    # Gather processed files and generate download URLs
    processed_files = []
    for file in os.listdir(OUTPUT_FOLDER):
        if '_redacted' in file and allowed_file(file):
            download_url = url_for('download_file', filename=file, _external=True)
            processed_files.append({'filename': file, 'download_url': download_url})
            print(f"Redacted file processed: {file}")
        else:
            print(f"Skipped non-redacted or unsupported file in output: {file}")

    clear_input_folder()

    if not processed_files:
        return jsonify({'error': 'No valid processed files found'}), 400

    return jsonify({'processedFiles': processed_files}), 200

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)
    except FileNotFoundError:
        abort(404)

# Hardcode S3 credentials and bucket info for demonstration
AWS_ACCESS_KEY_ID = "addkeyhere"
AWS_SECRET_ACCESS_KEY = "addkeyhere"
AWS_S3_BUCKET_NAME = "addnamehere"           
AWS_S3_REGION = "addregionhere"                 

s3_client = boto3.client(
    's3',
    region_name=AWS_S3_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

@app.route('/send_to_s3', methods=['POST'])
def send_to_s3():
    data = request.get_json()
    filename = data.get('filename')
    if not filename:
        return jsonify({'error': 'No filename provided'}), 400

    local_filepath = os.path.join(OUTPUT_FOLDER, filename)
    if not os.path.exists(local_filepath):
        return jsonify({'error': 'File does not exist'}), 404

    s3_key = filename
    # Determine MIME type
    content_type, _ = mimetypes.guess_type(local_filepath)
    if not content_type:
        content_type = 'application/octet-stream'

    try:
        s3_client.upload_file(
            local_filepath,
            AWS_S3_BUCKET_NAME,
            s3_key,
            ExtraArgs={
                'ACL': 'public-read',
                'ContentType': content_type,
                'ContentDisposition': 'inline'
            }
        )
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return jsonify({'error': 'Failed to upload to S3'}), 500

    public_url = f"https://<HOSTED WEBSITE ENDPOINT>/?key={s3_key}"

    # Remove the file from OUTPUT_FOLDER after sending to S3
    try:
        os.unlink(local_filepath)
        print(f"Deleted {filename} from OUTPUT_FOLDER after sending to S3.")
    except Exception as e:
        print(f"Error deleting file {local_filepath}: {e}")

    return jsonify({'public_url': public_url}), 200

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

if __name__ == '__main__':
    app.run(debug=True)


