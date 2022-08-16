@echo off

@echo from telepythy.gui.__main__ import main; main() > telepythy.py

python -OO -m nuitka^
 --plugin-enable=pyside6^
 --include-module=pygments.lexers.python^
 --include-module=pygments.styles^
 --include-package-data=telepythy^
 --disable-console^
 --windows-icon-from-ico=res/snake.ico^
 --standalone^
 --output-dir=build/^
 .\telepythy.py

del telepythy.py
