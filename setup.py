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


def install_supabase_cli():
    # if is_supabase_cli_installed():
    #     print("Supabase CLI is already installed.")
    #     return

    os_type = platform.system()
    arch_type = platform.machine()

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
            if os_type == "Darwin" and arch_type == "arm64":
                subprocess.run(
                    ["arch", "-arm64", "brew", "install", "supabase/tap/supabase"],
                    check=True,
                )
            else:
                subprocess.run(["brew", "install", "supabase/tap/supabase"], check=True)
            print("Supabase CLI installed successfully.")

        else:
            print(f"Unsupported OS: {os_type}. Installation failed.")

    except subprocess.CalledProcessError as error:
        print(f"Installation failed with error: {error}")
        return


def setup_db():
    install_supabase_cli()

    print("Starting supabase...")
    subprocess.run(["supabase", "start"], check=True)

    print("Resetting the database...")
    subprocess.run(["supabase", "db", "reset"], check=True)

    print("🌱 Seeding database with agents...")
    subprocess.run(["poetry", "run", "db-seed"], check=True)


if __name__ == "__main__":
    os_type = platform.system()

    if os_type == "Windows":
        print(
            "⚠️ This setup script does not support Windows yet. Please follow the instructions in the README to set up the project."
        )

    if is_poetry_installed():
        print("✅ Poetry is already installed.")
    else:
        print("⏳ Poetry not found, installing...")
        install_poetry()

    print("🎁 Installing dependencies... (this may take a while)")
    subprocess.run(["poetry", "install"], check=True)

    setup_db()
