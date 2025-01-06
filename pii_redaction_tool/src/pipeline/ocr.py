# src/pipeline/ocr.py

import os
from pipeline.utils import load_pii_config
from doctr.models import ocr_predictor
from doctr.io import DocumentFile
import fitz  # PyMuPDF

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
        config = load_pii_config()
        ocr_model = ocr_predictor(pretrained=True)

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