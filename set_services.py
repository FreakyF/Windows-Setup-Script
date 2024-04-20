import subprocess
import time
from typing import List

from config_service import setup_logging, read_config_file, validate_config_section, logging

CONFIG_FILE = "config.json"


def query_service_startup_type(service_name: str) -> str:
    """
    Queries the startup type of Windows service using the 'sc qc' command and returns the service startup type.
    The function maps the output to simplified keywords like 'auto', 'demand', 'disabled', and 'delayed-auto'. If the
    command fails, it returns 'unknown'.

    Parameters:
    - service_name (str): The name of the service to query.

    Returns:
    - str: The startup type of the service.
    """
    try:
        output = subprocess.check_output(["sc", "qc", service_name], text=True)
        if "AUTO_START" in output:
            return "auto"
        elif "DEMAND_START" in output:
            return "demand"
        elif "DISABLED" in output:
            return "disabled"
        elif "DELAYED_AUTO_START" in output:
            return "delayed-auto"
    except subprocess.CalledProcessError:
        return "unknown"


def query_service_status(service_name: str) -> str:
    """
    Queries the current status of a Windows service using the 'sc query' command. The function returns the service
    status such as 'running', 'stopped', or 'paused'. If the command execution fails, it returns 'unknown'.

    Parameters:
    - service_name (str): The name of the service to query.

    Returns:
    - str: The current status of the service.
    """
    try:
        output = subprocess.check_output(["sc", "query", service_name], text=True)
        if "RUNNING" in output:
            return "running"
        elif "STOPPED" in output:
            return "stopped"
        elif "PAUSED" in output:
            return "paused"
    except subprocess.CalledProcessError:
        return "unknown"


def wait_for_service_status(service_name: str, target_status: str, timeout: int = 30) -> bool:
    """
    Waits for a service to reach a specific status within a given timeout period. The function periodically checks the
    service status and returns True if the service reaches the target status within the timeout, otherwise return False.

    Parameters:
    - service_name (str): The name of the service.
    - target_status (str): The desired status to wait for ('running', 'stopped', 'paused').
    - timeout (int): The maximum time in seconds to wait for the service to reach the target status.

    Returns:
    - bool: True if the service reaches the target status within the timeout, otherwise False.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        current_status = query_service_status(service_name)
        if current_status == target_status:
            return True
        time.sleep(2)
    return False


def change_service_startup_type(name: str, startup_type: str) -> None:
    """
    Changes the startup type of Windows service using the 'sc config' command. The function first checks if the
    requested startup type is valid and then modifies the service if its current startup type differs from the requested
    one. Logs the outcome of each modification attempt.

    Parameters:
    - name (str): The name of the service.
    - startup_type (str): The desired startup type ('Automatic', 'Manual', 'Disabled', 'Automatic (Delayed Start)').
    """
    sc_startup_type = {
        "Automatic": "auto",
        "Manual": "demand",
        "Disabled": "disabled",
        "Automatic (Delayed Start)": "delayed-auto"
    }.get(startup_type)

    if sc_startup_type is None:
        logging.error(f"Invalid startup type '{startup_type}' for service '{name}'.")
        return

    current_startup_type = query_service_startup_type(name)
    if sc_startup_type == current_startup_type:
        logging.info(f"Service {name} is already in the desired startup type: {startup_type}.")
        return

    try:
        subprocess.check_output(["sc", "config", name, "start=", sc_startup_type], text=True, stderr=subprocess.DEVNULL)
        logging.info(f"Successfully changed startup type for {name} to {startup_type}.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to change startup type for {name}. Error: {e.output}")


def handle_service_state(name: str, desired_state: str) -> None:
    """
    Handles the state of a Windows service based on the desired action ('start', 'stop', 'pause', 'resume').
    It first validates the desired state, checks the current state of the service, and proceeds with the state change
    if necessary. It also verifies if pause and resume operations are supported for the service, and whether the
    startup type allows starting the service. It logs the outcome of the state change operation.

    Parameters:
    - name (str): The name of the service.
    - desired_state (str): The desired action for the service ('start', 'stop', 'pause', 'resume').
    """
    desired_state_map = {"start": "running", "stop": "stopped", "pause": "paused", "resume": "running"}
    target_status = desired_state_map.get(desired_state)

    if not target_status:
        logging.error(f"Invalid desired state '{desired_state}' for service '{name}'.")
        return

    current_status = query_service_status(name)
    if current_status == target_status:
        logging.info(f"Service {name} is already in the desired status: {desired_state}.")
        return

    pause_supported = False
    resume_supported = False
    output = subprocess.check_output(["sc", "qc", name], text=True)
    if "PAUSABLE" in output:
        pause_supported = True
    if "RESUME_PENDING" in output:
        resume_supported = True

    if desired_state == "pause" and not pause_supported:
        logging.error(f"Pause operation is not supported for service '{name}'.")
        return
    elif desired_state == "resume" and not resume_supported:
        logging.error(f"Resume operation is not supported for service '{name}'.")
        return

    startup_type = query_service_startup_type(name)
    if startup_type == "disabled" and desired_state == "start":
        logging.error(f"Cannot start service '{name}' because its startup type is Disabled.")
        return

    try:
        subprocess.run(["sc", desired_state, name], check=True, text=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        if wait_for_service_status(name, target_status):
            logging.info(f"Service {name} successfully changed to {desired_state}.")
        else:
            logging.error(f"Failed to change the status of {name} to {desired_state}.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error while attempting to change the state of {name} to {desired_state}: {e}")


def modify_windows_services(services_list: List[dict], enabled: bool) -> None:
    """
       Modifies the current state of a Windows service (start, stop, pause, resume) using the 'sc' command. The function
       first validates the requested state, checks the current state, and proceeds with the state change if necessary.
       It waits to confirm the state change and logs the outcome.

       Parameters:
       - name (str): The name of the service.
       - desired_state (str): The desired state action ('start', 'stop', 'pause', 'resume').
       """
    if not enabled:
        logging.info("Service modification is disabled.")
        return

    for service in services_list:
        name = service.get("name")
        startup_type = service.get("startupType")
        desired_state = service.get("serviceStatus").lower()

        change_service_startup_type(name, startup_type)
        handle_service_state(name, desired_state)


def main() -> None:
    """
    Executes the main functionality of the script which includes setting up logging, reading the configuration file,
    validating the 'servicesSettings' configuration section, and conditionally modifying services startup type and
    status based on the configuration.
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
