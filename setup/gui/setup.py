import os
import sys
from setuptools import setup

# chdir to root of repo
os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))
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
    packages=['telepythy', 'telepythy.lib', 'telepythy.gui'],
    entry_points={
        'gui_scripts': [
            'telepythy=telepythy.gui.__main__:main',
            ],
        'console_scripts': [
            'telepythy-service=telepythy.lib.__main__:main',
            ]
        },
    install_requires=[
        'appdirs',
        'attrdict',
        'Pygments',
        'PySide2',
        'QDarkStyle',
        'QtPy',
        'shiboken2',
        'six',
        'toml',
        ],
    )
