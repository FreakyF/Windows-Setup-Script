import os
import json
import logging

logging.basicConfig(level=logging.INFO)

CONFIG_FILE = "config.json"


def read_config_file(file_path: str) -> dict | None:
    """
    Attempts to read and return the contents of a JSON configuration file.
    """
    try:
        with open(file_path, "r") as file:
            config_data = json.load(file)
            logging.info(f"Successfully read configuration from {file_path}")
            return config_data
    except FileNotFoundError as e:
        logging.error(f"{file_path} not found. Error: {e}")
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON in {file_path}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error when reading {file_path}: {e}")
    return None


def validate_config(config_data: dict) -> bool:
    """
    Validates the configuration data to ensure it contains required keys.
    """
    if "foldersToCreate" in config_data:
        if isinstance(config_data["foldersToCreate"], list):
            return True
        else:
            logging.error("'foldersToCreate' must be a list.")
    else:
        logging.error("'foldersToCreate' key not found in the configuration file.")
    return False


def create_folders(folders_list: list):
    """
    Creates the folders specified in the folders_list.
    """
    for folder in folders_list:
        if not os.path.exists(folder):
            try:
                os.makedirs(folder)
                logging.info(f"Created folder: {folder}")
            except OSError as e:
                logging.error(f"Error creating folder {folder}: {e}")
        else:
            logging.info(f"Folder already exists: {folder}")


def main():
    config_data = read_config_file(CONFIG_FILE)

    if config_data and validate_config(config_data):
        folders_to_create = config_data["foldersToCreate"]
        create_folders(folders_to_create)
    else:
        logging.error("Configuration validation failed or the configuration file could not be read.")


if __name__ == "__main__":
    main()
