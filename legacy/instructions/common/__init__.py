"""Historical contracts; legacy child modules keep their original owners."""
from anclicker.instructions import common as _implementation

__all__ = _implementation.__all__


def __getattr__(name):
    if name in __all__ or name == 'actions':
        return getattr(_implementation, name)
    # Runtime and UI helpers can share a basename. Unknown children must be
    # imported from this package's legacy path rather than its runtime peer.
    raise AttributeError(name)
