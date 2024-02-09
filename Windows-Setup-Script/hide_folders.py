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
    if "foldersToHide" in config_data:
        if isinstance(config_data["foldersToHide"], list):
            return True
        else:
            logging.error("'foldersToHide' must be a list.")
    else:
        logging.error("'foldersToHide' key not found in the configuration file.")
    return False


def is_hidden(folder_path: str) -> bool:
    """
    Check if the folder is already hidden.
    """
    try:
        attributes = os.stat(folder_path).st_file_attributes
        return attributes & 2 == 2  # Check if the hidden attribute is set
    except Exception as e:
        logging.error(f"Error checking hidden status for folder {folder_path}: {e}")
        return False


def hide_folders(folders_list: list):
    """
    Hides the folders specified in the folders_list by setting the 'hidden' attribute.
    """
    for folder in folders_list:
        if os.path.exists(folder):
            if not is_hidden(folder):
                try:
                    os.system(f'attrib +h "{folder}"')
                    logging.info(f"Hidden folder: {folder}")
                except Exception as e:
                    logging.error(f"Error hiding folder {folder}: {e}")
            else:
                logging.info(f"Folder already hidden: {folder}")
        else:
            logging.info(f"Folder not found: {folder}")


def main():
    config_data = read_config_file(CONFIG_FILE)

    if config_data and validate_config(config_data):
        folders_to_hide = config_data["foldersToHide"]
        hide_folders(folders_to_hide)
    else:
        logging.error("Configuration validation failed or the configuration file could not be read.")


if __name__ == "__main__":
    main()
