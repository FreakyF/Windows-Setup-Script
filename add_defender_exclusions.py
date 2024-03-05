import subprocess
from typing import Dict

from config_service import setup_logging, read_config_file, logging

CONFIG_FILE = "config.json"

CMDLETS = {
    "Folder": "Add-MpPreference -ExclusionPath",
    "File": "Add-MpPreference -ExclusionPath",
    "FileType": "Add-MpPreference -ExclusionExtension",
    "Process": "Add-MpPreference -ExclusionProcess"
}

CHECK_CMDLETS = {
    "Folder": "Get-MpPreference | Select-Object -ExpandProperty ExclusionPath",
    "File": "Get-MpPreference | Select-Object -ExpandProperty ExclusionPath",
    "FileType": "Get-MpPreference | Select-Object -ExpandProperty ExclusionExtension",
    "Process": "Get-MpPreference | Select-Object -ExpandProperty ExclusionProcess"
}


def is_excluded(exclusion_type: str, path: str) -> bool:
    """
    Checks if the specified exclusion (file, folder, file type, or process) is already excluded in Windows Defender.
    This determination is made by invoking PowerShell commands to query the current exclusions within Windows Defender
    and checking if the specified path or identifier matches any of the existing exclusions.

    Parameters:
    - exclusion_type (str): The type of exclusion to check (e.g., "File", "Folder", "FileType", "Process").
    - path (str): The path, extension, or process name to check for exclusion.
    """
    check_cmdlet = CHECK_CMDLETS[exclusion_type]
    cmd = f"{check_cmdlet}"
    try:
        result = subprocess.run(["powershell", "-Command", cmd], check=True, capture_output=True, text=True)
        if path.lower() in result.stdout.lower():
            return True
        else:
            return False
    except subprocess.CalledProcessError as e:
        logging.error(
            f"Failed to check if {exclusion_type} exclusion is already present: {path}. Error: {e.stderr.strip()}")
        return False


def add_exclusion(exclusion: Dict[str, str]) -> None:
    """
    Adds an exclusion to Windows Defender, using the appropriate PowerShell cmdlet based on the type of exclusion
    (file, folder, file type, or process). Before attempting to add the exclusion, it checks if the exclusion already
    exists to prevent duplicates. If the exclusion is already present, logs an informational message. Otherwise,
    executes the PowerShell command to add the exclusion and logs the outcome, including any errors encountered
    during the process.

    Parameters:
    - exclusion (Dict[str, str]): A dictionary containing the type and path of the exclusion. The 'type' key
      specifies the exclusion type (e.g., "File", "Folder", "FileType", "Process"), and the 'path' key specifies
      the path, extension, or process name to exclude.
    """
    if is_excluded(exclusion['type'], exclusion['path']):
        logging.info(f"{exclusion['type']} exclusion is already present: {exclusion['path']}")
        return

    cmdlet = CMDLETS[exclusion['type']]
    path = exclusion['path']
    cmd = f"{cmdlet} '{path}'"
    try:
        subprocess.run(["powershell", "-Command", cmd], check=True, capture_output=True, text=True)
        logging.info(f"Successfully added {exclusion['type']} exclusion: {path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to add {exclusion['type']} exclusion: {path}. Error: {e.stderr.strip()}")


def process_exclusions(exclusions_config: Dict[str, any]) -> None:
    """
    Processes a configuration dictionary containing exclusion settings for Windows Defender. If exclusions are enabled
    in the configuration, iterates through each specified exclusion and attempts to add it using the `add_exclusion`
    function. Logs an informational message if exclusions are disabled in the configuration.

    Parameters:
    - exclusions_config (Dict[str, any]): The configuration for exclusions, including an 'enabled' key that indicates
      whether exclusions should be processed, and an 'exclusions' key containing a list of exclusions to add.
    """
    if not exclusions_config.get('enabled', False):
        logging.info("Exclusions are disabled in configuration.")
        return

    for exclusion in exclusions_config.get('exclusions', []):
        add_exclusion(exclusion)


def main() -> None:
    """
    Executes the main functionality of the script which includes setting up logging, reading the configuration file,
    validating the 'excludeFromDefender' configuration section, and conditionally adding exclusions based on the
    configuration.
    """
    setup_logging()
    config_data = read_config_file(CONFIG_FILE)

    if not config_data:
        logging.error("Failed to read configuration file.")
        return

    exclusions_config = config_data.get("excludeFromDefender", {})
    process_exclusions(exclusions_config)


if __name__ == "__main__":
    main()
