import os
import importlib
import collections

import qdarktheme
from pygments import styles
from pygments.lexer import Text

def get_theme_stylesheet(theme='dark'):
    return qdarktheme.load_stylesheet(theme)

def get_style(name, search_paths=None):
    paths = search_paths or []
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
        style.background_color = '#FFFFFF'
    elif not style.text_color:
        style.text_color = _color_from_brightness(style.background_color)
    elif not style.background_color:
        style.background_color = _color_from_brightness(style.text_color)

    if not style.highlight_color:
        style.highlight_color = _complementary_color(style.background_color)
    style.highlight_text_color = _color_from_brightness(style.highlight_color)

    style.text_color = _ensure_hash(style.text_color)
    style.background_color = _ensure_hash(style.background_color)
    style.highlight_text_color = _ensure_hash(style.highlight_text_color)
    style.highlight_color = _ensure_hash(style.highlight_color)

    return style

def get_styles(search_paths=None):
    paths = search_paths or []
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
    rgb = _hex2rgb(hexstr)
    comp = ['%02x' % (255 - c) for c in rgb]
    return ''.join(comp)

def _color_from_brightness(hexstr):
    return '#FFFFFF' if _color_brightness(hexstr) < 186 else '#000000'

def _color_brightness(hexstr):
    rgb = _hex2rgb(hexstr)
    return (0.212 * rgb.r) + (0.701 * rgb.g) + (0.087 * rgb.b)

RGB = collections.namedtuple('RGB', 'r g b')
def _hex2rgb(hexstr):
    hexstr = hexstr.lstrip('#')
    return RGB(*(int(c, 16) for c in (hexstr[0:2], hexstr[2:4], hexstr[4:6])))

def _ensure_hash(s):
    if s and not s.startswith('#'):
        s = '#' + s
    return s
