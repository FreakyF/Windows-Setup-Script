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


def add_exclusion(exclusion: Dict[str, str]) -> None:
    """
    Adds an exclusion to Windows Defender, using the appropriate PowerShell cmdlet based on the type of exclusion.

    Parameters:
    - exclusion (Dict[str, str]): A dictionary containing the type and path of the exclusion.
    """
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
    Processes the exclusions configuration to add each specified exclusion to Windows Defender.

    Parameters:
    - exclusions_config (Dict[str, any]): The configuration for exclusions.
    """
    if not exclusions_config.get('enabled', False):
        logging.info("Exclusions are disabled in configuration.")
        return

    for exclusion in exclusions_config.get('exclusions', []):
        add_exclusion(exclusion)


def main() -> None:
    """
    Main function to read configuration and add specified exclusions to Windows Defender.
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
