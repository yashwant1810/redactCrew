# src/pipeline/test_decrypt_sample_image.py

from pipeline.decrypt import decrypt_file
import os

def main():
    encrypted_path = os.path.join('input', 'sample_image.enc')  # Replace with your encrypted file
    decrypted_path = os.path.join('temp', 'decrypted_sample_image.png')
    decrypt_file(encrypted_path, decrypted_path)
    print(f"Decrypted file saved to: {decrypted_path}")

if __name__ == "__main__":
    main()