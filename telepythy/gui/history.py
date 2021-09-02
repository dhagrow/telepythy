class History:
    def __init__(self):
        self._history = []
        self._index = 0
        self._match = None

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value):
        self._index = min(max(0, value), len(self._history))

    def append(self, value):
        hist = self._history
        value = value.strip()
        if value and value != (hist and hist[-1]):
            hist.append(value)
        self.reset()

    def first(self):
        self.index = 0
        return self._history[0]

    def last(self):
        self.index = len(self._history) - 1
        return self._history[-1]

    def previous(self, match=None):
        self.index -= 1
        i, value = self._search(match, range(self.index, -1, -1))
        self.index = i
        return value

    def next(self, match=None):
        self.index += 1
        i, value = self._search(match, range(self.index, len(self._history)))
        self.index = i
        return value

    def _search(self, match, it):
        if self._match is None:
            self._match = match
        match = self._match

        for i in it:
            value = self._history[i]
            if not match or value.startswith(match):
                return i, value

        return (self.index, None)

    def reset(self):
        self.index = len(self._history)
        self._match = None

    def __bool__(self):
        return bool(self._history)
