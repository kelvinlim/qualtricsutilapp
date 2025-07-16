# qualtrics_util.py
import yaml
import os

def check_connection(token_file_path, config_file_path):
    """
    Simulates checking the connection to Qualtrics using provided config files.
    
    Args:
        token_file_path (str): Path to the qualtrics_token.yaml file.
        config_file_path (str): Path to the project_config.yaml file.

    Returns:
        tuple: A tuple containing (bool, str) for success/failure and a message.
    """
    # --- Input Validation ---
    if not token_file_path or not os.path.exists(token_file_path):
        return False, "Qualtrics token file not found or path is not set."
        
    if not config_file_path or not os.path.exists(config_file_path):
        return False, "Project config file not found or path is not set."

    # --- Placeholder Logic ---
    # In a real application, you would parse these files and use the
    # credentials to make an API call to Qualtrics.

    qualtrics_token_name = 'QUALTRICS_APITOKEN'
    try:
        print(f"Attempting to read token from: {token_file_path}")
        with open(token_file_path, 'r') as f:
            token_data = yaml.safe_load(f)
            # Example: check for a specific key
            if not token_data or qualtrics_token_name not in token_data:
                 return False, f"YAML is valid, but {qualtrics_token_name} key is missing in the token file."

        print(f"Attempting to read config from: {config_file_path}")
        with open(config_file_path, 'r') as f:
            config_data = yaml.safe_load(f)
            if not config_data or 'project_id' not in config_data:
                return False, "YAML is valid, but 'project_id' key is missing in the config file."

        print("--- Simulation: Pretending to make an API call... ---")
        # Simulate a successful connection
        print("Successfully connected to Qualtrics API.")
        return True, "Successfully connected to Qualtrics and validated configuration."

    except yaml.YAMLError as e:
        return False, f"Failed to parse a YAML file. Please check its syntax.\nError: {e}"
    except Exception as e:
        return False, f"An unexpected error occurred: {e}"

