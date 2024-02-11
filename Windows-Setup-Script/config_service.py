import json
import logging
from typing import Any, Dict, List


def setup_logging(level: str = "INFO") -> None:
    """
    Configures the logging system to use a specified log level. This function removes any existing handlers from the
    root logger before setting up a new handler to ensure that logs are not duplicated. It uses a standard logging
    format that includes the timestamp, log level, and message.

    Parameters:
    - level (str): A string representing the logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
    """
    numeric_level = getattr(logging, level.upper(), None)
    if numeric_level is None:
        raise ValueError(f"Invalid logging level: {level}")
    logging.root.handlers = []  # Remove any existing handlers
    logging.basicConfig(level=numeric_level, format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')


def read_config_file(file_path: str) -> Dict[str, Any]:
    """
    Attempts to read and parse a JSON configuration file, returning its content as a dictionary. If the file cannot be
    read or parsed, it logs an appropriate error message and returns an empty dictionary.

    Parameters:
    - file_path (str): The path to the JSON configuration file.

    Returns:
    Dict[str, Any]: The contents of the configuration file, or an empty dictionary if an error occurs.
    """
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        logging.error(f"Configuration file '{file_path}' not found.")
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON in the configuration file '{file_path}'.")
    except Exception as e:
        logging.error(f"Unexpected error reading '{file_path}': {str(e)}")
    return {}


def validate_config_section(config_section: Dict[str, Any], required_keys: List[Dict[str, Any]]) -> bool:
    """
    Checks whether a specific section of the configuration data contains all required keys with the correct type. It
    logs an error for each missing or incorrectly typed key.

    Parameters:
    - config_section (Dict[str, Any]): The configuration section to validate.
    - required_keys (List[Dict[str, Type]]): A list of dictionaries, each specifying a 'key' (str) to look for
      in `config_section` and its expected 'type' (type).

    Returns:
    bool: True if the section passes validation, False otherwise.
    """
    for req in required_keys:
        key = req['key']
        expected_type = req['type']
        if key not in config_section:
            logging.error(f"Key '{key}' is missing from the configuration section.")
            return False
        if not isinstance(config_section[key], expected_type):
            logging.error(f"Key '{key}' is not of type {expected_type.__name__}.")
            return False
    return True
