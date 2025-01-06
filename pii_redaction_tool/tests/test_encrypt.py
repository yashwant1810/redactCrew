# src/pipeline/test_encrypt_images.py

from pipeline.encrypt import encrypt_file
import os

def main():
    input_dir = 'input'
    encrypted_dir = 'input'  # Encrypted files will be saved in the same directory

    # Define supported image extensions
    supported_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')

    # List all image files in the input directory
    image_files = [f for f in os.listdir(input_dir) if f.lower().endswith(supported_extensions)]

    if not image_files:
        print(f"No image files found in the input directory: {input_dir}")
        return

    for image in image_files:
        input_path = os.path.join(input_dir, image)
        encrypted_filename = f"{os.path.splitext(image)[0]}.enc"
        output_path = os.path.join(encrypted_dir, encrypted_filename)

        # Encrypt the image
        encrypt_file(input_path, output_path)
        print(f"Encrypted '{image}' -> '{encrypted_filename}'")

    print("Encryption process completed.")

if __name__ == "__main__":
    main()