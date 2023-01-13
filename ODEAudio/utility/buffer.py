class Buffer:
    """A buffered list, which drops its oldest elements as it grows"""
    def __init__(self, max_size, data=None):
        self.max_size = max_size
        self.index_offset = 0
        if data:
            self.data = data
        else:
            self.data = []

        self.append_threshold = 1.5

    def _resize(self, threshold=0.0):
        if len(self) > self.max_size * threshold:
            self.index_offset -= len(self) - self.max_size
            self.data = self.data[-self.max_size:]

    def append(self, value):
        self.data.append(value)
        self._resize(self.append_threshold)  # Don't resize after every append

    def extend(self, values):
        self.data.extend(values)
        self._resize()

    def truncate(self, index):
        index = self._adjust_index(index)
        self.data = self.data[:index]

    def __len__(self):
        return len(self.data)

    def last_index(self):
        return -self.index_offset + len(self)

    def _adjust_index(self, index):
        if isinstance(index, slice):
            start = self._adjust_index(index.start) if index.start else None
            stop = self._adjust_index(index.stop) if index.stop else None
            return slice(start, stop, index.step)

        if index >= 0:
            # Check index hasn't already been dropped
            if index + self.index_offset < 0:
                raise IndexError('Requested index dropped')
            # Return offset index for regular indices
            return index + self.index_offset
        else:
            # Return unchanged index for searches from the end of array
            return index

    def __getitem__(self, item):
        return self.data[self._adjust_index(item)]

    def __setitem__(self, key, value):
        self.data[self._adjust_index(key)] = value
