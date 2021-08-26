import os
from setuptools import setup, find_packages

readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
with open(readme_path) as f:
    readme = f.read()

setup(
    name='telepythy',
    version='0.1.0',
    url='https://github.com/dhagrow/telepythy',
    author='Miguel Turner',
    author_email='cymrow@gmail.com',
    long_description=readme,
    long_description_content_type='text/markdown',
    packages=find_packages(exclude=['test']),
    entry_points={
        'console_scripts': [
            'telepythy=telepythy.gui.__main__:main'
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
