import toml
import appdirs
from attrdict import AttrDict

from ..lib import utils

DEFAULT_PATH = appdirs.user_config_dir('telepythy.cfg', False)
# when blank sys.executable will be used
DEFAULT_INTERPRETER = 'python'

def init(path=None):
    path = path or DEFAULT_PATH

    defaults = AttrDict({
        'profile': {
            'default': {'command': DEFAULT_INTERPRETER},
            'connect': {'connect': utils.DEFAULT_ADDR},
            'serve': {'serve': utils.DEFAULT_ADDR},
            },
        'startup': {'source': ''},
        'style': {
            'app': 'qdarkstyle',
            'highlight': 'gruvbox-dark',
            'font_family': 'fira mono',
            'font_size': 12,
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
        cfg = {}

    cfg = defaults + cfg

    with open(path, 'w') as f:
        toml.dump(cfg, f)

    return cfg
