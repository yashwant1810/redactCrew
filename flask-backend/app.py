import os
import shutil
import time  # Import the time module for adding delay
from flask import Flask, request, jsonify, send_from_directory, abort
from flask_cors import CORS
from werkzeug.utils import secure_filename
from checkpoint_alpha import process_folder, configure_gemini_api

app = Flask(__name__)

# Allow CORS for requests from localhost:3000
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

# Define the folders for input and output
INPUT_FOLDER = 'Input'
OUTPUT_FOLDER = 'Output'

# Create folders if they don't exist
if not os.path.exists(INPUT_FOLDER):
    os.makedirs(INPUT_FOLDER)
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# Allowed file extensions for upload
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to clear the input folder
def clear_input_folder():
    for filename in os.listdir(INPUT_FOLDER):
        file_path = os.path.join(INPUT_FOLDER, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)  # Delete file
        except Exception as e:
            print(f'Error deleting file {file_path}: {e}')

# Route for uploading files and setting PII options
@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return 'No files uploaded', 400

    files = request.files.getlist('files')
    pii_options = request.form.get('piiOptions')

    # Replace 'true' and 'false' with Python equivalents 'True' and 'False'
    pii_options = pii_options.replace('true', 'True').replace('false', 'False')

    # Now evaluate the corrected pii_options string to a dictionary
    pii_flags = eval(pii_options)

    global REDUCT_AADHAAR, REDUCT_PAN, REDUCT_DRIVING_LICENSE, REDUCT_NAME
    REDUCT_AADHAAR = pii_flags['aadhar']
    REDUCT_PAN = pii_flags['pan']
    REDUCT_DRIVING_LICENSE = pii_flags['drivingLicense']
    REDUCT_NAME = pii_flags['name']

    processed_files = []

    # Process each file
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            input_filepath = os.path.join(INPUT_FOLDER, filename)
            file.save(input_filepath)

            gemini_model = configure_gemini_api()
            process_folder(INPUT_FOLDER, OUTPUT_FOLDER, gemini_model, 'Name')

            processed_file = f"redacted_{filename}"
            processed_files.append(processed_file)

            # Add a 1-second delay between processing files
            time.sleep(1)

    # Clear the Input folder after processing
    clear_input_folder()

    # Return the list of processed file paths to the frontend
    return jsonify({'processedFiles': processed_files})

# Route for downloading the processed file
@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)
    except FileNotFoundError:
        abort(404)

# CORS Configuration for Robustness
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

if __name__ == '__main__':
    app.run(debug=True)