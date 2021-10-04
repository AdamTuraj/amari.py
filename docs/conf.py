import os
import sys
import amari

sys.path.insert(0, os.path.abspath(".."))

project = "Amari.py"
copyright = "2021, TheF1ng3r"
author = "TheF1ng3r"

release = amari.__version__

extensions = [
    "recommonmark",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
