# src/pipeline/hindi_extraction.py

import re
import sys
import os
import numpy as np
import logging
from PIL import Image, ImageDraw, ImageFont
from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline
import easyocr
from pdf2image import convert_from_path

def setup_logging(output_dir='output', log_file='hindi_results.log'):
    """
    Sets up logging to output to both console and a file.

    Args:
        output_dir (str): Directory where the log file will be saved.
        log_file (str): Name of the log file.

    Returns:
        logger (logging.Logger): Configured logger object.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    logger = logging.getLogger('HindiTextExtractionNER')
    logger.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # File handler
    file_handler = logging.FileHandler(os.path.join(output_dir, log_file), mode='w', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def extract_text_with_bboxes(input_image, languages=['hi']):
    """
    Extract text and bounding boxes from an image using EasyOCR.

    Args:
        input_image (PIL.Image.Image): PIL Image object.
        languages (list): List of languages to be used by EasyOCR.

    Returns:
        list of tuples: Each tuple contains (bounding_box, text, confidence).
    """
    reader = easyocr.Reader(languages, gpu=False)  # Set gpu=True if GPU is available
    results = reader.readtext(np.array(input_image), detail=1, paragraph=False)
    return results

def filter_hindi_ocr_results(ocr_results, image_width, image_height):
    """
    Filter OCR results to include only Hindi text, excluding numbers, English letters, and unwanted special characters.

    Args:
        ocr_results (list of tuples): Each tuple contains (bounding_box, text, confidence).
        image_width (int): Width of the image in pixels.
        image_height (int): Height of the image in pixels.

    Returns:
        list of dicts: Each dict contains 'text' and 'bbox' for filtered OCR results.
    """
    filtered = []
    pattern = re.compile(r'^[\u0900-\u097F।\s]+$')  # Only Hindi characters and '।'

    for result in ocr_results:
        bbox, text, conf = result
        # Remove leading/trailing spaces
        text = text.strip()
        if not text:
            continue
        # Check if text contains only Hindi characters and '।'
        if pattern.match(text):
            # Compute a single bounding box (min_x, min_y, max_x, max_y)
            x_coords = [point[0] for point in bbox]
            y_coords = [point[1] for point in bbox]
            min_x, min_y = min(x_coords), min(y_coords)
            max_x, max_y = max(x_coords), max(y_coords)
            # Normalize coordinates to [0,1]
            normalized_bbox = (
                (float(min_x / image_width), float(min_y / image_height)),
                (float(max_x / image_width), float(max_y / image_height))
            )
            filtered.append({
                'text': text,
                'bbox': normalized_bbox
            })
    return filtered