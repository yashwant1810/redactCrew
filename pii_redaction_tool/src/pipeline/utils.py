# src/pipeline/utils.py

import os
from cryptography.fernet import Fernet
import yaml

def load_key():
    """
    Loads the symmetric encryption key from 'config/encryption_key.key'.
    
    Returns:
        bytes: The encryption key.
    
    Raises:
        FileNotFoundError: If the key file does not exist.
    """
    key_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'encryption_key.key')
    if not os.path.exists(key_path):
        raise FileNotFoundError(f"Encryption key not found at {key_path}. Please generate it first.")
    with open(key_path, 'rb') as key_file:
        key = key_file.read()
    return key

def generate_key():
    """
    Generates a new symmetric encryption key and saves it to 'config/encryption_key.key'.
    """
    key = Fernet.generate_key()
    # Resolve the project root by going two levels up from 'src/pipeline/'
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    key_path = os.path.join(project_root, 'config', 'encryption_key.key')
    
    # Ensure the 'config/' directory exists
    os.makedirs(os.path.dirname(key_path), exist_ok=True)
    
    with open(key_path, 'wb') as key_file:
        key_file.write(key)
    print(f"Encryption key generated and saved to {key_path}")

def load_pii_config(config_path='config/settings.yaml'):
    """
    Loads PII configuration from the YAML file.
    
    Parameters:
        config_path (str): Path to the configuration YAML file.
    
    Returns:
        dict: Parsed configuration dictionary.
    
    Raises:
        FileNotFoundError: If the configuration file does not exist.
        ValueError: If the configuration file is empty.
        yaml.YAMLError: If there's an error parsing the YAML file.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at {config_path}.")
    with open(config_path, 'r') as file:
        try:
            config = yaml.safe_load(file)
            if config is None:
                raise ValueError(f"Configuration file {config_path} is empty.")
            print(f"Loaded PII Configuration: {config}")  # Debugging statement
            return config
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")
            raise