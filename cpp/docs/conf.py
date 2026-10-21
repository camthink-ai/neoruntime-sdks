# Configuration file for the Sphinx documentation builder (C++ SDK, Chinese).
#
# Mirrors python/docs/conf.py but drops autodoc — there is no Python package
# to import here. The English API reference is Doxygen (cpp/Doxyfile), not
# Sphinx; this tree is the Chinese quick-start & module overview published
# at /cpp/zh/.

# -- Project information -----------------------------------------------------

project = 'NeoRuntime C++ SDK'
copyright = '2025-2026, CamThink'
author = 'CamThink'

# -- General configuration ---------------------------------------------------

extensions = []
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
source_suffix = '.rst'

# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_logo = None
html_favicon = None

html_theme_options = {
    'navigation_depth': 4,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'includehidden': True,
    'titles_only': False,
}

# Language
language = 'zh_CN'
