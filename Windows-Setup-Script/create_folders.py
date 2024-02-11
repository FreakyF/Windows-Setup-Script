import os
from typing import List

from config_service import setup_logging, read_config_file, validate_config_section, logging

CONFIG_FILE = "config.json"


def create_folders(folders_list: List[str], enabled: bool) -> None:
    """
    Creates directories specified in `folders_list` if `enabled` is True. Each folder is created only if it does not
    already exist. The function logs the outcome of each attempt to create a directory, including cases where the
    directory already exists, where the creation is successful, and where an error occurs during creation. Paths in
    `folders_list` can include environment variables, which are expanded to their values.

    Parameters:
    - folders_list (List[str]): A list of directory paths to create.
    - enabled (bool): If False, directory creation is skipped, and a log entry is made indicating it's disabled.
    """
    if not enabled:
        logging.info("Directory creation is skipped as it's disabled by configuration.")
        return

    for folder_path in folders_list:
        if not folder_path:
            logging.error("Received an empty string as a folder path. Skipping...")
            continue

        folder_path = os.path.expandvars(folder_path)

        if os.path.exists(folder_path):
            logging.info(f"Directory '{folder_path}' already exists.")
        else:
            try:
                os.makedirs(folder_path)
                logging.info(f"Directory '{folder_path}' created successfully.")
            except Exception as e:
                logging.error(f"Failed to create directory '{folder_path}': {str(e)}")


def main() -> None:
    """
    Executes the main functionality of the script which includes setting up logging, reading the configuration file,
    validating the 'createFolders' configuration section, and conditionally creating directories based on the
    configuration.
    """
    setup_logging()
    config_data = read_config_file(CONFIG_FILE)

    if not config_data:
        logging.error("Failed to read the configuration file.")
        return

    create_folders_keys = [
        {'key': 'enabled', 'type': bool},
        {'key': 'paths', 'type': list}
    ]
    if not validate_config_section(config_data.get("createFolders", {}), create_folders_keys):
        logging.error("The 'createFolders' section in the configuration is invalid.")
        return

    create_folders(config_data["createFolders"]["paths"], config_data["createFolders"]["enabled"])


if __name__ == "__main__":
    main()
