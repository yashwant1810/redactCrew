# src/pipeline/test_decrypt_redacted_sample_image.py

from pipeline.decrypt import decrypt_file
import os

def main():
    # Define paths
    encrypted_path = os.path.join('output', 'sample_image_redacted.enc')
    decrypted_path = os.path.join('output', 'decrypted_sample_image_redacted.png')
    
    # Check if the encrypted file exists
    if not os.path.exists(encrypted_path):
        print(f"Encrypted file not found: {encrypted_path}")
        return
    
    # Decrypt the file
    try:
        decrypt_file(encrypted_path, decrypted_path)
        print(f"Decrypted redacted image saved to: {decrypted_path}")
    except Exception as e:
        print(f"An error occurred during decryption: {e}")

if __name__ == "__main__":
    main()