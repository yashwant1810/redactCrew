import re
import fitz  # PyMuPDF for PDFs
import pytesseract
from PIL import Image, ImageDraw
import cv2
import os
import google.generativeai as genai
import numpy as np
from fuzzywuzzy import fuzz  # For fuzzy matching
from dotenv import load_dotenv

load_dotenv()
api_key2 = os.getenv('API_KEY')

# PAN, Aadhaar, and Driving License detection regex patterns
pan_pattern = r'[A-Z]{5}\d{4}[A-Z]'
aadhaar_pattern = r'\b\d{4}\s?\d{4}\s?\d{4}\b'  # Aadhaar with or without spaces
driving_license_pattern = r'[A-Z]{2}\s?-?\s?\d{2}\s?-?\s?\d{11}'

# Boolean flags for PII types
REDUCT_AADHAAR = True
REDUCT_PAN = True
REDUCT_DRIVING_LICENSE = True
REDUCT_NAME = True

# =======================================
# Configure Gemini API
# =======================================
def configure_gemini_api():
    """Configure the Gemini API using the gemini-1.5-flash model."""
    print("Configuring Gemini API...")
    genai.configure(api_key=api_key2)

    # Use the gemini-1.5-flash model with structured output
    model = genai.GenerativeModel(
        'gemini-1.5-flash',
        generation_config={"response_mime_type": "text/plain"}  # Text-based response
    )
    print("Gemini API configured successfully.")
    return model

# =======================================
# Gemini API for Name Detection
# =======================================
def call_gemini_api_for_pii(text, model, redact_type):
    """Send text to Gemini API for detecting selective PII based on the user's request."""
    print(f"Calling Gemini API for {redact_type} detection...")

    prompt = f"""
    From the given text, identify any occurrences of:
    - {redact_type}

    For each detected entity, provide its start and end positions in the text in the following format:

    [Entity], Start: [Start index], End: [End index]

    Do not include any additional headers or formatting, just return one entity per line.
    
    Text: {text}
    """

    response = model.generate_content(prompt)

    print(f"Full API response: {response}")

    if response.candidates:
        try:
            if hasattr(response.candidates[0].content, 'parts'):
                candidate_text = response.candidates[0].content.parts[0].text
                output = candidate_text.splitlines()
                entities = []
                for line in output:
                    if "Start" in line and "End" in line:
                        parts = line.split(",")
                        if len(parts) >= 3:
                            entity = parts[0].strip()
                            start = int(parts[1].replace("Start:", "").strip())
                            end = int(parts[2].replace("End:", "").strip())
                            entities.append({"entity": entity, "start": start, "end": end, "type": redact_type})
                return entities
            else:
                print("No valid content or parts field in the API response.")
                return None
        except Exception as e:
            print(f"Error parsing Gemini API response: {e}")
            return None
    else:
        print("No valid candidates or safety ratings in the response.")
        return None

