# Python Coding Style Rules

## General Philosophy
- Prefer simple, straightforward implementations over complex abstractions
- Focus on readability and maintainability
- Write code that is easy to test and debug

## Programming Paradigm
- Prefer functional programming over object-oriented programming
- Avoid classes unless absolutely necessary
- Use pure functions when possible
- Minimize state and side effects

## Code Structure
- Write modular functions with single responsibilities
- Keep functions focused and relatively short
- Use descriptive function and variable names
- Include clear docstrings for functions using Google style
- Place main execution code under `if __name__ == '__main__':`

## Dependencies
- Prefer standard library modules over external dependencies
- Avoid complex frameworks unless essential
- Use simple, well-established libraries when needed
- Explicitly import required modules at the top

## Error Handling
- Use explicit error handling with try/except blocks
- Specify exact exceptions to catch
- Include helpful error messages
- Document expected exceptions in docstrings

## Code Formatting
- Follow PEP 8 guidelines
- Use 4 spaces for indentation
- Maximum line length of 100 characters
- Use meaningful whitespace to group related code

## File Organization
- One function per logical operation
- Clear separation between utility functions and main logic
- Command-line argument parsing at the bottom of the file
- Organize imports: standard library first, then third-party

## Code Assistant Interactions
- Show code changes as incremental, step-by-step suggestions
- Present one code block or modification at a time
- Allow manual implementation of each suggested change
- Explain the purpose of each modification before showing the code
- Wait for confirmation before proceeding to next change
- Focus on small, manageable chunks of code
- Maintain user control over all code modifications

## Command-Line Output Style
- Use concise, professional output messages
- Employ color coding for different message types (error, warning, info)
- Maintain clean, minimal output formatting
- Avoid emojis and decorative characters
- Skip progress bars unless download/processing time exceeds 5 seconds
- Present data in simple, readable tables when needed
- Use professional, neutral language in output messages:
    - Correct: "Processing complete"
    - Avoid: "Awesome! Processing finished!!!"
- Keep error messages informative but brief
- Format log messages consistently
- Reserve stdout for actual output, use stderr for status/error messages
- Limit output to what's necessary for the user to understand the tool's operation

## Type Hints and Type Checking
- Use type hints for all function parameters and return values
- Employ type hints for complex variables where type is not obvious
- Include type checking in development workflow using mypy
- Use Optional[] for parameters that may be None
- Prefer builtin types (str, int, list, dict) in type hints
- Use collections.abc for container types (Sequence, Mapping)
- Keep type hints readable - use line breaks for complex types
- Document any type-related assumptions in docstrings
- Use Union[] sparingly - prefer designing functions to accept specific types
- Validate input types at function boundaries when necessary

## Script Execution
- Start command-line tool scripts with proper shebang line:
    ```python
    #!/usr/bin/env python3
    ```
- Make scripts executable using `chmod +x script.py`
- Allow direct execution without `python` command prefix
- Include encoding declaration if needed: `# -*- coding: utf-8 -*-`
- Place license/copyright notice after shebang if required
- Keep script headers clean and minimal
- Use `argparse` for command-line argument parsing
- Include a `--help` option for usage information
- Provide clear error messages for invalid arguments
- Exit with appropriate status codes (0 for success, 1 for errors)

## HTTP Request Handling
- Use the Requests library for HTTP operations
- Include standard security-related CLI arguments:
    - `-k` or `--insecure`: Sets `verify=False` in Requests
    - `--burp`: Routes traffic through Burp Suite proxy (http://localhost:8080)
- When verify=False is used, suppress insecure request warnings:
    ```python
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    ```
- Configure Burp proxy settings when --burp is used:
    ```python
    proxies = {"http": "http://localhost:8080", "https": "http://localhost:8080"}
    requests.get(url, proxies=proxies)
    ```
- Maintain consistent HTTP request configuration across the codebase
- Handle HTTP errors gracefully with appropriate status messages
- Include request timeout settings
- Log relevant request/response details at debug level
- Command line tools that make HTTP requests should provide the user with a runtime option to specify a custom `User-Agent` header, defaulting to a generic one named after the tool name if not specified:
    ```python
    headers = {"User-Agent": "MyTool/1.0"}
    requests.get(url, headers=headers)
    ```

## Output Formatting and Colors
- Choose output formatting library based on needs:
    1. Rich: For complex Markdown/JSON/code output with advanced formatting
    2. Colorama: For basic color and simple formatting needs
    3. ANSI codes: For minimal dependencies and basic color output
- When using ANSI codes, define color constants at file top:
    ```python
    RED = '\033[31m'
    GREEN = '\033[32m'
    RESET = '\033[0m'
    ```
- Use consistent color scheme across the application:
    - Red: Errors
    - Yellow: Warnings
    - Green: Success
    - Blue: Information
- Keep color usage minimal and purposeful
- Ensure all colored output includes reset codes
- Consider colorblind accessibility in color choices
- Provide option to disable colors (e.g., `--no-color` flag)
- Use color output only in terminal environments that support it
- Avoid using colors in logs or files, reserve them for terminal output

## Project Structure and Repository
- Create dedicated directory for each significant Python project (10+ lines)
- Name project directory similarly to main tool script
- Initialize project components:
    ```
    project_name/
    ├── venv/              # Virtual environment
    ├── .git/              # Git repository
    ├── README.md          # Project documentation
    ├── .gitignore        # Git ignore rules
    └── project_name.py   # Main tool script
    ```
- Include standard `.gitignore` entries:
    ```
    venv/
    .idea/
    .vscode/
    __pycache__/
    *.pyc
    *.pyo
    *.pyd
    .Python
    .env
    .coverage
    ```
- Maintain current README.md:
    - Update with new features
    - Document changes to existing functionality
    - Keep installation and usage sections current
- Create virtual environment using:
    ```bash
    python3 -m venv venv
    ```

## Secrets and Security
- Never hardcode secrets in source code or config files
- Manage secrets using 1Password:
    - Prefer direct Python integration with 1Password if available
    - Otherwise use `op` CLI to export secrets to environment variables:
        ```bash
        export SECRET=$(op read "op://vault/item/field")
        ```
- Access secrets in code through environment variables:
    ```python
    import os
    secret = os.getenv('SECRET')
    if not secret:
        raise ValueError("Required secret not found in environment")
    ```
- Security checks:
    - Run Semgrep scan before each GitHub push
    - Add pre-commit hook:
        ```bash
        semgrep scan --config=auto
        ```
- Additional security practices:
    - Use `.env` files only for non-sensitive configuration
    - Add `*.env` to `.gitignore`
    - Document secret requirements in README.md
    - Log secret usage without exposing values
    - Rotate secrets regularly

## Testing
- Use Python's built-in `unittest` framework for basic testing:
    ```python
    import unittest

    def add(a: int, b: int) -> int:
        return a + b

    class TestBasicFunctions(unittest.TestCase):
        def test_add(self):
            self.assertEqual(add(2, 2), 4)
            self.assertEqual(add(-1, 1), 0)
    ```
- Run tests from command line:
    ```bash
    python -m unittest discover tests/
    ```
- Basic test structure:
    - Place tests in `tests/` directory
    - Name test files with `test_` prefix
    - One test class per source file
    - Test method names start with `test_`
- Minimum test coverage:
    - Test main function arguments
    - Test error conditions
    - Test edge cases (empty input, invalid input)
- Use `pytest` for simpler test writing:
    ```python
    def test_add():
        assert add(2, 2) == 4
        assert add(-1, 1) == 0
    ```
- Continue using PyCharm's built-in test runner
- Include test instructions in README.md
