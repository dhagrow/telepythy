import os
import importlib

import qdarktheme
from pygments import styles
from pygments.lexer import Text

BASE_PATH = os.path.dirname(__file__)

def get_app_stylesheet(theme='dark'):
    return qdarktheme.load_stylesheet(theme)

def get_style(name, search_paths=None):
    paths = (search_paths or []) + [BASE_PATH]
    for path in paths:
        try:
            style = _get_local_style(name, path)
            break
        except styles.ClassNotFound:
            pass
    else:
        style = styles.get_style_by_name(name)

    # hack in some useful attrs
    style.text_color = style.styles[Text]
    if not any((style.text_color, style.background_color)):
        style.text_color = '#000000'
        style.background_color = '#ffffff'
    elif not style.text_color:
        style.text_color = _complementary_color(style.background_color)
    elif not style.background_color:
        style.background_color = _complementary_color(style.text_color)

    if not style.highlight_color:
        style.highlight_color = '#49a0ae'
    style.highlight_text_color = _complementary_color(style.highlight_color)

    style.text_color = style.styles[Text] = _ensure_hash(style.text_color)
    style.background_color = _ensure_hash(style.background_color)
    style.highlight_text_color = _ensure_hash(style.highlight_text_color)
    style.highlight_color = _ensure_hash(style.highlight_color)

    return style

def get_styles(search_paths=None):
    paths = (search_paths or []) + [BASE_PATH]
    names = set()
    for path in paths:
        names.update(_get_local_styles(path))
    names.update(styles.get_all_styles())
    for name in names:
        yield name

def _get_local_style(name, path):
    try:
        mod = _import_path(name, path)
    except OSError:
        raise styles.ClassNotFound("Could not find style module %r." % name)

    cls_name = name.title() + 'Style'
    try:
        return getattr(mod, cls_name)
    except AttributeError:
        raise styles.ClassNotFound(
            "Could not find style class %r in style module." % cls_name)

def _get_local_styles(path):
    for name in os.listdir(path):
        if name.startswith('_'):
            continue
        yield os.path.splitext(name)[0]

def _import_path(name, path):
    path = os.path.join(path, name + '.py')
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# tweaked from: https://stackoverflow.com/a/38478744
def _complementary_color(hexstr):
    hexstr = hexstr.lstrip('#')
    rgb = (hexstr[0:2], hexstr[2:4], hexstr[4:6])
    comp = ['%02x' % (255 - int(a, 16)) for a in rgb]
    return ''.join(comp)

def _ensure_hash(s):
    if s and not s.startswith('#'):
        s = '#' + s
    return s
