import pprint


class Borg(object):
    """Singletons are a way of ensuring we have shared state data for all objects
       This is another pattern of ensuring that - which not allows a 'singleton'
       typ approach, but also allows us multiple inheritance without having to boiler plate
       the same code over and over.
    """
    _shared_state = {}

    def __init__(self):
        self.__dict__ = self._shared_state

    def __str__(self):
        return pprint.pformat(self._shared_state)
