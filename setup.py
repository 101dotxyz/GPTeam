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


def is_docker_installed():
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
        print("✅ Docker is installed")
        return True
    except FileNotFoundError:
        return False
    except subprocess.CalledProcessError:
        return False


def install_poetry():
    install_cmd = "curl -sSL https://install.python-poetry.org | python3 -"
    os.system(install_cmd)

    poetry_bin_path = os.path.expanduser("~/.local/bin")
    if poetry_bin_path not in os.environ["PATH"]:
        os.environ["PATH"] = f"{poetry_bin_path}:{os.environ['PATH']}"


def is_supabase_cli_installed():
    try:
        result = subprocess.run(
            ["supabase", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def install_or_update_supabase_cli():
    # if is_supabase_cli_installed():
    #     print("Supabase CLI is already installed.")
    #     return

    os_type = platform.system()

    try:
        if os_type == "Windows":
            print("Installing Supabase CLI for Windows...")
            subprocess.run(
                [
                    "powershell.exe",
                    "scoop",
                    "bucket",
                    "add",
                    "supabase",
                    "https://github.com/supabase/scoop-bucket.git",
                ],
                check=True,
            )
            subprocess.run(
                ["powershell.exe", "scoop", "install", "supabase"], check=True
            )
            print("Supabase CLI installed successfully.")

        elif os_type == "Darwin" or os_type == "Linux":
            print("Installing Supabase CLI for Mac/Linux...")
            subprocess.run(["brew", "install", "supabase/tap/supabase"], check=True)
            print("Supabase CLI installed successfully.")

        else:
            print(f"Unsupported OS: {os_type}. Installation failed.")

    except subprocess.CalledProcessError as error:
        print(f"Installation failed with error: {error}")
        return


if __name__ == "__main__":
    os_type = platform.system()

    if os.environ.get("CI") == "true":
        # Skip user prompts when running in CI environment
        prompt = False
    else:
        prompt = True

    if os_type == "Windows":
        print(
            "⚠️ This setup script does not support Windows yet. Please follow the instructions in the README to set up the project."
        )

    if not is_docker_installed():
        print(
            "⚠️ Docker is not installed. Please install Docker and try again. See https://docs.docker.com/get-docker/ for instructions."
        )
        exit(1)

    if is_poetry_installed():
        print("✅ Poetry is already installed.")
    else:
        if prompt:
            answer = input(
                "⚠️ Poetry not found. Would you like to install it now? (y/n): "
            )
            if answer.lower() != "y":
                exit(1)

        print("🚀 Installing Poetry...")
        install_poetry()

    print("🎁 Installing dependencies... (this may take a while)")
    subprocess.run(["poetry", "install"], check=True)

if not is_supabase_cli_installed():
    if prompt:
        answer = input(
            "⚠️ Supabase CLI not found. Would you like to install it now? (y/n): "
        )
        if answer.lower() != "y":
            exit(1)

    print("🚀 Installing Supabase CLI...")
    install_or_update_supabase_cli()


print("Starting supabase...")
subprocess.run(["supabase", "start"], check=True)

print("Resetting the database...")
subprocess.run(["supabase", "db", "reset"], check=True)

print("🌱 Seeding database with agents...")
subprocess.run(["poetry", "run", "db-seed"], check=True)
