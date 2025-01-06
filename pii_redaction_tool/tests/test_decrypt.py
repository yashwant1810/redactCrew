# src/pipeline/test_decrypt.py

from pipeline.decrypt import decrypt_file
import os

def main():
    encrypted_path = os.path.join('input', 'sample.enc')
    decrypted_path = os.path.join('output', 'sample_decrypted.txt')
    decrypt_file(encrypted_path, decrypted_path)

if __name__ == "__main__":
    main()