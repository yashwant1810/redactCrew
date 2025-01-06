# src/pipeline/pii_detection.py

import re
from pipeline.utils import load_pii_config
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

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
            "pattern": r"\b(Birth\s?[Dd]ate)?\s?:?\s?(\d{1,2}[/.-]\d{1,2}[/.-]\d{4})\b"
        },
        {
            "name": "Date Format 2", 
            "pattern": r"\b(Date\s?of\s?[Bb]irth)?\s?:?\s?(\d{1,2}[/.-]\d{1,2}[/.-]\d{4})\b"
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
    print("\n--- Starting PII Detection ---")

    extracted_text_lines = [line['text'] for line in extracted_data]

    model_name = "dbmdz/bert-large-cased-finetuned-conll03-english"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForTokenClassification.from_pretrained(model_name)
    ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple")

    pii_config = load_pii_config()
    id_patterns = get_id_patterns()
    date_patterns = get_date_patterns()

    pii_entities = []

    # Flags
    person_flag = pii_types.get('person', False)
    address_flag = pii_types.get('address', False)
    org_flag = pii_types.get('org', False)

    print("Performing NER-based detection...")
    for line_data in extracted_data:
        text = line_data['text']
        entities = ner_pipeline(text)
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
    # Map the given ID card names to config keys:
    # "Aadhaar Card" -> "aadhar"
    # "PAN Card" -> "pan"
    # "Driving Licence" -> "dl"
    # "Voter ID Card" -> "voter"
    # "Ration Card" -> Possibly "ration_card" (if you want to handle it in config)
    # "Birth Certificate" -> "birth_certificate"
    # "Passport" -> "passport"
    for id_type, pattern in id_patterns.items():
        normalized_key = id_type.lower()  # e.g. "driving licence", "voter id card"
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
            if re.search(pattern, line_data['text'], re.IGNORECASE):
                entity_data = {
                    'type': normalized_key,
                    'text': line_data['text'],
                    'bounding_box': {
                        'left': line_data['left'],
                        'top': line_data['top'],
                        'width': line_data['width'],
                        'height': line_data['height']
                    }
                }
                pii_entities.append(entity_data)
                print(f"Detected {id_type.upper()}: {line_data['text']} at {entity_data['bounding_box']}")

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