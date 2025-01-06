# src/pipeline/workflow.py

import os
import shutil
import warnings
import yaml
from pipeline.decrypt import decrypt_file
from pipeline.encrypt import encrypt_file
from pipeline.ocr import extract_text_and_coords
from pipeline.pii_detection import find_pii_entities
from pipeline.redaction import redact_image, redact_pdf
from pipeline.utils import load_pii_config
from pipeline.hindi_extraction import extract_text_with_bboxes, filter_hindi_ocr_results, setup_logging as hindi_setup_logging
from pipeline.hindi_detection import perform_hindi_ner, map_hindi_entities_to_bboxes
from tqdm import tqdm
from PIL import Image

warnings.filterwarnings("ignore")

def process_english(decrypted_file_path, redacted_file_path, pii_types):
    extracted_data = extract_text_and_coords(decrypted_file_path)
    
    english_extracted_text = " ".join([line['text'] for line in extracted_data if line.get('text')])
    print("\n--- English Extracted Text ---")
    print(english_extracted_text)
    print("--- End of English Extracted Text ---\n")

    detected_pii = find_pii_entities(extracted_data, pii_types)

    if detected_pii:
        print("\n--- Detected PII (English) ---")
        for entity in detected_pii:
            print(f"Type: {entity['type']}, Text: {entity['text']}, Bounding Box: {entity['bounding_box']}")
        print("--- End of Detected PII (English) ---\n")
    else:
        print("\nNo English PII detected.\n")

    original_ext = os.path.splitext(decrypted_file_path)[1].lower()
    if original_ext == '.pdf':
        redact_pdf(decrypted_file_path, detected_pii, redacted_file_path, pii_types)
    else:
        redact_image(decrypted_file_path, detected_pii, extracted_data, redacted_file_path, pii_types)

    return detected_pii

def process_hindi(hindi_decrypted_path, redacted_file_path, hindi_config, pii_types):
    if not hindi_config.get('enabled', False):
        return

    from PIL import Image
    original_ext = os.path.splitext(hindi_decrypted_path)[1].lower()

    if original_ext == '.pdf':
        from pdf2image import convert_from_path
        pages = convert_from_path(hindi_decrypted_path)
        hindi_extracted_data = []
        for page in pages:
            ocr_results = extract_text_with_bboxes(page, languages=hindi_config.get('languages', ['hi']))
            image_width, image_height = page.size
            filtered_ocr = filter_hindi_ocr_results(ocr_results, image_width, image_height)
            hindi_extracted_data.extend(filtered_ocr)
    else:
        with Image.open(hindi_decrypted_path) as img:
            ocr_results = extract_text_with_bboxes(img, languages=hindi_config.get('languages', ['hi']))
            image_width, image_height = img.size
            hindi_extracted_data = filter_hindi_ocr_results(ocr_results, image_width, image_height)

    hindi_extracted_text = " ".join([entry['text'] for entry in hindi_extracted_data if entry.get('text')])
    print("\n--- Hindi Extracted Text ---")
    print(hindi_extracted_text)
    print("--- End of Hindi Extracted Text ---\n")

    hindi_person_entities = perform_hindi_ner(
        cleaned_text=' '.join([entry['text'] for entry in hindi_extracted_data]),
        model_name=hindi_config.get('ner_model', 'ai4bharat/IndicNER'),
        logger=hindi_config.get('logger', None)
    )

    print("\n--- Debug: Hindi Person Entities ---")
    for ent in hindi_person_entities:
        print(ent)
    print("--- End of Debug: Hindi Person Entities ---\n")

    hindi_mapped_entities = map_hindi_entities_to_bboxes(hindi_person_entities, hindi_extracted_data)

    if hindi_mapped_entities:
        print("\n--- Detected PII (Hindi) ---")
        for entity in hindi_mapped_entities:
            print(f"Name: {entity['text']}, Bounding Boxes: {entity['bounding_box']}")
        print("--- End of Detected PII (Hindi) ---\n")
    else:
        print("\nNo Hindi PII detected.\n")

    # Only redact if hindi_mapped_entities exist AND 'person' type redaction is enabled
    if hindi_mapped_entities and pii_types.get('person', False):
        if original_ext == '.pdf':
            redact_pdf(hindi_decrypted_path, hindi_mapped_entities, redacted_file_path, pii_types)
        else:
            redact_image(hindi_decrypted_path, hindi_mapped_entities, hindi_extracted_data, redacted_file_path, pii_types)

