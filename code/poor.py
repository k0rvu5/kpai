import sys
import re
import subprocess
import os
import json
from openai import OpenAI
import pyperclip

colors = {
    "gray":"\033[90m", 
    "red":"\033[91m", 
    "green":"\033[92m", 
    "yellow":"\033[93m", 
    "blue":"\033[94m", 
    "magenta":"\033[95m", 
    "cyan":"\033[96m", 
    "boldgray":"\033[30m", 
    "boldred":"\033[31m", 
    "boldgreen":"\033[32m", 
    "boldyellow":"\033[33m", 
    "boldblue":"\033[34m", 
    "boldmagenta":"\033[35m", 
    "boldcyan":"\033[36m", 
    "default":"\033[0m",
}

def check_os():
    if sys.platform == "win32":
        return "windows"
    elif sys.platform == "darwin":
        return "macos"
    elif sys.platform == "linux":
        return "linux"
    else:
        return "unknown"

def check_api(config):
    if config["api_key"] == "":
        return True


def set_api_key(config, config_path):
    print(colors["red"], "API key is not set.")
    print(colors["green"], "Go to [link https://mdb.ai/llm-serve]MindsDB, get you API Key and enter it: ")
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


def ai_generate(api_key, llm, prompt, config):
    client = OpenAI(
        api_key=api_key,
        base_url="https://llm.mdb.ai/"
    )
    completion = client.chat.completions.create(
        model=llm,
        messages=prompt,
        stream=False
    )
    if config["llm"] == "gemini-1.5-pro":
        return completion.choices[0].message.content[:-1]
    else:
        return completion.choices[0].message.content


def open_vim_and_get_input(filename="input.txt"):
    subprocess.run(["vim", filename])
    with open(filename, "r") as file:
        data = file.read()
    os.remove(filename)
    return data
    

def parse_ai_response(text, user_input):
    pattern = r"```\w+(.*?)```"
    replacement = r"\033[95m\g<1>\033[0m"
    text = re.sub(pattern, replacement, text, flags=re.DOTALL)
    pattern = r"\*\*(.*?)\*\*"
    replacement = r"\033[36m\g<1>\033[0m"
    text = re.sub(pattern, replacement, text, flags=re.DOTALL)
    pattern = r"`(.*?)`"
    replacement = r"\033[92m\g<1>\033[0m"
    text = re.sub(pattern, replacement, text, flags=re.DOTALL)
    text = text.replace("*", "%s*%s" % (colors["boldmagenta"], colors["default"]))

    # if "<p>" in user_input.lower():
    #     clipboard = pyperclip.paste()
    #     user_input = user_input.replace("<p>", clipboard)
    
    return text


def interactive_mode(api_key, llm, config):
    messages = [
        {
            "role": "system",
            "content": config["llm_customizer_message"],
        },
    ]
    while True:
        copy_response = False
        user_input = input("%sYou: %s" % (colors["boldyellow"], colors["default"]))
        if "<p>" in user_input:
            user_input = re.sub("<p>", pyperclip.paste(), user_input)
        if "<c>" in user_input:
            user_input = re.sub("<c>", "", user_input)
            copy_response = True
        if "<cb>" in user_input:
            user_input = re.sub(r"\s*<cb>\s*", "", user_input)
            

        if user_input.lower() == "exit" or user_input.lower() == "q":
            break
        
        if user_input.lower() == "save":
            save_chat_name = input("Enter a name for this chat: ")
            messages.insert(0, config["llm"])
            with open("%s.json" % save_chat_name, "w") as file:
                json.dump(messages, file, indent=4)
            print("%sFile saved successfuly!" % colors["green"])
            break

        if user_input.lower() == "vim":
            user_input = open_vim_and_get_input()[:-1]

        messages.append({"role": "user", "content": user_input})

        # print_panel(console, user_input, config["user_message_color"], config["user_message_border_color"], "You")
        # print("%sYou: %s%s" % (colors["boldcyan"], colors["default"], user_input))
        response = ai_generate(api_key, llm, messages, config)
        messages.append({"role": "assistant", "content": response})
        
        if copy_response:
            pyperclip.copy(response)

        text_obj = parse_ai_response(response, user_input)
        if config["llm"] == "gpt-3.5-turbo":
            print("%sGPT: %s%s" % (colors["boldred"], colors["default"],text_obj))
        elif config["llm"] == "claude-3-haiku":
            print("%sClaude: %s%s" % (colors["boldred"], colors["default"],text_obj))
        elif config["llm"] == "gemini-1.5-pro":
            print("%sGemini: %s%s" % (colors["boldred"], colors["default"],text_obj))
        elif config["llm"] == "llama-3-70b":
            print("%sLlama: %s%s" % (colors["boldred"], colors["default"],text_obj))

def handle_cli_args(args, config, config_path):
    if args[1] == "help":
        print("""kpai help:""")
    elif args[1] == "list":
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
    elif args[1] == "show":
        print(json.dumps(config, indent=4))
    elif args[1] == "read":
        jsonname = args[2]
        with open(jsonname, "r") as file:
            messages_list = json.load(file)
            print("%sLLM%s: %s" % (colors["boldgreen"], colors["default"], messages_list[0]))
            messages_list = messages_list[1:]
            for i in messages_list:
                if i["role"] == "system":
                    print("%s%s%s: %s" % (colors["boldcyan"], i["role"], colors["default"], i["content"]))
                elif i["role"] == "user":
                    print("%s%s%s: %s" % (colors["boldyellow"], i["role"], colors["default"], i["content"]))
                elif i["role"] == "assistant":
                    print("%s%s%s: %s" % (colors["boldred"], i["role"], colors["default"], i["content"]))

    elif args[1] == "set":
        if args[2] not in config.keys():
            print(f"{args[2]} is not a valid key")
            sys.exit(1)
        config[args[2]] = " ".join(args[3:])
        with open(config_path, "w") as file:
            json.dump(config, file, indent=4)
