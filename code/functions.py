import sys
import re
import subprocess
import os
import json
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
import pyperclip

def check_api(config):
    if config["api_key"] == "":
        return True


def set_api_key(config, config_path):
    console = Console()
    console.print("API key is not set." , style="bold red")
    console.print("Go to [link https://mdb.ai/llm-serve]MindsDB, get you API Key and enter it: ", style="green",end="")
    api_key = input()
    config["api_key"] = api_key
    with open(config_path, "w") as file:
        json.dump(config, file, indent=4)


def load_config(config_path):
    if not os.path.exists(config_path):
        create_default_config(config_path)

    with open(config_path, "r") as file:
        return json.load(file)


def create_default_config(config_path):
    default_config = {
        "api_key": "",
        "llm": "gpt-3.5-turbo",
        "llm_customizer_message": "You are a helpful assistant.",
        "user_message_color": "bold blue",
        "user_message_border_color": "blue",
        "ai_answer_color": "white",
        "ai_answer_border_color": "green"
    }
    with open(config_path, "w") as file:
        json.dump(default_config, file, indent=4)


def ai_generate(api_key, llm, prompt):
    client = OpenAI(
        api_key=api_key,
        base_url="https://llm.mdb.ai/"
    )
    completion = client.chat.completions.create(
        model=llm,
        messages=prompt,
        stream=False
    )
    return completion.choices[0].message.content[:-1]


def open_vim_and_get_input(filename="input.txt"):
    subprocess.run(["vim", filename])
    with open(filename, "r") as file:
        data = file.read()
    os.remove(filename)
    return data
    

def print_panel(console, content, color, border_color, title):
    panel = Align.center(
        Panel(
            Text(content, style=color),
            border_style=border_color,
            title=title,
        ),
        vertical="middle",
    )
    console.print(panel)


def parse_ai_response(user_input, response, ai_answer_color):
    # response = re.sub(r'\*\*(.*?)\*\*', r'\033[1m\1\033[0m', response)
    response = "\n" + response
    response_parts = response.split("```")

    text_obj = Text()
    for part in response_parts:
        if not part.startswith("\n"):
            if re.search(r"^[\sa-z]", part):
                x = re.search(r"^(\w*\s)", part).end()
                text_obj.append(part[x:-1], style="magenta")
                if "<copy_code_blocks>" in user_input:
                    pyperclip.copy(part[x:-1])
        else:
            text_obj.append(part, style=ai_answer_color)

    return text_obj


def interactive_mode(console, api_key, llm, config):
    messages = [
        {
            "role": "system",
            "content": config["llm_customizer_message"],
        },
    ]
    while True:
        user_input = input("\033[1m\033[94mYou: \033[0m ")
        if "<p>" in user_input:
            user_input = re.sub("<p>", pyperclip.paste(), user_input)
        print("\033[F", end="")
        print("\033[k", end="")

        if user_input.lower() == "exit":
            break

        if user_input.lower() == "vim":
            user_input = open_vim_and_get_input()[:-1]

        messages.append({"role": "user", "content": user_input})

        print_panel(console, user_input, config["user_message_color"], config["user_message_border_color"], "You")

        response = ai_generate(api_key, llm, messages)
        messages.append({"role": "assistant", "content": response})
        if "<c>" in user_input:
            pyperclip.copy(response)

        text_obj = parse_ai_response(user_input, response, config["ai_answer_color"])
        panel_content = Panel(text_obj[1:], border_style=config["ai_answer_border_color"], title=config["llm"])
        console.print(panel_content)


def handle_cli_args(args, config, config_path):
    if args[1] == "list":
        print("""claude-3-haiku
codellama-70b
dbrx
gemma-7b
gpt-3.5-turbo
hermes-2-pro
llama-3-70b
llama-3-8b
mistral-7b
mixtral-8x7b
gemini-1.5-pro
text-embedding-ada-002""")
    elif args[1] == "config":
        if args[2] == "show":
            print(json.dumps(config, indent=4))
        elif args[2] == "change":
            if args[3] not in config.keys():
                print(f"{args[3]} is not a valid key")
                sys.exit(1)
            config[args[3]] = " ".join(args[4:])
            with open(config_path, "w") as file:
                json.dump(config, file, indent=4)


# def main():
#     config_path = "/home/korvus/code/.config"
#     config = load_config(config_path)
#     api_key = config["api_key"]
#     llm = config["llm"]
# 
#     console = Console()
# 
#     if len(sys.argv) == 1:
#         interactive_mode(console, api_key, llm, config)
#     else:
#         handle_cli_args(sys.argv, config)
# 
# 
# if __name__ == "__main__":
#     main()
