#!/usr/bin/env python3
"""Generate a strong SECRET_KEY and show commands to save it to environment.

Usage:
  python scripts/generate_secret.py [--write-dotenv]

Options:
  --write-dotenv   Write the generated key to a local .env file (overwrites if exists)
"""
import secrets
import argparse
import os


def generate_key(nbytes: int = 32) -> str:
    return secrets.token_hex(nbytes)


def print_instructions(key: str, write_dotenv: bool = False):
    print("Generated SECRET_KEY:\n")
    print(key)
    print()
    print("Commands to set in your environment:")
    print()
    print("PowerShell (current session):")
    print(f"  $env:SECRET_KEY = \"{key}\"")
    print()
    print("PowerShell (persist for current user):")
    print(f"  setx SECRET_KEY \"{key}\"")
    print()
    print("Windows CMD (current session):")
    print(f"  set SECRET_KEY={key}")
    print()
    print("Bash (current session):")
    print(f"  export SECRET_KEY=\"{key}\"")
    print()
    print("To persist on Bash, add the export line to ~/.bashrc or ~/.profile")
    print()
    if write_dotenv:
        dotenv_path = os.path.join(os.getcwd(), ".env")
        with open(dotenv_path, "w", encoding="utf-8") as f:
            f.write(f"SECRET_KEY={key}\n")
        print(f"Wrote .env to: {dotenv_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-dotenv", action="store_true", help="Write .env file in project root")
    args = parser.parse_args()
    key = generate_key()
    print_instructions(key, write_dotenv=args.write_dotenv)


if __name__ == "__main__":
    main()
