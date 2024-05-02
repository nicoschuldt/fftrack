import json

import os
import json

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


def load_config(config_file_path=DEFAULT_CONFIG_PATH):
    """
    Load configuration data from a JSON file.

    Args:
        config_file_path (str): Path to the JSON config file.

    Returns:
        dict: Configuration data.
    """
    if not os.path.exists(config_file_path):
        raise FileNotFoundError(f"Config file not found: {config_file_path}")
    with open(config_file_path, 'r') as f:
        config_data = json.load(f)
    return config_data


def save_config(config_data, config_file_path=DEFAULT_CONFIG_PATH):
    """
    Save configuration data to a JSON file.

    Args:
        config_data (dict): Configuration data to save.
        config_file_path (str): Path to the JSON config file. If None, use the default path.

    Returns:
        None
    """
    if config_file_path is None:
        config_file_path = DEFAULT_CONFIG_PATH
    with open(config_file_path, 'w') as f:
        json.dump(config_data, f, indent=4)
    return None
