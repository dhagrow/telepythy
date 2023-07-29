import random
import mistune

_current_tip = 0
def get(index=None):
    global _current_tip
    if index is None:
        index = _current_tip % len(_tips)
        random.shuffle(_tips)
    _current_tip += 1
    return mistune.html(_tips[index])

_tips = [
'`Ctrl+[` and `Ctrl+]` fold and unfold output sections, respectively. In each case, the most recent folded/unfolded section will be toggled.',
'`Ctrl+-` and `Ctrl+=` can be used to quickly zoom in and out.',
'Even if you hide the menu bar, the menu is always available by clicking on the hamburger menu on the bottom-left of the UI.',
'The bottom-right of the UI displays your connection status to the currently selected profile. Click the button at the bottom-right to select a different profile. You can also use the "Profiles" menu.',
'You can move the source editor around if you first enable the "Source Titlebar" in the "View" menu.',
'A profile can be selected on startup using the `--profile` command-line option. You can get a list of all profiles using `--list-profiles`.',
'The Telepythy service has no dependencies and supports Python 2.7+.',
'Start a remote service using `pip install telepythy-service`, then run the `telepythy-svc` command. Use `-h` for help and `-v`, or `-vv` for verbose output.',
'Save a copy of `telepythy_service.pyz`, and copy it anywhere. It can be run directly using `python telepythy_service.pyz`.',
'`Ctrl+Return` or `Enter` (on the keypad) will always execute your code. If there is only one line, just `Return` is enough. Add a `space` to the end of the line to avoid executing.',
'Hit `F12` to popup the settings pane.',
'You can run a startup script for every new session. Just add your code to `<config-dir>/startup.py`. This is convenient for common imports and utility functions.',
]
