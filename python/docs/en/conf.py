# Configuration file for the Sphinx documentation builder.

import os
import sys

# Add SDK to path (en/ is one level deeper than the original docs/)
sys.path.insert(0, os.path.abspath('../..'))

# Fix proto import issue
proto_dir = os.path.abspath('../../hailo_ipc_sdk/proto')
if proto_dir not in sys.path:
    sys.path.insert(0, proto_dir)

# Mock the proto modules if they fail to import (for docs only)
try:
    import hailo_ipc_sdk.proto.inference_pb2 as _inf_pb2
    sys.modules['inference_pb2'] = _inf_pb2
except Exception:
    pass

try:
    import hailo_ipc_sdk.proto.media_pb2 as _med_pb2
    sys.modules['media_pb2'] = _med_pb2
except Exception:
    pass

try:
    import hailo_ipc_sdk.proto.device_pb2 as _dev_pb2
    sys.modules['device_pb2'] = _dev_pb2
except Exception:
    pass

try:
    import hailo_ipc_sdk.proto.event_pb2 as _evt_pb2
    sys.modules['event_pb2'] = _evt_pb2
except Exception:
    pass

try:
    import hailo_ipc_sdk.proto.app_pb2 as _app_pb2
    sys.modules['app_pb2'] = _app_pb2
except Exception:
    pass

try:
    import hailo_ipc_sdk.proto.camera_pb2 as _cam_pb2
    sys.modules['camera_pb2'] = _cam_pb2
except Exception:
    pass

# -- Project information -----------------------------------------------------

project = 'AIPC Platform Python SDK'
copyright = '2025-2026, CamThink'
author = 'CamThink'
release = '0.3.0'
version = '0.3.0'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx.ext.autosummary',
    'sphinx.ext.coverage',
    'sphinx_rtd_theme',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_logo = None
html_favicon = '_static/favicon.png'

html_theme_options = {
    'navigation_depth': 4,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'includehidden': True,
    'titles_only': False,
}

# -- Extension configuration -------------------------------------------------

napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

autodoc_typehints = 'description'
autodoc_typehints_description_target = 'documented'

autosummary_generate = True

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'grpc': ('https://grpc.github.io/grpc/python/', None),
}

# Language
language = 'en'

# -- Options for LaTeX output ------------------------------------------------

latex_engine = 'xelatex'

latex_elements = {
    'papersize': 'a4paper',
    'pointsize': '11pt',
    'figure_align': 'htbp',
    'preamble': r'''
\usepackage{xeCJK}
\setCJKmainfont{Noto Serif CJK SC}
\setCJKsansfont{Noto Sans CJK SC}
\setCJKmonofont{Noto Sans Mono CJK SC}
\usepackage{bookmark}
\hypersetup{
    colorlinks=true,
    linkcolor=blue!70!black,
    urlcolor=blue!70!black,
}
''',
}

latex_logo = None
latex_appendices = []
latex_domain_indices = True
