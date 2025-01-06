# src/main.py

import os
from pipeline.encrypt import encrypt_file
from pipeline.workflow import run_workflow
from pipeline.decrypt import decrypt_file
from tqdm import tqdm

def process_new_files(input_dir='input', output_dir='output', temp_dir='temp', pii_config_path='config/settings.yaml'):
    """
    Encrypts all image and PDF files in the input directory, processes them for PII redaction,
    and saves the redacted encrypted files to the output directory.
    """
    # Define supported file extensions
    supported_extensions = ('.png', '.pdf', '.jpg', '.jpeg', '.bmp', '.tiff')
    
    # List all supported files in the input directory
    input_files = [f for f in os.listdir(input_dir) if f.lower().endswith(supported_extensions)]
    
    if not input_files:
        print(f"No supported files found in the input directory: {input_dir}")
        return
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Encrypt all supported files
    encrypted_files = []
    print("Starting Encryption Process...")
    for file in tqdm(input_files, desc="Encrypting files"):
        input_path = os.path.join(input_dir, file)
        encrypted_filename = f"{file}.enc"
        encrypted_output_path = os.path.join(input_dir, encrypted_filename)
        
        # Encrypt the file
        encrypt_file(input_path, encrypted_output_path)
        encrypted_files.append(encrypted_filename)
        print(f"Encrypted '{file}' -> '{encrypted_filename}'")
    
    print("Encryption Process Completed.\n")
    
    # Run the existing redaction workflow on encrypted files
    print("Starting PII Redaction Process...")
    run_workflow(
        input_dir=input_dir,
        output_dir=output_dir,
        temp_dir=temp_dir,
        pii_config_path=pii_config_path
    )
    print("PII Redaction Process Completed.\n")
    
    # Decrypt redacted files (optional)
    print("Starting Decryption of Redacted Files...")
    for enc_file in encrypted_files:
        # Define the expected redacted encrypted filename
        base_name = os.path.splitext(enc_file)[0]
        redacted_enc_file = f"{base_name}_redacted.enc"
        encrypted_path = os.path.join(output_dir, redacted_enc_file)
        
        if not os.path.exists(encrypted_path):
            print(f"Encrypted file not found: {encrypted_path}")
            continue
        
        # Extract original extension by removing '.enc'
        original_filename = os.path.splitext(enc_file)[0]
        original_ext = os.path.splitext(original_filename)[1]
        
        # Determine decrypted file extension
        if original_ext.lower() == '.pdf':
            decrypted_extension = 'pdf'
        else:
            decrypted_extension = original_ext.lstrip('.').lower()
            if decrypted_extension not in ['png', 'jpg', 'jpeg', 'bmp', 'tiff']:
                decrypted_extension = 'png'
        
        decrypted_path = os.path.join(output_dir, f"decrypted_{original_filename}_redacted.{decrypted_extension}")
        decrypt_file(encrypted_path, decrypted_path)
        print(f"Decrypted '{redacted_enc_file}' -> 'decrypted_{original_filename}_redacted.{decrypted_extension}'")
    print("Decryption of Redacted Files Completed.\n")

if __name__ == "__main__":
    process_new_files()