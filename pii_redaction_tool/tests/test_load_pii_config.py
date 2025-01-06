# src/pipeline/test_load_pii_config.py

from pipeline.utils import load_pii_config

def main():
    config = load_pii_config()
    print("PII Configuration Loaded Successfully:")
    print(config)

if __name__ == "__main__":
    main()