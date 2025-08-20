import json
import os

CONFIG_PATH = "config.json"

def load_config():
    if not os.path.exists(CONFIG_PATH):
        print("Config file not found, creating default config.")
        default_config = {
            "downloads_folder": "C:/Users/Default/Downloads",
            "backup_folder": "C:/Users/Default/Backup"
        }
        save_config(default_config)
        return default_config
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=4)
    print("Config saved.")

def change_folder_location(config, key, new_path):
    if key in config:
        print(f"Changing '{key}' from '{config[key]}' to '{new_path}'")
        config[key] = new_path
        save_config(config)
    else:
        print(f"Setting '{key}' does not exist in config.")

def main():
    config = load_config()
    print("Current Config:", config)
    print("Location of donwloads: ", config['downloads_folder'])

    # Example: user changes folder location
    change_folder_location(config, "downloads_folder", "D:/NewDownloads")

    # Load again to confirm it's saved
    config = load_config()
    print("Updated Config:", config)

if __name__ == "__main__":
    main()
