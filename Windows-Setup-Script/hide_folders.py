import os
import ctypes
from typing import List

from config_service import setup_logging, read_config_file, validate_config_section, logging

CONFIG_FILE = "config.json"

FILE_ATTRIBUTE_HIDDEN = 0x02


def is_hidden(folder_path: str) -> bool:  # TODO: Rewrite the method annotation or simplify this method.
    """
    Checks if the specified folder is hidden in Windows.

    Parameters:
    - folder_path (str): The path of the folder to check.

    Returns:
    - bool: True if the folder is hidden, False otherwise.
    """
    return (ctypes.windll.kernel32.GetFileAttributesW(folder_path) != -1) and \
        (ctypes.windll.kernel32.GetFileAttributesW(folder_path) & FILE_ATTRIBUTE_HIDDEN != 0)


def set_hidden_attribute(folder_path: str):
    """
    Sets the hidden attribute to a folder in Windows.
    Uses the SetFileAttributesW function from the Windows API through ctypes.

    Parameters:
    - folder_path (str): The path of the folder to hide.
    """
    if not ctypes.windll.kernel32.SetFileAttributesW(folder_path, FILE_ATTRIBUTE_HIDDEN):
        raise ctypes.WinError()


def hide_folders(folders_list: List[str], enabled: bool) -> None:
    """
    Hides directories specified in `folders_list` if `enabled` is True. Each folder is hidden only if it is
    not already hidden. The function logs the outcome of each attempt to hide a directory, including cases where
    the directory is already hidden, where the hiding is successful, and where an error occurs during hiding.
    Paths in `folders_list` can include environment variables, which are expanded to their values.

    Parameters:
    - folders_list (List[str]): A list of directory paths to hide.
    - enabled (bool): If False, directory hiding is skipped, and a log entry is made indicating it's disabled.
    """
    if not enabled:
        logging.info("Directory hiding is skipped as it's disabled by configuration.")
        return

    for folder_path in folders_list:
        folder_path = os.path.expandvars(folder_path)

        if not os.path.exists(folder_path):
            logging.error(f"Directory '{folder_path}' does not exist. Skipping...")
            continue

        if is_hidden(folder_path):
            logging.info(f"Directory '{folder_path}' is already hidden.")
            continue

        try:
            set_hidden_attribute(folder_path)
            logging.info(f"Directory '{folder_path}' is now hidden.")
        except Exception as e:
            logging.error(f"Failed to hide directory '{folder_path}': {str(e)}")


def main() -> None:
    """
    Executes the main functionality of the script which includes setting up logging, reading the configuration
    file, validating the 'hideFolders' configuration section, and conditionally hiding directories based on
    the configuration.
    """
    setup_logging()
    config_data = read_config_file(CONFIG_FILE)

    if not config_data:
        logging.error("Failed to read the configuration file.")
        return

    hide_folders_section_keys = [
        {'key': 'enabled', 'type': bool},
        {'key': 'paths', 'type': list}
    ]
    if not validate_config_section(config_data.get("hideFolders", {}), hide_folders_section_keys):
        logging.error("The 'hideFolders' section in the configuration is invalid.")
        return

    hide_folders(config_data["hideFolders"]["paths"], config_data["hideFolders"]["enabled"])


if __name__ == "__main__":
    main()