# =======================================
# Redact PII in Image
# =======================================
def redact_image(image, ocr_data, pan_numbers, aadhaar_numbers, driving_license_numbers, name_entities, original_size, resized_size):
    """Redact PAN, Aadhaar, Driving License, and names detected in the image."""
    print("Redacting PII in image...")

    # Calculate the scaling factor if the image was resized
    scale_x = original_size[1] / resized_size[1]
    scale_y = original_size[0] / resized_size[0]

    # Convert the image back to PIL
    if isinstance(image, np.ndarray):
        image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

    draw = ImageDraw.Draw(image)

    def clean_text(text):
        return re.sub(r'[^\w\s]', '', text).strip().lower()

    # Redact PAN numbers
    if REDUCT_PAN:
        for pan_number in pan_numbers:
            pan_clean = clean_text(pan_number)
            for word, x, y, w, h in zip(ocr_data['text'], ocr_data['left'], ocr_data['top'], ocr_data['width'], ocr_data['height']):
                word_clean = clean_text(word)
                if pan_clean in word_clean:
                    draw.rectangle([x, y, x + w, y + h], fill="black")

    # Redact Aadhaar numbers
    if REDUCT_AADHAAR:
        for aadhaar_number in aadhaar_numbers:
            tokens = aadhaar_number.split()
            positions = []
            for token in tokens:
                token_clean = clean_text(token)
                for word, x, y, w, h in zip(ocr_data['text'], ocr_data['left'], ocr_data['top'], ocr_data['width'], ocr_data['height']):
                    word_clean = clean_text(word)
                    if token_clean in word_clean:
                        positions.append((x, y, w, h))

            if len(positions) == len(tokens):
                min_x = min([x for x, _, _, _ in positions])
                max_x = max([x + w for x, _, w, _ in positions])
                min_y = min([y for _, y, _, _ in positions])
                max_y = max([y + h for _, y, _, h in positions])
                draw.rectangle([min_x, min_y, max_x, max_y], fill="black")

    # Redact Driving License numbers
    if REDUCT_DRIVING_LICENSE:
        for dl_number in driving_license_numbers:
            dl_clean = clean_text(dl_number)
            for word, x, y, w, h in zip(ocr_data['text'], ocr_data['left'], ocr_data['top'], ocr_data['width'], ocr_data['height']):
                word_clean = clean_text(word)
                if dl_clean in word_clean:
                    draw.rectangle([x, y, x + w, y + h], fill="black")

    # Redact Names from Gemini API
    if REDUCT_NAME:
        for entity in name_entities:
            for word, x, y, w, h in zip(ocr_data['text'], ocr_data['left'], ocr_data['top'], ocr_data['width'], ocr_data['height']):
                if fuzz.partial_ratio(entity['entity'], word) > 80:  # Use fuzzy matching for names
                    draw.rectangle([x, y, x + w, y + h], fill="black")

    return image

# =======================================
# Detect PAN, Aadhaar, and Driving License in Text
# =======================================
def detect_pii_in_text(text):
    """Detect PAN, Aadhaar, and Driving License numbers in the given text."""
    pan_matches = re.findall(pan_pattern, text)
    aadhaar_matches = re.findall(aadhaar_pattern, text)
    driving_license_matches = re.findall(driving_license_pattern, text)

    return pan_matches, aadhaar_matches, driving_license_matches

# =======================================
# Preprocess Image and Perform OCR
# =======================================
def preprocess_image(image_path):
    """Preprocess the image for OCR."""
    image = cv2.imread(image_path)

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Resize the image if it's too small
    height, width = gray.shape
    if height < 500 or width < 500:
        scale_factor = 2
        gray = cv2.resize(gray, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)

    return gray

def perform_ocr(image):
    """Perform OCR on the preprocessed image."""
    text = pytesseract.image_to_string(image)
    return text

# =======================================
# Redact PII in Image Files
# =======================================
def redact_pii_in_image_file(input_file, output_file, model, redact_type):
    """Redact PAN, Aadhaar, Driving License, and Names in image file."""
    print(f"Processing image file: {input_file}")
    
    # Load and preprocess the original image
    original_image = cv2.imread(input_file)
    original_size = original_image.shape[:2]  # (height, width)

    # Resize the image for consistent OCR
    resized_image = preprocess_image(input_file)
    resized_size = resized_image.shape[:2]  # (height, width)

    # Perform OCR on the resized image
    text = perform_ocr(resized_image)

    pan_numbers, aadhaar_numbers, driving_license_numbers = [], [], []
    name_entities = []

    # Detect based on boolean flags
    if REDUCT_AADHAAR:
        aadhaar_numbers = detect_pii_in_text(text)[1]
    if REDUCT_PAN:
        pan_numbers = detect_pii_in_text(text)[0]
    if REDUCT_DRIVING_LICENSE:
        driving_license_numbers = detect_pii_in_text(text)[2]
    if REDUCT_NAME:
        name_entities = call_gemini_api_for_pii(text, model, redact_type)

    if name_entities or pan_numbers or aadhaar_numbers or driving_license_numbers:
        # Perform OCR again to get bounding boxes
        ocr_data = pytesseract.image_to_data(resized_image, output_type=pytesseract.Output.DICT)
        print(f"OCR bounding box data: {ocr_data}")

        # Redact PII (PAN, Aadhaar, Driving License, Names)
        redacted_image = redact_image(original_image, ocr_data, pan_numbers, aadhaar_numbers, driving_license_numbers, name_entities, original_size, resized_size)
        redacted_image.save(output_file)
        print(f"Redacted image saved at: {output_file}")

