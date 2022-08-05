from ..lib import utils

from . import control
from .utils import virtualenvs

class Profiles:
    def __init__(self, profiles, verbose=0):
        self._profiles = dict(self._parse_profiles(profiles))
        self._verbose = verbose

    @property
    def _venvs(self):
        return {name: {'command': path} for name, path in virtualenvs()}

    def get_config_profiles(self):
        yield from self._profiles.keys()

    def get_virtualenv_profiles(self):
        yield from self._venvs.keys()

    def get_profile(self, name):
        try:
            sec = self._profiles[name]
        except KeyError:
            sec = self._venvs[name]
        return next(iter(sec.items()))

    def get_control(self, profile_name):
        type, value = self.get_profile(profile_name)

        if type == 'command':
            cmd = value or utils.DEFAULT_COMMAND
            return control.ProcessControl(('localhost', 0), cmd, self._verbose)

        elif type == 'connect':
            addr = utils.parse_address(value or utils.DEFAULT_ADDR)
            return control.ClientControl(addr)

        elif type == 'serve':
            addr = utils.parse_address(value or utils.DEFAULT_ADDR)
            return control.ServerControl(addr)

        assert False, 'invalid control init'

    def _parse_profiles(self, profiles):
        for profile, value in profiles.items():
            name, type = profile.split('.')
            yield (name, {type: value})
