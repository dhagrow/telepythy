import toml
import appdirs
from attrdict import AttrDict

DEFAULT_PATH = appdirs.user_config_dir('telepythy.cfg')
DEFAULT_INTERPRETER = 'python'

def init(path=None):
    path = path or DEFAULT_PATH

    defaults = AttrDict({
        'profile': {'default': {'command': DEFAULT_INTERPRETER}},
        'startup': {'source': ''},
        'style': {
            'output': 'gruvbox-dark',
            'source': 'gruvbox-dark',
            },
        'window': {
            'size': [800, 800],
            'view': {
                'menu': True,
                },
            },
        })

    try:
        with open(path) as f:
            cfg = toml.load(f)
    except FileNotFoundError:
        with open(path, 'w') as f:
            toml.dump(defaults, f)
        cfg = {}

    return defaults + cfg
