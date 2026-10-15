from pathlib import Path

IGNORE_DIRS = {".venv", ".git", "__pycache__", ".github", "models"}


def print_tree(directory: Path, prefix: str = ""):
    contents = sorted(directory.iterdir(), key=lambda x: (x.is_file(), x.name))

    for i, path in enumerate(contents):
        is_last = i == len(contents) - 1
        connector = "└── " if is_last else "├── "
        print(prefix + connector + path.name)

        if path.is_dir():
            if path.name in IGNORE_DIRS:
                continue

            extension = "    " if is_last else "│   "
            print_tree(path, prefix + extension)


if __name__ == "__main__":
    print_tree(Path("."))
