from functions import *

def main():

    username = os.getlogin()
    if check_os() == "windows":
        config_path = f"C:/Users/{username}/kpai_config"
    elif check_os() == "linux":
        config_path = f"/home/{username}/.kpai_config"
    config = load_config(config_path)
    if check_api(config):
        set_api_key(config, config_path)
        sys.exit(1)
    api_key = config["api_key"]
    llm = config["llm"]

    console = Console()

    if len(sys.argv) == 1:
        interactive_mode(console, api_key, llm, config)
    else:
        handle_cli_args(sys.argv, config, config_path)


if __name__ == "__main__":
    main()
