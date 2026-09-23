# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Picocomputer'
copyright = '2026 Rumbledethumps'
author = 'Rumbledethumps'
release = ''

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx_copybutton',
    'sphinx_inline_tabs',
    'sphinxext.opengraph',
]
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_title = 'Picocomputer 6502'
html_logo = '_static/logo.png'
html_favicon = '_static/favicon.ico'
c_id_attributes = ['ABI', 'lib']

html_static_path = ['_static']

# The icons are files so the sidebar links in custom.css can draw them too.
def icon(name):
    path = os.path.join(os.path.dirname(__file__), '_static', 'icons', name + '.svg')
    with open(path) as file:
        return file.read().strip()

html_css_files = ['custom.css']
html_theme_options = {
    # 'announcement': '',
    'source_repository': 'https://github.com/picocomputer/picocomputer.github.io/',
    'source_branch': 'main',
    'source_directory': 'docs/source/',
    'footer_icons': [
        {
            'name': 'GitHub',
            'url': 'https://github.com/picocomputer',
            'html': icon('github'),
            'class': '',
        },
        {
            'name': 'Discord',
            'url': 'https://discord.gg/TC6X8kTr6d',
            'html': icon('discord'),
            'class': '',
        },
        {
            'name': 'YouTube',
            'url': 'https://www.youtube.com/@rumbledethumps',
            'html': icon('youtube'),
            'class': '',
        },
    ],
}

# -- Options for Open Graph link previews ------------------------------------
# https://sphinxext-opengraph.readthedocs.io/

ogp_site_url = 'https://picocomputer.github.io/'
ogp_image = 'https://picocomputer.github.io/_static/logo.png'
