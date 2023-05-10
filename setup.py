#!/usr/bin/env python3

import os
import platform
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

    print("Installing dependencies...")
    subprocess.run(["poetry", "install"], check=True)

    print("Seeding database with agents...")
    subprocess.run(["poetry", "run", "db-seed"], check=True)
