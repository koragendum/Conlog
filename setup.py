# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['conlog']

package_data = \
{'': ['*']}

install_requires = \
['networkx<3', 'numpy<2']

entry_points = \
{'console_scripts': ['conlog = conlog:__main__']}

setup_kwargs = {
    'name': 'conlog',
    'version': '0.0.0a0',
    'description': 'Conlog: SMT (Satisfying Maze Traversal) Solver',
    'long_description': None,
    'author': None,
    'author_email': None,
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.10,<3.11',
}
from build import *
build(setup_kwargs)

setup(**setup_kwargs)
