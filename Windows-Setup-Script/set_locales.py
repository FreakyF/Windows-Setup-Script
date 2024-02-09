import winreg
import json
import logging

logging.basicConfig(level=logging.INFO)

KEY_PATH = r"Control Panel\International"
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


def set_registry_values(key, config_values):
    """
    Sets registry values based on the configuration data.
    """
    try:
        for value_name, value_data in config_values["localeValues"].items():
            if isinstance(value_data, str):
                registry_type = winreg.REG_SZ
            elif isinstance(value_data, int):
                registry_type = winreg.REG_DWORD
            else:
                raise ValueError(f"Unsupported type for value {value_name}: {type(value_data)}")

            winreg.SetValueEx(key, value_name, 0, registry_type, value_data)

        logging.info("Registry values set successfully.")
    except Exception as e:
        logging.error(f"Error setting registry values: {e}")


def main():
    config_data = read_config_file(CONFIG_FILE)

    if config_data and "localeValues" in config_data:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, KEY_PATH, 0, winreg.KEY_SET_VALUE)
        except FileNotFoundError:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, KEY_PATH)

        set_registry_values(key, config_data)
    else:
        logging.error("Configuration validation failed or the configuration file could not be read.")


if __name__ == "__main__":
    main()
