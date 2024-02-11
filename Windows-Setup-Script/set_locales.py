import winreg as reg

from config_service import setup_logging, read_config_file, validate_config_section, logging

CONFIG_FILE = "config.json"
KEY_PATH = r"Control Panel\International"


def modify_locale(settings: dict, enabled: bool) -> None:
    if not enabled:
        logging.info("Registry modification is skipped as it's disabled by configuration.")
        return

    try:
        with reg.OpenKey(reg.HKEY_CURRENT_USER, KEY_PATH, 0, reg.KEY_WRITE | reg.KEY_READ) as key:
            for setting, setting_info in settings.items():
                if not setting_info.get('enabled', False):
                    logging.info(f"Registry setting '{setting}' is disabled in configuration. Skipping...")
                    continue

                new_value = setting_info.get('value')
                try:
                    current_value, _ = reg.QueryValueEx(key, setting)
                    if current_value == new_value:
                        logging.info(f"Registry setting '{setting}' already set to '{new_value}'. Skipping...")
                        continue
                    else:
                        reg.SetValueEx(key, setting, 0, reg.REG_SZ, new_value)
                        logging.info(f"Registry setting '{setting}' changed to '{new_value}'.")
                except FileNotFoundError:
                    logging.info(f"Registry setting '{setting}' does not exist. Skipping...")

    except Exception as e:
        logging.error(f"Failed to modify registry: {str(e)}")


def main() -> None:
    setup_logging()
    config_data = read_config_file(CONFIG_FILE)

    if not config_data:
        logging.error("Failed to read the configuration file.")
        return

    locale_settings_keys = [
        {'key': 'enabled', 'type': bool},
        {'key': 'formatOptions', 'type': dict}
    ]
    if not validate_config_section(config_data.get("localeSettings", {}), locale_settings_keys):
        logging.error("The 'localeSettings' section in the configuration is invalid.")
        return

    modify_locale(config_data["localeSettings"]["formatOptions"], config_data["localeSettings"]["enabled"])


if __name__ == "__main__":
    main()
