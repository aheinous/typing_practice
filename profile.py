import json

from dbg_log import dbg
from text_gen import ALL_CHARS


class Profile:
    def __init__(self, fname=None):
        if fname:
            self.load(fname)
        else:
            self._init_data()


    def init_char(self, char):
        if char not in self._data['times_seen']:
            self._data['times_seen'][char] = 0
            self._data['times_correct'][char] = 0

    def _init_data(self):
        self._data = {
                'times_seen' : {},
                'times_correct' : {}
            }
        for char in ALL_CHARS:
            self._data['times_seen'][char] = 0
            self._data['times_correct'][char] = 0


    def report_miss(self, char):
        # dbg('report_miss ' +char)
        char = char.lower()
        self.init_char(char)

        self._data['times_seen'][char] += 1


    def report_hit(self, char):
        # dbg('report_hit ' +char)
        char = char.lower()
        self._data['times_seen'][char] += 1
        self._data['times_correct'][char] += 1


    def load(self, fname):
        with open(fname, 'r') as f:
            print(f'loading {fname}')
            self._data = json.load(f)

    def store(self, fname):
        with open(fname, 'w') as f:
            print(f'saving {fname}')
            json.dump(self._data, f, indent=4, sort_keys=True)

    def percentages(self):
        def iter():
            for char, correct in self._data['times_correct'].items():
                seen = self._data['times_seen'][char]
                if seen:
                    yield (correct / seen, char)

        return sorted(iter())


    def percentage(self, char):
        if not self.times_seen(char):
            return None
        return self.times_seen(char) / self.times_correct(char)





    def all_times_seen(self):
        return sorted( [(n,c) for c, n in self._data['times_seen'].items()] )

    def times_seen(self,char):
        return self._data['times_seen'][char.lower()]

    def times_correct(self,char):
        return self._data['times_correct'][char.lower()]



def main():
    profile = {
        'times_seen' : {'a':100, 'b':12},
        'times_correct' : {'a':80, 'b':6}
    }

    with open('profile.json', 'w') as f:
        json.dump(profile, f, indent=4, sort_keys=True)

if __name__ == '__main__':
    main()