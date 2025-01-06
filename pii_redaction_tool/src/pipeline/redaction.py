# src/pipeline/redaction.py

from PIL import Image, ImageDraw
import os
import fitz  # PyMuPDF

def redact_image(image_path, pii_entities, extracted_data, output_path, pii_types):
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
            page.apply_redactions()

        doc.save(output_path)
        print(f"Redacted PDF saved to: {output_path}")

    except Exception as e:
        print(f"Redaction failed for {pdf_path}: {e}")
        raise