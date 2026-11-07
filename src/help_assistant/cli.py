"""The commands. Each milestone adds its own."""

import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="help-assistant", description=__doc__)
    parser.add_subparsers(dest="command", required=True)
    parser.parse_args(argv)
    return 0
