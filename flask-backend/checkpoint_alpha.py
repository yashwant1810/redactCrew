# checkpoint_alpha.py

import os
import shutil
import warnings
import re
import fitz  # PyMuPDF
from PIL import Image, ImageDraw
from doctr.models import ocr_predictor
from doctr.io import DocumentFile
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

warnings.filterwarnings("ignore")

def load_pii_config():
    """
    Loads PII configuration.
    Currently returns an empty dictionary.
    Modify this function if you have specific configurations.
    
    Returns:
        dict: Configuration dictionary.
    """
    # If you have specific PII configurations, load them here.
    # For now, returning an empty dictionary.
    return {}

def pdf_to_images(pdf_path, output_dir='temp_images'):
    """
    Converts a PDF to images using PyMuPDF.

    Parameters:
        pdf_path (str): Path to the PDF file.
        output_dir (str): Directory to save the images.

    Returns:
        List[str]: Paths to the generated image files.
    """
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    image_paths = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        image_path = os.path.join(output_dir, f"page_{page_num + 1}.png")
        pix.save(image_path)
        image_paths.append(image_path)

    return image_paths

def extract_text_and_coords(file_path):
    """
    Extracts text and bounding box coordinates from an image or PDF using docTR OCR.

    Parameters:
        file_path (str): Path to the image or PDF file.

    Returns:
        List[dict]: A list of dictionaries containing 'text', 'left', 'top', 'width', 'height' for each line.
    """
    try:
        config = load_pii_config()  # Load PII configurations if any
        # Initialize OCR model if not already done
        if not hasattr(extract_text_and_coords, "ocr_model"):
            extract_text_and_coords.ocr_model = ocr_predictor(pretrained=True)

        ocr_model = extract_text_and_coords.ocr_model

        # Determine if file is PDF or image
        if file_path.lower().endswith(".pdf"):
            try:
                doc = DocumentFile.from_pdf(file_path)
            except Exception as e:
                print(f"Error reading PDF with docTR: {e}")
                print("Attempting to convert PDF to images using PyMuPDF...")
                image_paths = pdf_to_images(file_path)
                doc = DocumentFile.from_images(image_paths)
        else:
            doc = DocumentFile.from_images(file_path)

        result = ocr_model(doc)

        extracted_data = []
        # docTR returns normalized coordinates (relative to page width/height)
        for page in result.pages:
            for block in page.blocks:
                for line_obj in block.lines:
                    line_text = " ".join(word.value for word in line_obj.words)
                    # geometry: ((x0, y0), (x1, y1))
                    (x0, y0), (x1, y1) = line_obj.geometry
                    # Convert normalized coords into width/height
                    left = float(x0)
                    top = float(y0)
                    width = float(x1 - x0)
                    height = float(y1 - y0)
                    
                    extracted_data.append({
                        'text': line_text,
                        'left': left,
                        'top': top,
                        'width': width,
                        'height': height
                    })

        return extracted_data
    except Exception as e:
        print(f"Error during OCR extraction: {e}")
        return []

def get_id_patterns():
    return {
        "Ration Card": r"\b(Ration\s?Card|RC)\s?[-/]?\s?(\d{5,12})\b",
        "Birth Certificate": r"\b(Birth\s?Certificate|BC)\s?[-/]?\s?([A-Z]{2}\d{6,10})\b",
        "Aadhaar Card": r"\b(Aadhaar\s?Card)?\s?:?\s?(\d{4}\s?\d{4}\s?\d{4})\b",
        "PAN Card": r"\b([A-Z]{5}\d{4}[A-Z])\b",
        "Passport": r"\b([A-Z]\d{7})\b",
        "Driving Licence": r"\b(DL|Driving\s?Licence)\s?[-/]?\s?([A-Z]{2}\d{7,9})\b",
        "Voter ID Card": r"\b(Voter\s?ID\s?Card)?\s?:?\s?([A-Z]{3}\d{7})\b"
    }

def get_date_patterns():
    return [
        {
            "name": "Date Format 1", 
            "pattern": r"\b(Birth\s?[Dd]ate)?\s?:?\s?(\d{1,2}[\/\.-]\d{1,2}[\/\.-]\d{4})\b"
        },
        {
            "name": "Date Format 2", 
            "pattern": r"\b(Date\s?of\s?[Bb]irth)?\s?:?\s?(\d{1,2}[\/\.-]\d{1,2}[\/\.-]\d{4})\b"
        },
        {
            "name": "Date Format 3", 
            "pattern": r"\b(DoB)?\s?:?\s?(\d{4}[-]\d{1,2}[-]\d{1,2})\b"
        },
        {
            "name": "Date Format 4", 
            "pattern": r"\b(Birth\s?[Dd]ate)?\s?:?\s?(\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4})\b"
        },
        {
            "name": "Date Format 5", 
            "pattern": r"\b(जन्म\s?तिथि|जन्म\s?दिनांक)?\s?:?\s?(\d{1,2}\s*(?:जनवरी|फरवरी|मार्च|अप्रैल|मई|जून|जुलाई|अगस्त|सितंबर|अक्टूबर|नवंबर|दिसंबर)\s*\d{4})\b"
        },
        {
            "name": "Date Format 6", 
            "pattern": r"\b(DoB)?\s?:?\s?(\d{1,2}\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d{4})\b"
        }
    ]

