import os
import sys
from setuptools import setup, find_packages

os.chdir(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, '.')

import telepythy

with open('README.md') as f:
    readme = f.read()

setup(
    name='telepythy',
    version=telepythy.__version__,
    url='https://github.com/dhagrow/telepythy',
    author='Miguel Turner',
    author_email='cymrow@gmail.com',
    long_description=readme,
    long_description_content_type='text/markdown',
    packages=find_packages() + ['telepythy.gui'],
    entry_points={
        'gui_scripts': [
            'telepythy=telepythy.gui.__main__:main',
            ],
        'console_scripts': [
            'telepythy-service=telepythy.lib.__main__:main',
            ]
        },
    install_requires=[
        'appdirs>=1.4.4',
        'attrdict>=2.0.1',
        'colorlog>=6.6.0',
        'Pygments>=2.12.0',
        'PySide6-Essentials>=6.3.0',
        'QDarkStyle>=3.0.3',
        'QtPy>=2.1.0',
        'qtsass>=0.3.0',
        'shiboken6>=6.3.0',
        'toml>=0.10.2',
        ],
    )
