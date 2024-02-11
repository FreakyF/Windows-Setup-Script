import os
import subprocess
from typing import List

from config_service import setup_logging, read_config_file, validate_config_section, logging

CONFIG_FILE = "config.json"

GET_EXCLUSION_CMDLET = "Get-MpPreference | Select-Object -ExpandProperty ExclusionPath"
ADD_EXCLUSION_CMDLET = "Add-MpPreference -ExclusionPath"


def get_current_exclusions() -> List[str]:
    """
    Retrieves the current list of folder paths excluded in Windows Defender.

    Returns:
    - List[str]: A list of paths that are currently excluded.
    """
    try:
        result = subprocess.check_output(["powershell", "-Command", GET_EXCLUSION_CMDLET], text=True)
        exclusions = [line.strip() for line in result.split('\n') if line.strip()]
        return exclusions
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to retrieve current exclusions: {str(e)}")
        return []


def add_exclusion(folder_path: str) -> None:
    """
    Adds a folder to Windows Defender exclusions using PowerShell.

    Parameters:
    - folder_path (str): The path of the folder to add to exclusions.
    """
    cmd = f"{ADD_EXCLUSION_CMDLET} '{folder_path}'"
    try:
        subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(
            f"Failed to add '{folder_path}' to Windows Defender exclusions. PowerShell error: {e.stderr.strip()}")
        raise


def add_folders_to_exclusions(folders_list: List[str], enabled: bool) -> None:
    """
    Adds directories specified in `folders_list` to Windows Defender exclusions if `enabled` is True.  Each folder is
    added only if it is not already excluded. The function logs the outcome of each attempt to exclude a directory,
    including cases where the directory is already excluded, where the exclusion is successful, and where an error
    occurs during exclusion. Paths in `folders_list` can include environment variables, which are expanded to their
    values.

    Parameters:
    - folders_list (List[str]): A list of directory paths to add to exclusions.
    - enabled (bool): If False, adding exclusions is skipped, and a log entry is made indicating it's disabled.
    """
    if not enabled:
        logging.info("Adding folders to Windows Defender exclusions is skipped as it's disabled by configuration.")
        return

    current_exclusions = get_current_exclusions()

    for folder_path in folders_list:
        folder_path = os.path.expandvars(folder_path)

        if not os.path.exists(folder_path):
            logging.error(f"Directory '{folder_path}' does not exist. Skipping...")
            continue

        if folder_path in current_exclusions:
            logging.info(f"Directory '{folder_path}' is already in Windows Defender exclusions.")
            continue

        try:
            add_exclusion(folder_path)
            logging.info(f"Directory '{folder_path}' was added to Windows Defender exclusions.")
        except Exception as e:
            logging.error(f"Failed to add directory '{folder_path}' to Windows Defender exclusions: {str(e)}")


def main() -> None:
    """
    Executes the main functionality of the script which includes setting up logging, reading the configuration file,
    validating the 'excludeFoldersFromDefender' configuration section, add directories to Windows Defender exclusions
    based on the configuration.
    """
    setup_logging()
    config_data = read_config_file(CONFIG_FILE)

    if not config_data:
        logging.error("Failed to read the configuration file.")
        return

    defender_exclusions_section_keys = [
        {'key': 'enabled', 'type': bool},
        {'key': 'paths', 'type': list}
    ]
    if not validate_config_section(config_data.get("excludeFoldersFromDefender", {}), defender_exclusions_section_keys):
        logging.error("The 'excludeFoldersFromDefender' section in the configuration is invalid.")
        return

    add_folders_to_exclusions(config_data["excludeFoldersFromDefender"]["paths"],
                              config_data["excludeFoldersFromDefender"]["enabled"])


if __name__ == "__main__":
    main()
