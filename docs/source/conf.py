# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Picocomputer'
copyright = '2026 Rumbledethumps'
author = 'Rumbledethumps'
release = ''

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []
templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
html_css_files = ['custom.css']
html_sidebars = {'**': ['about.html', 'navigation.html', 'relations.html', 'donate.html']}
html_theme_options = {
    'donate_url': 'https://ko-fi.com/rumbledethumps',
    'font_family': 'Arial, sans-serif',
    'github_banner': True,
    'github_user': 'picocomputer',
    'github_repo': '',
    'fixed_sidebar': True,
    'show_relbars': True,
    'sidebar_width': '230px', # undo alabaster's override
}
