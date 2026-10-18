#!/usr/bin/env python3
"""Manage local keyenv without displaying key values or modifying projects."""

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys


KEY_NAMES = (
    "DEEPSEEK_API_KEY",
    "MOONSHOT_API_KEY",
    "ZHIPU_API_KEY",
    "DASHSCOPE_API_KEY",
    "ARK_API_KEY",
    "DOUBAO_VOICE_API_KEY",
    "MINIMAX_API_KEY",
)
KEYENV_PATH = Path.home() / ".call-llm" / "keyenv"
KEY_LINE = re.compile(r"^([A-Z][A-Z0-9_]*)=(.*)$")


def initialize(path=KEYENV_PATH):
    """Create a blank file once, without replacing existing credentials."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError("keyenv must not be a symbolic link")
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        if not path.is_file():
            raise ValueError("keyenv path is not a regular file") from None
        return False
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
        stream.write("# Local Call LLM credentials. Fill only the keys you need.\n")
        stream.write("# Never commit, paste, or share this file.\n")
        for name in KEY_NAMES:
            stream.write(f"{name}=\n")
    return True


def read_keys(path=KEYENV_PATH):
    """Parse plain KEY=value lines; do not execute shell syntax."""
    if path.is_symlink() or not path.is_file():
        raise ValueError("keyenv is missing or is not a regular file; run init first")
    result = {}
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = KEY_LINE.fullmatch(line)
        if not match or match.group(1) not in KEY_NAMES:
            raise ValueError(f"invalid keyenv field on line {number}")
        name, value = match.groups()
        if name in result:
            raise ValueError(f"duplicate keyenv field on line {number}: {name}")
        # A pair of surrounding quotes is accepted for ordinary copy/paste.
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        result[name] = value
    return result


def run(command, requested, path=KEYENV_PATH):
    if not command:
        raise ValueError("a command is required after --")
    if not requested or any(name not in KEY_NAMES for name in requested):
        raise ValueError("select at least one supported --key")
    stored = read_keys(path)
    environment = os.environ.copy()
    for name in KEY_NAMES:
        if name not in requested:
            environment.pop(name, None)
    for name in requested:
        if not environment.get(name):
            value = stored.get(name, "")
            if not value:
                raise ValueError(f"{name} is not configured")
            environment[name] = value
    return subprocess.run(command, env=environment, check=False).returncode


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="action", required=True)
    subcommands.add_parser("init", help="create an empty local keyenv once")
    subcommands.add_parser("status", help="show configured variable names, never values")
    runner = subcommands.add_parser("run", help="pass selected keys to a child process")
    runner.add_argument("--key", action="append", dest="keys", required=True, choices=KEY_NAMES)
    runner.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        if args.action == "init":
            created = initialize()
            print(f"{'Created' if created else 'Already exists'}: {KEYENV_PATH}")
            return 0
        if args.action == "status":
            stored = read_keys()
            for name in KEY_NAMES:
                print(f"{name}: {'set' if stored.get(name) else 'missing'}")
            return 0
        command = args.command[1:] if args.command and args.command[0] == "--" else args.command
        return run(command, args.keys)
    except (OSError, ValueError) as error:
        print(f"keyenv: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
