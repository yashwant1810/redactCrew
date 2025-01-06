# src/pipeline/encrypt.py

from cryptography.fernet import Fernet
from pipeline.utils import load_key
import os

def encrypt_file(input_path, output_path):
    """
    Encrypts a file and saves it to the specified output path.

    Parameters:
        input_path (str): Path to the plaintext input file.
        output_path (str): Path to save the encrypted file.

    Raises:
        FileNotFoundError: If the input file does not exist.
        Exception: If encryption fails.
    """
    try:
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        key = load_key()
        fernet = Fernet(key)

        with open(input_path, 'rb') as file:
            original_data = file.read()

        encrypted_data = fernet.encrypt(original_data)

        with open(output_path, 'wb') as encrypted_file:
            encrypted_file.write(encrypted_data)

        print(f"File encrypted: {input_path} -> {output_path}")
    except Exception as e:
        print(f"Encryption failed for {input_path}: {e}")
        raise