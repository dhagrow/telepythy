import os
import importlib
from pygments import styles

BASE_PATH = os.path.dirname(__file__)

def get_style(name, search_paths=None):
    paths = (search_paths or []) + [BASE_PATH]
    for path in paths:
        try:
            return _get_local_style(name, path)
        except styles.ClassNotFound:
            pass
    return styles.get_style_by_name(name)

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