def find_pii_entities(extracted_data, pii_types):
    """
    Identifies PII entities in the extracted text using NER and regex.
    Supports multiple PII types including IDs and dates.
    """
    print("\n--- Starting PII Detection ---")

    # Load NER model once globally to optimize performance
    model_name = "dbmdz/bert-large-cased-finetuned-conll03-english"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForTokenClassification.from_pretrained(model_name)
    ner_pipeline_instance = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple")

    id_patterns = get_id_patterns()
    date_patterns = get_date_patterns()

    pii_entities = []

    # Flags for NER-based detection
    person_flag = pii_types.get('person', False)
    address_flag = pii_types.get('address', False)
    org_flag = pii_types.get('org', False)

    print("Performing NER-based detection...")
    for line_data in extracted_data:
        text = line_data['text']
        entities = ner_pipeline_instance(text)
        for entity in entities:
            ent_type = entity['entity_group']
            ent_text = entity['word'].strip()

            pii_type = None
            if ent_type == "PER" and person_flag:
                pii_type = 'person'
            elif ent_type == "LOC" and address_flag:
                pii_type = 'address'
            elif ent_type == "ORG" and org_flag:
                pii_type = 'org'

            if pii_type:
                entity_data = {
                    'type': pii_type,
                    'text': ent_text,
                    'bounding_box': {
                        'left': line_data['left'],
                        'top': line_data['top'],
                        'width': line_data['width'],
                        'height': line_data['height']
                    }
                }
                pii_entities.append(entity_data)
                print(f"Detected {pii_type.upper()}: {ent_text} at {entity_data['bounding_box']}")

    print("Performing ID and date regex detection...")
    # ID Normalization
    for id_type, pattern in get_id_patterns().items():
        normalized_key = id_type.lower()
        # Mapping specific ID types to their keys in pii_types
        if normalized_key == "aadhaar card":
            normalized_key = "aadhar"
        elif normalized_key == "pan card":
            normalized_key = "pan"
        elif normalized_key == "driving licence":
            normalized_key = "dl"
        elif normalized_key == "voter id card":
            normalized_key = "voter"
        elif normalized_key == "ration card":
            normalized_key = "ration_card"
        elif normalized_key == "birth certificate":
            normalized_key = "birth_certificate"
        elif normalized_key == "passport":
            normalized_key = "passport"

        if not pii_types.get(normalized_key, False):
            continue

        for line_data in extracted_data:
            matches = re.findall(pattern, line_data['text'], re.IGNORECASE)
            if matches:
                for match in matches:
                    # Depending on the pattern, match could be a tuple
                    if isinstance(match, tuple):
                        # Assuming the second group contains the ID number
                        matched_text = match[1] if len(match) > 1 else match[0]
                    else:
                        matched_text = match
                    entity_data = {
                        'type': normalized_key,
                        'text': matched_text,
                        'bounding_box': {
                            'left': line_data['left'],
                            'top': line_data['top'],
                            'width': line_data['width'],
                            'height': line_data['height']
                        }
                    }
                    pii_entities.append(entity_data)
                    print(f"Detected {id_type.upper()}: {matched_text} at {entity_data['bounding_box']}")

    # DOB detection
    if pii_types.get('dob', False):
        found_dates_set = set()
        for date_fmt in date_patterns:
            pattern = re.compile(date_fmt['pattern'], re.IGNORECASE | re.UNICODE)
            for line_data in extracted_data:
                matches = re.findall(pattern, line_data['text'])
                if matches:
                    flat_matches = [m[1] if isinstance(m, tuple) else m for m in matches]
                    new_matches = [m for m in flat_matches if m not in found_dates_set]
                    for match in new_matches:
                        found_dates_set.add(match)
                        entity_data = {
                            'type': 'dob',
                            'text': match,
                            'bounding_box': {
                                'left': line_data['left'],
                                'top': line_data['top'],
                                'width': line_data['width'],
                                'height': line_data['height']
                            }
                        }
                        pii_entities.append(entity_data)
                        print(f"Detected DOB: {match} at {entity_data['bounding_box']}")

        # Additional DOB pattern
        dob_pattern = re.compile(r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[-/]\d{1,2})\b', re.IGNORECASE)
        for line_data in extracted_data:
            dob_matches = dob_pattern.findall(line_data['text'])
            for dob_match in dob_matches:
                if dob_match not in found_dates_set:
                    found_dates_set.add(dob_match)
                    entity_data = {
                        'type': 'dob',
                        'text': dob_match,
                        'bounding_box': {
                            'left': line_data['left'],
                            'top': line_data['top'],
                            'width': line_data['width'],
                            'height': line_data['height']
                        }
                    }
                    pii_entities.append(entity_data)
                    print(f"Detected DOB: {dob_match} at {entity_data['bounding_box']}")

    print("--- Completed PII Detection ---\n")
    return pii_entities

