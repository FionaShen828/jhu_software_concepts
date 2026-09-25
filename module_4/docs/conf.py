import sys
from pathlib import Path


# Add the project's src directory so Sphinx can import
# the application modules for autodoc.
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))


project = "GradCafe Analysis"
copyright = "2026, Fiona Shen"
author = "Fiona Shen"


extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]


templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


html_theme = "alabaster"

html_static_path = ["_static"]