def process_file(encrypted_input_path, encrypted_output_path, temp_dir, pii_types, hindi_config, english_enabled, hindi_enabled):
    try:
        os.makedirs(temp_dir, exist_ok=True)

        base_name = os.path.basename(encrypted_input_path)
        if not base_name.endswith('.enc'):
            print(f"Skipping non-encrypted file: {base_name}")
            return
        original_filename = base_name[:-4]
        original_ext = os.path.splitext(original_filename)[1].lower()

        decrypted_file_path = os.path.join(temp_dir, f'decrypted_input{original_ext}')
        redacted_file_path = os.path.join(temp_dir, f'redacted_input{original_ext}')

        decrypt_file(encrypted_input_path, decrypted_file_path)

        if english_enabled:
            process_english(decrypted_file_path, redacted_file_path, pii_types)
            encrypt_file(redacted_file_path, encrypted_output_path)
        else:
            shutil.copyfile(decrypted_file_path, redacted_file_path)
            encrypt_file(redacted_file_path, encrypted_output_path)

        if hindi_enabled and hindi_config.get('enabled', False):
            hindi_decrypted_path = os.path.join(temp_dir, f'decrypted_redacted_input{original_ext}')
            decrypt_file(encrypted_output_path, hindi_decrypted_path)

            process_hindi(hindi_decrypted_path, redacted_file_path, hindi_config, pii_types)

            encrypt_file(redacted_file_path, encrypted_output_path)
            os.remove(hindi_decrypted_path)

        os.remove(decrypted_file_path)
        os.remove(redacted_file_path)

        print(f"Successfully processed: {encrypted_input_path} -> {encrypted_output_path}")

    except Exception as e:
        print(f"Error processing file {encrypted_input_path}: {e}")

def run_workflow(input_dir='input', output_dir='output', temp_dir='temp', pii_config_path='config/settings.yaml'):
    import logging

    try:
        with open(pii_config_path, 'r') as file:
            config = yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Configuration file not found: {pii_config_path}")
        return
    except yaml.YAMLError as e:
        print(f"Error parsing configuration file: {e}")
        return

    processing_config = config.get('processing', {})
    english_enabled = processing_config.get('english_enabled', True)
    hindi_enabled = processing_config.get('hindi_enabled', True)

    pii_patterns = config.get('pii_patterns', {})

    # Include dl and voter
    pii_types = {
        'aadhar': pii_patterns.get('aadhar', False),
        'pan': pii_patterns.get('pan', False),
        'person': pii_patterns.get('person', False),
        'gpe': False,
        'org': False,
        'address': pii_patterns.get('address', False),
        'dob': pii_patterns.get('dob', False),
        'dl': pii_patterns.get('dl', False),       # Added dl
        'voter': pii_patterns.get('voter', False)  # Added voter
    }

    hindi_config = config.get('hindi_processing', {})
    hindi_logger = hindi_setup_logging(
        output_dir=output_dir,
        log_file=hindi_config.get('log_file', 'hindi_results.log')
    )
    hindi_config['logger'] = hindi_logger

    os.makedirs(output_dir, exist_ok=True)
    encrypted_files = [f for f in os.listdir(input_dir) if f.endswith('.enc')]

    if not encrypted_files:
        print(f"No encrypted files found in the input directory: {input_dir}")
        return

    for file in tqdm(encrypted_files, desc="Processing files"):
        encrypted_input_path = os.path.join(input_dir, file)
        base_name = os.path.splitext(file)[0]
        encrypted_output_path = os.path.join(output_dir, f"{base_name}_redacted.enc")

        process_file(
            encrypted_input_path=encrypted_input_path,
            encrypted_output_path=encrypted_output_path,
            temp_dir=temp_dir,
            pii_types=pii_types,
            hindi_config=hindi_config,
            english_enabled=english_enabled,
            hindi_enabled=hindi_enabled
        )

    try:
        shutil.rmtree(temp_dir)
        print(f"Temporary directory '{temp_dir}' removed.")
    except Exception as e:
        print(f"Error removing temporary directory '{temp_dir}': {e}")