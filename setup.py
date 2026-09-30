#!/usr/bin/env python3

import os
import platform
import shutil
import subprocess


def is_poetry_installed():
    try:
        subprocess.run(["poetry", "--version"], capture_output=True, check=True)
        return True
    except FileNotFoundError:
        return False
    except subprocess.CalledProcessError:
        return False


def install_poetry():
    install_cmd = "curl -sSL https://install.python-poetry.org | python3 -"

    os.system(install_cmd)

    if os_type == "Windows":
        poetry_bin_path = os.path.expanduser("~\\AppData\\Roaming\\Python\\Scripts")
    else:
        poetry_bin_path = os.path.expanduser("~/.local/bin")

    if poetry_bin_path not in os.environ["PATH"]:
        if os_type == "Windows":
            os.environ["PATH"] = f"{poetry_bin_path};{os.environ['PATH']}"
        else:
            os.environ["PATH"] = f"{poetry_bin_path}:{os.environ['PATH']}"


def copy_env_file_if_missing(env_example_path=".env.example", env_file_path=".env"):
    if not os.path.exists(env_file_path):
        print("Creating .env file...")
        shutil.copyfile(env_example_path, env_file_path)


if __name__ == "__main__":
    os_type = platform.system()

    if os.environ.get("CI") == "true":
        # Skip user prompts when running in CI environment
        prompt = False
    else:
        prompt = True

    if is_poetry_installed():
        print("Poetry is already installed.")
    else:
        if prompt:
            answer = input(
                "⚠️ Poetry not found. Would you like to install it now? (y/n): "
            )
            if answer.lower() != "y":
                exit(1)

        print("Installing Poetry...")
        install_poetry()

    # Copy .env.example to .env without relying on a platform-specific command.
    copy_env_file_if_missing()

    print("Installing dependencies...")
    subprocess.run(["poetry", "install"], check=True)

    print("Seed the database...")
    subprocess.run(["poetry", "run", "db-reset"], check=True)

    print(
        "\nSetup complete!\n\n-> You are ready to run the world. Please set your OPENAI_API_KEY in .env and run `poetry run world` to get started."
    )
