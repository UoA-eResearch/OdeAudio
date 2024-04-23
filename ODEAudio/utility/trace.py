from os import path, makedirs

from ODEAudio.root import ROOT_DIR


class Trace:
    """Class responsible for creating trace files, and streaming data to them"""
    def __init__(self, filename=None):
        self.filename = None
        self.file = None
        self.pars = None

        self.setup()

    def setup(self):
        self.filename = self._new_trace_filename()
        self.file = open(self.filename, 'w', buffering=1)
        self.file.write('t,cA,cB,eA,eB,d0,d1,d2,d3,d4\n')
        self.pars = [0] * 4

    def reset(self):
        self.close()

    def update_pars(self, cA, eA, cB, eB):
        self.pars = [cA, cB, eA, eB]

    @staticmethod
    def _new_trace_filename():
        i = 0
        folder = path.join(ROOT_DIR, 'traces')
        makedirs(folder, exist_ok=True)
        while path.exists(path.join(folder, f'trace_{i:>03}.csv')):
            i += 1

        return path.join(folder, f'trace_{i:>03}.csv')

    def write(self, t, Y):
        for tt, yy in zip(t, Y):
            self.file.write(f'{tt},{",".join(map(str, self.pars))},{",".join(map(str, yy))}\n')

    def close(self):
        self.file.close()