# =======================================
# Redact PII in PDF Files
# =======================================
def redact_pii_in_pdf(input_pdf, output_pdf, model, redact_type):
    """Redact PAN, Aadhaar, Driving License, and Names in PDF file."""
    print(f"Processing PDF file: {input_pdf}")
    doc = fitz.open(input_pdf)

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        print(f"Processing page {page_num + 1}")

        # Extract text from the page
        page_text = page.get_text("text")
        print(f"Extracted text from page {page_num + 1}:\n{page_text[:500]}...")

        pan_numbers, aadhaar_numbers, driving_license_numbers = [], [], []
        name_entities = []

        # Detect based on boolean flags
        if REDUCT_AADHAAR:
            aadhaar_numbers = detect_pii_in_text(page_text)[1]
        if REDUCT_PAN:
            pan_numbers = detect_pii_in_text(page_text)[0]
        if REDUCT_DRIVING_LICENSE:
            driving_license_numbers = detect_pii_in_text(page_text)[2]
        if REDUCT_NAME:
            name_entities = call_gemini_api_for_pii(page_text, model, redact_type)

        # Redact PAN, Aadhaar, and Driving License
        if REDUCT_AADHAAR or REDUCT_PAN or REDUCT_DRIVING_LICENSE:
            for pan in pan_numbers:
                areas = page.search_for(pan)
                for area in areas:
                    print(f"Redacting PAN: {pan}")
                    page.add_redact_annot(area, fill=(0, 0, 0))

            for aadhaar in aadhaar_numbers:
                areas = page.search_for(aadhaar)
                for area in areas:
                    print(f"Redacting Aadhaar: {aadhaar}")
                    page.add_redact_annot(area, fill=(0, 0, 0))

            for dl in driving_license_numbers:
                areas = page.search_for(dl)
                for area in areas:
                    print(f"Redacting Driving License: {dl}")
                    page.add_redact_annot(area, fill=(0, 0, 0))

        # Redact Names
        if REDUCT_NAME and name_entities:
            for entity in name_entities:
                areas = page.search_for(entity['entity'])
                for area in areas:
                    print(f"Redacting Name: {entity['entity']}")
                    page.add_redact_annot(area, fill=(0, 0, 0))

        page.apply_redactions()  # Apply redactions for the current page

    doc.save(output_pdf)
    doc.close()
    print(f"Redaction completed. Saved the redacted file as {output_pdf}")

# =======================================
# Process Files
# =======================================
def process_file(input_file, output_folder, model, redact_type):
    file_ext = os.path.splitext(input_file)[1].lower()

    if file_ext == '.pdf':
        print(f"Processing PDF file: {input_file}")
        output_file = os.path.join(output_folder, 'redacted_' + os.path.basename(input_file))
        redact_pii_in_pdf(input_file, output_file, model, redact_type)
    elif file_ext in ['.jpg', '.jpeg', '.png']:
        print(f"Processing image file: {input_file}")
        output_file = os.path.join(output_folder, 'redacted_' + os.path.basename(input_file))
        redact_pii_in_image_file(input_file, output_file, model, redact_type)
    else:
        print(f"Unsupported file format: {input_file}")

# =======================================
# Folder Processing
# =======================================
def process_folder(input_folder, output_folder, model, redact_type):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        input_file = os.path.join(input_folder, filename)
        if os.path.isfile(input_file):
            print(f"Processing file: {input_file}")
            process_file(input_file, output_folder, model, redact_type)
        else:
            print(f"Skipping non-file entry: {filename}")

# Example usage:
input_folder = 'Input'  # Replace with your folder path
output_folder = 'Output'  # Replace with your folder path
redact_type = 'Name'  # Can be 'Name', 'Date of Birth', or anything the user asks

# Initialize the model and process files based on the boolean flags set at the top
gemini_model = configure_gemini_api()
process_folder(input_folder, output_folder, gemini_model, redact_type)