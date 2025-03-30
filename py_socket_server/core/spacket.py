class SPacket:
    def __init__(self):
        self._data = bytearray()

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        if isinstance(value, (bytes, bytearray)):
            self._data = value
        else:
            raise TypeError('The value must be of the bytes or bytearray type.')