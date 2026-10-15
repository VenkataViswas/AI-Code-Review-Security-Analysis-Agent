### 1. `ast` (Abstract Syntax Trees)

The `ast` module processes Python code without executing it. It parses raw Python code into a tree structure representing its grammatical syntax.

#### Primary Uses

* **Syntax Validation:** Check for syntax errors before running a script.
* **Static Code Analysis & Linting:** Analyze code structure, detect unused imports, or build custom linters (e.g., Flake8, pylint).
* **Safe Code Evaluation:** Safely evaluate string literals using `ast.literal_eval()` instead of the dangerous `eval()`.
* **Code Modification / Refactoring:** Transform source code programmatically before execution using `ast.NodeTransformer`.

#### Key Functions

* `ast.parse(source)`: Parses source string into an AST root node. Throws `SyntaxError` if syntax is invalid.
---

### 2. `shutil` (Shell Utilities)

The `shutil` module provides high-level file operations. While `os` handles basic system calls (like `os.remove()` or `os.mkdir()`), `shutil` handles complete file/folder copying, moving, archiving, and system utility lookups.

#### Primary Uses

* **Copying Files & Folders:** Copy individual files or entire directory trees.
* **Moving & Renaming:** Move files/directories across paths or file systems.
* **Deleting Directories:** Recursively remove non-empty folders.
* **Finding System Executables:** Locate binaries registered in system environment paths (e.g., finding `javac` or `git`).
* **Archives:** Create or extract `.zip`, `.tar`, or `.gz` files.
