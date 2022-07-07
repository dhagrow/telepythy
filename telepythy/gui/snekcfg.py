import typing
import collections
import configparser

# rename the original so we can use the name
_type = type

ConfigItem = collections.namedtuple('ConfigItem', 'default, type')
ConfigType = collections.namedtuple('ConfigType', 'encode, decode')

class Config:
    def __init__(self, path):
        self._path = path
        self._parser = configparser.ConfigParser(interpolation=None)
        self._items = {}
        self._types = {}

        self._register_default_types()

    def init(self, key, default, type=None):
        self._items[key] = ConfigItem(default, type or _type(default))

        section_name, value_name = self._split_key(key)
        sct = self.section(section_name, create=True)

        sct[value_name] = default

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __getitem__(self, key):
        section_name, value_name = self._split_key(key)
        value = self._parser[section_name][value_name]
        typename = self._items[key].type
        return self.decode(value, typename)

    def __setitem__(self, key, value):
        section_name, value_name = self._split_key(key)
        typename = self._items[key].type
        enc_value = self.encode(value, typename)
        self._parser[section_name][value_name] = enc_value

    def options(self, section):
        return self._parser.options(section)

    def items(self, section):
        sct = self.section(section)
        return [(name, sct.get(name)) for name in sct.options()]

    def section(self, section, create=False):
        if create:
            try:
                self._parser.add_section(section)
            except configparser.DuplicateSectionError:
                pass
        return ConfigSection(section, self)

    def sections(self):
        return self._parser.sections()

    def __iter__(self):
        yield from self.sections()

    def todict(self):
        return {section: dict(self.section(section).items())
            for section in self.sections()}

    ## persistence ##

    def read(self):
        self._parser.read(self._path)

    def write(self):
        with open(self._path, 'w') as f:
            self._parser.write(f)

    def sync(self):
        self.read()
        self.write()

    ## encoding ##

    def encode(self, value, typename):
        typename = self._typename(typename)
        try:
            encode = self._types[typename].encode
        except KeyError:
            raise UnknownType(typename)
        return encode(value)

    def decode(self, value, typename):
        typename = self._typename(typename)
        try:
            decode = self._types[self._typename(typename)].decode
        except KeyError:
            raise UnknownType(typename)
        return decode(value)

    ## types ##

    def register_type(self, name, encode, decode):
        name = self._typename(name)
        self._types[name] = ConfigType(
            encode or (lambda v: v),
            decode or (lambda v: v),
            )

    def unregister_type(self, name):
        name = self._typename(name)
        del self._types[name]

    def unregister_all_types(self):
        self._types.clear()

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.todict())

    ## internal ##

    def _register_default_types(self):
        self.register_type(str, None, None)
        self.register_type(int, str, int)
        self.register_type(float, str, float)

        _boolean_states = {'1': True, 'yes': True, 'true': True, 'on': True,
            '0': False, 'no': False, 'false': False, 'off': False}
        self.register_type(bool,
            lambda x: 'true' if x else 'false',
            lambda x: _boolean_states[x.lower()])

        # it would technically be more correct to use typing.Tuple[str, ...]
        # to register the generic case of an unbounded tuple, but for general
        # use it's simpler to let the user decide if they want to be that strict
        self.register_type(typing.Tuple[str],
            lambda v: ','.join(v),
            lambda v: tuple(x.strip() for x in v.split(',')))
        self.register_type(typing.Tuple[int],
            lambda v: ','.join(str(x) for x in v),
            lambda v: tuple(int(x.strip()) for x in v.split(',')))

    def _split_key(self, key):
        return key.split('.', 1)

    def _typename(self, name):
        if isinstance(name, str):
            pass
        elif isinstance(name, typing.Type):
            name = name.__name__
        else:
            name = str(name)
        return name

class ConfigSection:
    def __init__(self, name, config):
        self._name = name
        self._config = config

    def init(self, name, default, type=None):
        self._config.init(self._key(name), default, type)

    def get(self, name, default=None):
        return self._config.get(self._key(name), default)

    def __getitem__(self, name):
        return self._config[self._key(name)]

    def __setitem__(self, name, value):
        self._config[self._key(name)] = value

    def options(self):
        return self._config.options(self._name)

    def items(self):
        return self._config.items(self._name)

    def __iter__(self):
        yield from self.options()

    ## internal ##

    def _key(self, *names):
        return '.'.join((self._name,) + names)

class ConfigError(Exception):
    pass

class UnknownType(ConfigError):
    pass
