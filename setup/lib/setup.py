import os
from setuptools import setup

readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
with open(readme_path) as f:
    readme = f.read()

setup(
    name='telepythy-service',
    version='0.2.0',
    url='https://github.com/dhagrow/telepythy',
    author='Miguel Turner',
    author_email='cymrow@gmail.com',
    long_description=readme,
    long_description_content_type='text/markdown',
    packages=['telepythy', 'telepythy.lib'],
    entry_points={
        'console_scripts': [
            'telepythy-service=telepythy.lib.__main__:main'
            ]
        },
    )
