# src/pipeline/test_encrypt_workflow.py

from pipeline.encrypt import encrypt_file
import os

def main():
    input_path = os.path.join('input', 'sample_image.png')
    encrypted_path = os.path.join('input', 'sample_image.enc')
    encrypt_file(input_path, encrypted_path)

if __name__ == "__main__":
    main()