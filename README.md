# Telepythy

Telepythy is a desktop Python shell inspired by [DreamPie][1] with some notable additional features. It is designed to streamline a prototyping workflow.

## Features

* Divided editor for code
* Modern UI based on Qt 6
* Syntax highlighting (based on Pygments)
* Embeddable service with no third-party dependencies
* Connections to remote Python interpreters (as client or server)
* Swap between multiple interpreter profiles (local or remote)
* UI requires Python 3 on Linux/Windows/OSX (tested: 3.6/3.9 on Linux/Windows)
* Embeddable service supports Python 2 and 3 on all platforms (tested: 2.7/3.6/3.9 on Linux/Windows)

## Motivation

As a long-time user of [DreamPie][1], I have grown comfortable with the workflow that it offers. However, I have often wished for additional features. Unfortunately, it looks as if all development [stopped][2] sometime before 2016, and the last official release was in 2012. I looked into creating a fork to add the features I was interested in, but the effort to modernize (i.e. Python 3) an unfamiliar and complex code-base was too daunting for me.

Of course, [Jupyter][3] exists and is very powerful. But I have always found the workflow awkward. I don't really want a shareable code notebook. I want a prototyping and debugging tool.

So, I decided to start from scratch, and **Telepythy** is the result.

## Installation

At the moment there is no installer available for **Telepythy**. The easiest option is to use `pip`:

```shell
$ pip install telepythy
```

NOTE: This will pull in [PySide2][4], which weighs in at >100mb. I expect the eventual installer to be <20mb.

## Documentation

*work in progress*

## Roadmap

**Telepythy** is very much a work in progress. Here are some features that are planned for future releases (in no particular order):

* Minimal PyPI package for the embeddable service (no dependencies)
* Configuration UI
* Profile configuration UI
* Style/syntax highlighting configuration UI
* Smart copy/paste
* UNIX domain sockets
* Folding for code and output blocks
* Code snippets
* Session import/export
* Embedded documentation
* Platform installers
* Upgrade to PySide6 (QML? snake_case!)
* Localization
* Website/logo

If you have additional feature suggestions, please don't hesistate to create an [issue][5]. Note that I work on this project in my free time and I don't expect to work on features that I don't personally find useful. I do, however, welcome pull requests.

[1]: http://www.dreampie.org/
[2]: https://github.com/noamraph/dreampie/issues/65
[3]: https://jupyter.org/
[4]: https://wiki.qt.io/Qt_for_Python
[5]: https://github.com/dhagrow/telepythy/issues/new
