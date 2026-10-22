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
pygments_style = 'a11y_pygments.github_light.style.Theme'
pygments_dark_style = 'a11y_pygments.github_dark.style.Theme'
c_id_attributes = ['ABI', 'lib']

html_static_path = ['_static']
html_extra_path = ['_extra']

# The icons are files so the sidebar links in custom.css can draw them too.
def icon(name):
    path = os.path.join(os.path.dirname(__file__), '_static', 'icons', name + '.svg')
    with open(path) as file:
        return file.read().strip()

from pygments.lexers import CMakeLexer
from pygments.token import String


# The stock lexer reads RAM(<x>) inside a call as a string that ends the call
# at the inner ")", which breaks the highlighting of rp6502_asset() lines.
class RP6502CMakeLexer(CMakeLexer):
    tokens = {
        'args': [
            (r'[^()$"# \t\n]+', String) if rule[0] == r'[^)$"# \t\n]+' else rule
            for rule in CMakeLexer.tokens['args']
        ],
    }


def setup(app):
    app.add_lexer('cmake', RP6502CMakeLexer)


html_css_files = ['custom.css']
html_js_files = ['custom.js']
html_theme_options = {
    # 'announcement': '',
    'source_repository': 'https://github.com/picocomputer/picocomputer.github.io/',
    'source_branch': 'main',
    'source_directory': 'docs/source/',
    'footer_icons': [
        {
            'name': 'GitHub',
            'url': 'https://github.com/picocomputer?view_as=public',
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
    # The GitHub styles have the page's own background, so code keeps the
    # backgrounds of furo's default styles, a11y-light and native. C
    # signatures take the colors that the GitHub styles give a declaration.
    'light_css_variables': {
        'color-code-background': '#f2f2f2',
        'color-api-name': '#0550ae',
        'color-api-pre-name': '#0550ae',
        'color-api-keyword': '#cf222e',
        'color-api-overall': '#24292f',
    },
    'dark_css_variables': {
        'color-code-background': '#202020',
        'color-api-name': '#79c0ff',
        'color-api-pre-name': '#79c0ff',
        'color-api-keyword': '#ff7b72',
        'color-api-overall': '#c9d1d9',
    },
}

# -- Options for Open Graph link previews ------------------------------------
# https://sphinxext-opengraph.readthedocs.io/

ogp_site_url = 'https://picocomputer.github.io/'
ogp_image = 'https://picocomputer.github.io/_static/logo.png'
