# Configuration file for the Sphinx documentation builder.

# -- Project information

project = 'ReflectX'
copyright = 'Logan Pearce, 2023'
author = 'Logan Pearce'

release = '0.1'
version = '0.1.0'

# -- General configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

templates_path = ['_templates']

# -- Options for HTML output

extensions = ["sphinx_rtd_theme"]
html_theme = "sphinx_rtd_theme"
#html_theme = "classic"
html_logo = 'images/reflectX-transp.png'

# -- Options for EPUB output
epub_show_urls = 'footnote'
