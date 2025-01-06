# src/pipeline/hindi_detection.py

import re
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import sys

def perform_hindi_ner(cleaned_text, model_name="ai4bharat/IndicNER", logger=None):
    """
    Perform Named Entity Recognition on the cleaned Hindi text.
    Expects to return person entities with 'start' and 'end' indices.
    """
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForTokenClassification.from_pretrained(model_name)
    except OSError as e:
        if logger:
            logger.error(f"Error loading the model '{model_name}': {e}")
            logger.error("Ensure the model name is correct and you have internet connectivity.")
        else:
            print(f"Error loading the model '{model_name}': {e}")
            print("Ensure the model name is correct and you have internet connectivity.")
        sys.exit(1)

    ner_pipeline_obj = pipeline(
        "token-classification",
        model=model,
        tokenizer=tokenizer,
        aggregation_strategy="simple",
        device=-1  # Use CPU. Set to 0 if GPU is available.
    )

    ner_results = ner_pipeline_obj(cleaned_text)

    person_entities = []
    for entity in ner_results:
        if entity.get("entity_group") == "PER":
            # Safely extract start/end, or default to None if not present
            person_name = entity["word"].replace("##", "")
            confidence = entity["score"]
            start = entity.get("start")
            end = entity.get("end")

            # Only append if start and end exist
            if start is not None and end is not None:
                person_entities.append({
                    "name": person_name,
                    "confidence": confidence,
                    "start": start,
                    "end": end
                })

    return person_entities

def map_hindi_entities_to_bboxes(person_entities, word_info_list):
    """
    Map detected person entities to a single bounding box similar to English pipeline.
    If 'start' or 'end' are missing, skip that entity.
    """

    def merge_bboxes(bboxes):
        # Merge multiple ((x0, y0), (x1, y1)) boxes into a single bounding box
        if not bboxes:
            return None
        min_x = min(b[0][0] for b in bboxes)
        min_y = min(b[0][1] for b in bboxes)
        max_x = max(b[1][0] for b in bboxes)
        max_y = max(b[1][1] for b in bboxes)
        return {
            'left': float(min_x),
            'top': float(min_y),
            'width': float(max_x - min_x),
            'height': float(max_y - min_y)
        }

    mapped_entities = []

    for entity in person_entities:
        # Skip if 'start' or 'end' not present
        if "start" not in entity or "end" not in entity:
            continue

        name = entity['name']
        confidence = entity['confidence']
        start = entity['start']
        end = entity['end']

        bboxes = []
        # Accumulate all bounding boxes of words that overlap the entity text indices
        for word in word_info_list:
            word_start = word.get('start')
            word_end = word.get('end')
            if word_start is None or word_end is None:
                continue

            # Check for character index overlap
            if not (word_end <= start or word_start >= end):
                bboxes.append(word['bbox'])

        # Merge all bounding boxes into one
        merged_box = merge_bboxes(bboxes)

        # If merged_box is None, entity had no valid bounding boxes
        if merged_box is None:
            # You can either skip or just continue without bounding box
            continue

        # Return a structure similar to English detection
        mapped_entities.append({
            'type': 'person',    # Assign a type - Hindi NER currently detects persons
            'text': name,         # Use 'text' instead of 'name' to be consistent
            'bounding_box': merged_box
        })

    return mapped_entities