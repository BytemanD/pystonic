import argparse
import os


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_check = subparsers.add_parser("check")
    parser_check.add_argument(
        "--test", action="store_true", help="Run tests with pytest"
    )

    args = parser.parse_args()

    if args.command == "check":
        commands = ["ruff format src tests", "ruff check --fix src tests"]
        if args.test:
            commands.append("pytest")
        for command in commands:
            print(f"###### {command} ######")
            os.system(command)


if __name__ == "__main__":
    main()
