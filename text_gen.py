import re
from collections import Counter
import glob
import string
import itertools
import random

from dbg_log import dbg


# fname = '/home/alex/Projects/qmk_firmware/drivers/eeprom/eeprom_spi.c'
# search_paths = [
#     '/home/alex/Projects/qmk_firmware/**/*.h',
#     '/home/alex/Projects/qmk_firmware/**/*.cpp',
# ]



# include = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ,.?:;!'
# force = '&por#!/?;:*'

# force = ''.join(set(force.lower() + force.upper()))
# include += force
# include = ''.join(set(include.lower() + include.upper()))

# min_len = 2




def get_files_from_search_paths(search_paths):
    for path in search_paths:
        for fname in glob.iglob(path, recursive=True):
            yield fname

def read_lns_from_files(fnames):
    for fname in fnames:
        with open(fname) as f:
            for ln in f.readlines():
                yield ln

def tokenize_lns(lns):
    for ln in lns:
        for t in ln.split():
            yield t

class TextGen:
    def __init__(self,
            search_paths,
            include_chars,
            force_chars,
            min_len):
        self.search_paths = search_paths
        include_chars += force_chars
        self.include_chars = include_chars = ''.join(set(include_chars.lower() + include_chars.upper()))
        self.force_chars = ''.join(set(force_chars.lower() + force_chars.upper()))
        self.min_len = min_len

        self.include_engine = re.compile('^[' + self.include_chars + ']+$',)
        self.force_engine = re.compile(f'[{force_chars}]')

        self.token_set = set(self.filtered(
                tokenize_lns(
                    read_lns_from_files(
                        get_files_from_search_paths(search_paths)))))

        self.subset = set()

    def filtered(self, it):
        for tok in it:
            if (len(tok) >= self.min_len
                    and self.include_engine.match(tok)
                    and not (len(set(tok)) <= 2 and len(tok) >= 3)
                    ):
                yield tok


    def find_good_subset(self):
        tokens = list(self.token_set)
        random.shuffle(tokens)

        tgt_len = 50


        tgts = list(set(self.force_chars.lower()))
        print(tgts)
        tgt_idx = dict(zip(tgts, range(len(tgts))))
        print(tgt_idx)
        char_scores = [0] * len(tgts)

        highest_c = ''
        lowest_c = ''

        def update_lowest_and_highest():
            nonlocal lowest_c
            nonlocal highest_c
            lowest_cnt = float('inf')
            highest_cnt = 0
            for i, (char, cnt) in enumerate(zip(tgts, char_scores)):
                if cnt < lowest_cnt:
                    lowest_cnt = cnt
                    lowest_c = char
                if cnt > highest_cnt:
                    highest_cnt = cnt
                    highest_c = char


        update_lowest_and_highest()


        def add_tok(tok):
            for c in tok:
                idx = tgt_idx.get(c, None)
                if idx is not None:
                    char_scores[idx] += 1
            good_toks.add(tok)
            update_lowest_and_highest()

        good_toks = set()

        iter_count = 0

        def loop(predicate, target_len):
            nonlocal lowest_c
            nonlocal iter_count
            nonlocal highest_c
            nonlocal tokens
            dbg(f'starting loop: tgt len {target_len}')

            did_something = True
            while len(good_toks) < target_len and did_something:
                did_something = False
                for tok in tokens:
                    if not len(good_toks) < target_len-1:
                        break
                    # if lowest_c in tok :
                    if predicate(tok) and tok not in good_toks:
                        add_tok(tok)
                        did_something = True
            dbg(f'itercount: {iter_count}, good_toks: {len(good_toks)}')
            dbg(f'tgt: {tgts}, char_scores: {char_scores}')

        loop(lambda tok: lowest_c in tok,
            3,
            )
        loop(lambda tok: lowest_c in tok and not highest_c in tok,
            tgt_len,
            )
        loop(lambda tok: lowest_c in tok,
            tgt_len,
            )
        loop(lambda tok: highest_c not in tok and self.force_engine.match(tok),
            min(tgt_len, len(good_toks)*2),
            )

        self.subset = list(good_toks)


    def random_string_from_current_subset(self, tgt_len):
        assert self.subset
        s = ''
        while len(s) < tgt_len:
            s += random.choice(list(self.subset))
            s += ' '
        return s[:-1]





def test_version():
    search_paths = [
        '/home/alex/Projects/qmk_firmware/**/*.h',
        '/home/alex/Projects/qmk_firmware/**/*.cpp',
    ]
    include_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ,.?:;!'
    force_chars = '&por#!/?;:*'
    min_len = 1
    return TextGen(search_paths, include_chars, force_chars, min_len)




def main():

    tg = test_version()
    tg.find_good_subset()

    s = tg.random_string_from_current_subset(400)

    print(s)





# def main():
#     # readfiles()
#     token_bag = count_tokens(filtered(read_tokens(read_file_lines())))
#     # for token, count in token_bag.items():
#     #     print(token, count)

#     scored = list(give_score(token_bag.items()))
#     scored = sorted(scored, reverse=True)

#     words = list(find_good_aubset(scored))


#     while True:
#         s = ''
#         while len(s) < 300:
#             s += random.choice(words)
#             s += ' '
#         interactive.main_basic(s, False, None, False, None)



if __name__ == '__main__':
    main()
