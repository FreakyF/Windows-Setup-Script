import subprocess
import time
from typing import List

from config_service import setup_logging, read_config_file, validate_config_section, logging

CONFIG_FILE = "config.json"

def query_service_startup_type(service_name: str) -> str:
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
    start_time = time.time()
    while time.time() - start_time < timeout:
        current_status = query_service_status(service_name)
        if current_status == target_status:
            return True
        time.sleep(2)
    return False

def change_service_startup_type(name: str, startup_type: str) -> None:
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
        subprocess.check_output(["sc", "config", name, "start=", sc_startup_type], text=True)
        logging.info(f"Successfully changed startup type for {name} to {startup_type}.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to change startup type for {name}. Error: {e.output}")

def handle_service_state(name: str, desired_state: str) -> None:
    desired_state_map = {"start": "running", "stop": "stopped", "pause": "paused", "resume": "running"}
    target_status = desired_state_map.get(desired_state)

    if not target_status:
        logging.error(f"Invalid desired state '{desired_state}' for service '{name}'.")
        return

    current_status = query_service_status(name)
    if current_status == target_status:
        logging.info(f"Service {name} is already in the desired status: {desired_state}.")
        return

    try:
        subprocess.run(["sc", desired_state, name], check=True, text=True)
        if wait_for_service_status(name, target_status):
            logging.info(f"Service {name} successfully changed to {desired_state}.")
        else:
            logging.error(f"Failed to change the status of {name} to {desired_state}.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error while attempting to change the state of {name} to {desired_state}: {e}")

def modify_windows_services(services_list: List[dict], enabled: bool) -> None:
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
