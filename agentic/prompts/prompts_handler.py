from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "templates"


def load_prompt_template(template_name: str = "prompt.md") -> str:
    """
    Reads a markdown prompt template from the templates directory and returns its content as a string.

    Args:
        template_name (str): Name of the template file in the templates directory.

    Returns:
        str: The raw prompt string loaded from the markdown template.
    """
    template_path = TEMPLATES_DIR / template_name
    if not template_path.is_file():
        raise FileNotFoundError(f"Prompt template not found at {template_path}")
    return template_path.read_text(encoding="utf-8").strip()


def get_prompt(template_name: str = "prompt.md") -> str:
    """
    Alias for load_prompt_template. Reads and returns the prompt string from the specified template file.
    """
    return load_prompt_template(template_name)


# Exported prompt string loaded directly from templates/prompt.md
INCIDENT_RESPONSE_PROMPT = load_prompt_template("prompt.md")