def redact_image(image_path, pii_entities, output_path, pii_types):
    """
    Redacts identified PII in images.
    """
    try:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        with Image.open(image_path) as img:
            image_width, image_height = img.size
            draw = ImageDraw.Draw(img)

            for entity in pii_entities:
                entity_type = entity.get('type', '')
                if not pii_types.get(entity_type, False):
                    # Skip redaction if disabled
                    continue

                bbox = entity['bounding_box']
                left = bbox['left'] * image_width
                top = bbox['top'] * image_height
                width = bbox['width'] * image_width
                height = bbox['height'] * image_height

                rectangle = [left, top, left + width, top + height]
                draw.rectangle(rectangle, fill='black')

            img.save(output_path)
            print(f"Redacted image saved to: {output_path}")

    except Exception as e:
        print(f"Redaction failed for {image_path}: {e}")
        raise

def redact_pdf(pdf_path, pii_entities, output_path, pii_types):
    """
    Redacts identified PII in a PDF by overlaying black boxes.
    """
    try:
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        doc = fitz.open(pdf_path)
        for page_num, page in enumerate(doc, start=1):
            for entity in pii_entities:
                entity_type = entity.get('type', '')
                if not pii_types.get(entity_type, False):
                    continue

                bbox = entity['bounding_box']
                if bbox is None:
                    continue
                rect = fitz.Rect(
                    bbox['left'] * page.rect.width,
                    bbox['top'] * page.rect.height,
                    (bbox['left'] + bbox['width']) * page.rect.width,
                    (bbox['top'] + bbox['height']) * page.rect.height
                )
                page.add_redact_annot(rect, fill=(0, 0, 0))
            # Apply redactions for the current page
            page.apply_redactions()

        doc.save(output_path)
        print(f"Redacted PDF saved to: {output_path}")

    except Exception as e:
        print(f"Redaction failed for {pdf_path}: {e}")
        raise

def process_file(input_path, output_folder, pii_types):
    """
    Extracts text, detects PII, and redacts if needed.
    If no PII is found, copies the file as is to the output directory.
    """
    extracted_data = extract_text_and_coords(input_path)
    if not extracted_data:
        # If OCR failed or no data, just copy the file
        output_file = os.path.join(output_folder, os.path.basename(input_path))
        shutil.copyfile(input_path, output_file)
        print("No text extracted. File copied as-is.")
        return

    english_extracted_text = " ".join([line['text'] for line in extracted_data if line.get('text')])
    print("\n--- English Extracted Text ---")
    print(english_extracted_text)
    print("--- End of English Extracted Text ---\n")

    detected_pii = find_pii_entities(extracted_data, pii_types)

    if detected_pii:
        print("\n--- Detected PII ---")
        for entity in detected_pii:
            print(f"Type: {entity['type']}, Text: {entity['text']}, Bounding Box: {entity['bounding_box']}")
        print("--- End of Detected PII ---\n")
    else:
        print("\nNo PII detected.\n")

    base_name = os.path.basename(input_path)
    root, ext = os.path.splitext(base_name)
    if detected_pii:
        # Redact
        if ext.lower() == '.pdf':
            output_file = os.path.join(output_folder, f"{root}_redacted.pdf")
            redact_pdf(input_path, detected_pii, output_file, pii_types)
        else:
            output_file = os.path.join(output_folder, f"{root}_redacted{ext}")
            redact_image(input_path, detected_pii, output_file, pii_types)
    else:
        # No PII detected, just copy
        output_file = os.path.join(output_folder, base_name)
        shutil.copyfile(input_path, output_file)
        print("No PII detected. File copied as-is.")

def process_folder(input_folder, output_folder, pii_types):
    """
    Processes all supported files in the input_folder and saves redacted files to output_folder.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    supported_extensions = ('.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp')
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(supported_extensions):
            input_file = os.path.join(input_folder, filename)
            print(f"Processing file: {input_file}")
            process_file(input_file, output_folder, pii_types)
        else:
            print(f"Skipping unsupported file format: {filename}")

