import argparse
import logging
import json
import yaml
import os
import jsonschema
from jsonschema import validate
from jsonschema.exceptions import ValidationError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def setup_argparse():
    """
    Sets up the argument parser for the command-line interface.
    """
    parser = argparse.ArgumentParser(description='Validates configuration files against a schema or best practice rules.')
    parser.add_argument('config_file', help='Path to the configuration file (YAML or JSON).')
    parser.add_argument('--schema_file', help='Path to the JSON schema file.  If not provided, basic validation is performed.')
    parser.add_argument('--format', choices=['json', 'yaml'], help='Specify the format of the configuration file. If not given, it will be inferred from the file extension.')
    parser.add_argument('--best_practice', action='store_true', help='Enable best practice validation (e.g., check for insecure configurations).')  # Add best practice flag
    return parser.parse_args()


def load_config_file(config_file, format=None):
    """
    Loads the configuration file from the given path.

    Args:
        config_file (str): Path to the configuration file.
        format (str, optional):  The format of the config file ('json' or 'yaml'). If None, attempts to determine it from extension.

    Returns:
        dict: The configuration data as a dictionary.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        ValueError: If the file format is not supported or cannot be determined.
        Exception: If there's an error during file reading or parsing.
    """
    try:
        with open(config_file, 'r') as f:
            if format is None:
                if config_file.lower().endswith('.json'):
                    format = 'json'
                elif config_file.lower().endswith('.yaml') or config_file.lower().endswith('.yml'):
                    format = 'yaml'
                else:
                    raise ValueError("Could not determine file format.  Please specify with --format")

            if format == 'json':
                try:
                    config_data = json.load(f)
                except json.JSONDecodeError as e:
                    raise Exception(f"Error decoding JSON file: {e}")
            elif format == 'yaml':
                try:
                    config_data = yaml.safe_load(f)
                except yaml.YAMLError as e:
                    raise Exception(f"Error decoding YAML file: {e}")
            else:
                raise ValueError("Unsupported file format.  Must be JSON or YAML.")

            return config_data
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    except ValueError as e:
        raise ValueError(str(e))
    except Exception as e:
        raise Exception(f"Error loading configuration file: {e}")


def load_schema_file(schema_file):
    """
    Loads the JSON schema file from the given path.

    Args:
        schema_file (str): Path to the JSON schema file.

    Returns:
        dict: The schema data as a dictionary.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        Exception: If there's an error during file reading or parsing.
    """
    try:
        with open(schema_file, 'r') as f:
            try:
                schema_data = json.load(f)
                return schema_data
            except json.JSONDecodeError as e:
                raise Exception(f"Error decoding schema file: {e}")
    except FileNotFoundError:
        raise FileNotFoundError(f"Schema file not found: {schema_file}")
    except Exception as e:
        raise Exception(f"Error loading schema file: {e}")


def validate_with_schema(config_data, schema_data):
    """
    Validates the configuration data against the provided JSON schema.

    Args:
        config_data (dict): The configuration data to validate.
        schema_data (dict): The JSON schema to validate against.

    Returns:
        bool: True if the configuration is valid, False otherwise.
        str: An empty string if validation is successful, otherwise an error message.
    """
    try:
        validate(instance=config_data, schema=schema_data)
        return True, ""
    except ValidationError as e:
        return False, str(e)
    except jsonschema.exceptions.SchemaError as e:
        return False, f"Schema error: {str(e)}"
    except Exception as e:
        return False, f"An unexpected error occurred during schema validation: {str(e)}"


def perform_best_practice_validation(config_data):
    """
    Performs best practice validation on the configuration data.  This is a placeholder;
    actual best practice checks should be implemented here.

    Args:
        config_data (dict): The configuration data to validate.

    Returns:
        bool: True if best practices are followed, False otherwise.
        str: An empty string if validation is successful, otherwise an error message.
    """
    # Placeholder for best practice checks.
    # Add your specific checks here (e.g., check for default passwords, insecure settings, etc.).
    errors = []

    if "api_key" in config_data and config_data["api_key"] == "YOUR_API_KEY":
      errors.append("Warning: API key is set to the default value. Please update to a secure value.")

    if len(errors) > 0:
        return False, "\n".join(errors)
    else:
        return True, ""


def main():
    """
    Main function to execute the configuration file validation.
    """
    args = setup_argparse()

    try:
        config_data = load_config_file(args.config_file, args.format)
        logging.info(f"Configuration file loaded: {args.config_file}")

        if args.schema_file:
            schema_data = load_schema_file(args.schema_file)
            logging.info(f"Schema file loaded: {args.schema_file}")

            is_valid, message = validate_with_schema(config_data, schema_data)
            if is_valid:
                logging.info("Configuration file is valid against the schema.")
            else:
                logging.error(f"Configuration file is invalid against the schema: {message}")
                exit(1)  # Exit with an error code if validation fails
        else:
            logging.info("No schema file provided, skipping schema validation.")

        if args.best_practice:
          is_valid, message = perform_best_practice_validation(config_data)
          if is_valid:
              logging.info("Configuration file passes best practice validation.")
          else:
              logging.warning(f"Configuration file failed best practice validation: {message}")
              # Don't exit, just warn. It is common to enable best practice check but not mandate
        else:
            logging.info("Best practice validation skipped.")

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        exit(1)


if __name__ == "__main__":
    main()


# Example usage:
# Create a sample JSON config file named config.json:
# {
#   "name": "My Application",
#   "version": "1.0.0",
#   "debug": true,
#   "api_key": "YOUR_API_KEY"
# }

# Create a sample JSON schema file named schema.json:
# {
#   "type": "object",
#   "properties": {
#     "name": { "type": "string" },
#     "version": { "type": "string" },
#     "debug": { "type": "boolean" },
#     "api_key": { "type": "string" }
#   },
#   "required": ["name", "version"]
# }

# Run the validator with the schema:
# python main.py config.json --schema_file schema.json --best_practice

# Run the validator without a schema to skip schema validation:
# python main.py config.json --best_practice

#  Run the validator without schema or best practices
# python main.py config.json