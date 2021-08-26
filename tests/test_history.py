import pytest

from telepythy.gui import history

@pytest.fixture
def hist():
    h = history.History()
    h.append('alpha')
    h.append('beta')
    h.append('eta')
    h.append('gamma')
    h.append('delta')
    h.append('epsilon')
    return h

def test_previous(hist):
    assert hist.previous() == 'epsilon'
    assert hist.previous() == 'delta'
    assert hist.previous() == 'gamma'
    assert hist.next() == 'delta'
    assert hist.previous() == 'gamma'
    assert hist.previous() == 'eta'
    assert hist.previous() == 'beta'
    assert hist.previous() == 'alpha'

def test_next(hist):
    assert hist.next() is None
    assert hist.previous() == 'epsilon'
    assert hist.previous() == 'delta'
    assert hist.next() == 'epsilon'
    assert hist.next() is None
    assert hist.previous() == 'epsilon'

def test_first(hist):
    assert hist.first() == 'alpha'

    assert hist.next() == 'beta'
    assert hist.previous() == 'alpha'
    assert hist.next() == 'beta'
    assert hist.next() == 'eta'

    assert hist.first() == 'alpha'

def test_last(hist):
    assert hist.last() == 'epsilon'

    assert hist.previous() == 'delta'
    assert hist.next() == 'epsilon'
    assert hist.previous() == 'delta'
    assert hist.previous() == 'gamma'

    assert hist.last() == 'epsilon'

def test_previous_search(hist):
    assert hist.previous('e') == 'epsilon'
    assert hist.previous('e') == 'eta'
    assert hist.previous('e') is None
    assert hist.previous() is None

def test_next_search(hist):
    assert hist.first() == 'alpha'
    assert hist.next('e') == 'eta'
    assert hist.next('e') == 'epsilon'
    assert hist.next('e') is None
    assert hist.next() is None

def test_no_duplicates(hist):
    hist.append('epsilon')
    hist.append('epsilon')
    hist.append('zeta')
    assert hist.previous() == 'zeta'
    assert hist.previous() == 'epsilon'
    assert hist.previous() == 'delta'
