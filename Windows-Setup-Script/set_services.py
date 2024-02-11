import subprocess
import time
from typing import List

from config_service import setup_logging, read_config_file, validate_config_section, logging

CONFIG_FILE = "config.json"


def modify_windows_services(services_list: List[dict], enabled: bool) -> None:
    """
    Modifies Windows services based on the provided `services_list` if `enabled` is True. Each service in the list is
    modified according to the specified parameters, such as startup type and service status.
    The function logs the outcome of each modification attempt, including cases where the service is already in the
    desired state, where the modification is successful, and where an error occurs during the process.

    Parameters:
    - services_list (List[dict]): A list of dictionaries representing Windows services to be modified.
    - enabled (bool): If False, service modification is skipped, and a log entry is made indicating it's disabled.
    """
    if not enabled:
        logging.info("Service modification is disabled.")
        return

    for service in services_list:
        name = service.get("name")
        startup_type = service.get("startupType")
        desired_state = service.get("serviceStatus").lower()

        startup_type_mapping = {
            "Automatic": "auto",
            "Manual": "demand",
            "Disabled": "disabled",
            "Automatic (Delayed Start)": "delayed-auto"
        }

        sc_startup_type = startup_type_mapping.get(startup_type)

        if sc_startup_type is None:
            logging.error(f"Invalid startup type '{startup_type}' for service '{name}'.")
            continue

        try:
            subprocess.check_output(["sc", "config", name, "start=", sc_startup_type], text=True)
            logging.info(f"Successfully changed startup type for {name} to {startup_type}.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to change startup type for {name}. Error: {e.output}")

        try:
            logging.info(f"Attempting to {desired_state} {name}...")
            if desired_state == "start":
                subprocess.run(["sc", "start", name], check=True, text=True)
                time.sleep(2)  # Wait for a couple of seconds to let the service respond
            elif desired_state == "stop":
                subprocess.run(["sc", "stop", name], check=True, text=True)
                time.sleep(2)

            status_output = subprocess.check_output(["sc", "query", name], text=True)
            if desired_state in status_output.lower():
                logging.info(f"Service {name} is now in the desired status: {desired_state}.")
            else:
                logging.error(f"Failed to {desired_state} {name}. Current status not as expected.")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error while attempting to {desired_state} {name}: {e}")


def main() -> None:
    """
    Executes the main functionality of the script which includes setting up logging, reading the configuration file,
    validating the 'servicesSettings' configuration section, and conditionally modifying services based on the
    configuration.
    """
    setup_logging()
    config_data = read_config_file(CONFIG_FILE)

    if not config_data:
        logging.error("Failed to read the configuration file.")
        return

    services_settings_keys = [
        {'key': 'enabled', 'type': bool},
        {'key': 'services', 'type': list}
    ]
    if not validate_config_section(config_data.get("servicesSettings", {}), services_settings_keys):
        logging.error("The 'servicesSettings' section in the configuration is invalid.")
        return

    modify_windows_services(config_data["servicesSettings"]["services"], config_data["servicesSettings"]["enabled"])


if __name__ == "__main__":
    main()
