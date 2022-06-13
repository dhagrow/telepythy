import toml
import appdirs

from ..lib import logs
from ..lib import utils

log = logs.get(__name__)

DEFAULT_PATH = appdirs.user_config_dir('telepythy.cfg', False)
# when blank, sys.executable will be used
DEFAULT_INTERPRETER = 'python'

class AttrDict(dict):
    def __getattr__(self, name):
        try:
            return super().__getattr__(name)
        except AttributeError:
            try:
                val = self[name]
            except KeyError:
                raise AttributeError(name)
            if isinstance(val, dict):
                return self.__class__(val)
            return val

    def __or__(self, other):
        return AttrDict(super().__or__(other))

def init(path=None):
    path = path or DEFAULT_PATH

    log.debug('config: %s', path)

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
            'size': [820, 820],
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

    cfg = defaults | cfg

    with open(path, 'w') as f:
        toml.dump(cfg, f)

    return cfg
