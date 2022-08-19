import os
from setuptools import setup, find_packages

os.chdir(os.path.dirname(__file__))

import telepythy

with open('README.md') as f:
    readme = f.read()

setup(
    name='telepythy',
    version=telepythy.__version__,
    url='https://github.com/dhagrow/telepythy',
    author='Miguel Turner',
    author_email='cymrow@gmail.com',
    license='MIT',
    description='An embeddable, remote-capable Python shell',
    long_description=readme,
    long_description_content_type='text/markdown',
    packages=find_packages() + ['telepythy.gui'],
    package_data={'telepythy': ['telepythy_service.pyz']},
    entry_points={
        'gui_scripts': [
            'telepythy-gui=telepythy.gui.__main__:run',
            ],
        'console_scripts': [
            'telepythy-svc=telepythy.lib.__main__:run',
            ]
        },
    install_requires=[
        'appdirs>=1.4.4',
        'colorlog>=6.6.0',
        'Pygments>=2.12.0',
        'pyqtdarktheme>=1.1.0',
        'PySide6-Essentials>=6.3.0',
        'QtPy>=2.1.0',
        'shiboken6>=6.3.0',
        'snekcfg>=0.1.0',
        ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Interpreters',
        'Topic :: Utilities',
        ],
    )
