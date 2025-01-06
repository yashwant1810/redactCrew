# src/pipeline/decrypt.py

from cryptography.fernet import Fernet, InvalidToken
from pipeline.utils import load_key
import os

def decrypt_file(input_path, output_path):
    """
    Decrypts an encrypted file and saves the plaintext to the specified output path.

    Parameters:
        input_path (str): Path to the encrypted input file.
        output_path (str): Path to save the decrypted file.

    Raises:
        FileNotFoundError: If the encrypted file does not exist.
        InvalidToken: If decryption fails due to an invalid key or corrupted file.
        Exception: For other decryption-related errors.
    """
    try:
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Encrypted file not found: {input_path}")

        key = load_key()
        fernet = Fernet(key)

        with open(input_path, 'rb') as enc_file:
            encrypted_data = enc_file.read()

        decrypted_data = fernet.decrypt(encrypted_data)

        with open(output_path, 'wb') as dec_file:
            dec_file.write(decrypted_data)

        print(f"File decrypted: {input_path} -> {output_path}")
    except FileNotFoundError as fnf_error:
        print(fnf_error)
        raise
    except InvalidToken:
        print(f"Invalid encryption key or corrupted file: {input_path}")
        raise
    except Exception as e:
        print(f"Decryption failed for {input_path}: {e}")
        raise