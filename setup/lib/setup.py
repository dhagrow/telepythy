import os
from setuptools import setup, find_packages

os.chdir(os.path.dirname(__file__))

import telepythy

with open('README.md') as f:
    readme = f.read()

setup(
    name='telepythy-service',
    version=telepythy.__version__,
    url='https://github.com/dhagrow/telepythy',
    author='Miguel Turner',
    author_email='cymrow@gmail.com',
    long_description=readme,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'telepythy-service=telepythy.lib.__main__:main'
            ]
        },
    )
