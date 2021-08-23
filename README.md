# Telepythy

Telepythy is a Python shell inspired by [DreamPie][1] with some notable additional features.

## Features

* Split output/source editor UI
* Modern UI based on Qt 6
* Syntax highlighting (based on Pygments)
* Embeddable agent with no third-party dependencies
* Connections to remote Python interpreters (as client or server)
* Swap between multiple interpreter profiles (local or remote)
* UI requires Python 3 on Linux/Windows/OSX (tested: 3.6/3.9 on Linux/Windows)
* Agent supports Python 2 and 3 on all platforms (tested: 2.7/3.6/3.9 on Linux/Windows)

## Motivation

As a long-time user of [DreamPie][1], I have grown comfortable with the workflow that it offers, but have often wished for additional features. Unfortunately, it looks as if all development [stopped][2] sometime before 2016. I looked into creating a fork to add the features I was interested in, but the effort to modernize (aka Python 3) an unfamiliar and complex code-base was too daunting for me.

Of course, [Jupyter][3] exists and is very powerful. But I have always found the workflow awkward. I don't really want a shareable code notebook. I want a prototyping and debugging tool.

So, I decided to start from scratch, and **Telepythy** is the result.

## Roadmap

**Telepythy** is very much a work in progress. Here are some features that are planned for future releases:

* Configuration UI
* Profile configuration UI
* Style/syntax highlighting configuration UI
* UNIX domain sockets
* Folding for code and output blocks
* Code snippets
* Embedded documentation
* Platform installers

[1]: http://www.dreampie.org/
[2]: https://github.com/noamraph/dreampie/issues/65
[3]: https://jupyter.org/
