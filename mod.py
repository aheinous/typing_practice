import re
from collections import Counter
import glob
import interactive
import string
import itertools
import random

fname = '/home/alex/Projects/qmk_firmware/drivers/eeprom/eeprom_spi.c'
search_paths = [
    '/home/alex/Projects/qmk_firmware/**/*.h',
    '/home/alex/Projects/qmk_firmware/**/*.cpp',
]



include = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ,.?:;!'
force = '&por#!/?;:*'

force = ''.join(set(force.lower() + force.upper()))
include += force
include = ''.join(set(include.lower() + include.upper()))

min_len = 2


def filelist():
    for path in search_paths:
        for fname in glob.iglob(path, recursive=True):
            yield fname

def read_file_lines():
    for fname in filelist():
        with open(fname) as f:
            for ln in f.readlines():
                yield ln

test = ['a b c d dog cat cat ! =- + +' 'x x x x x ']

def read_tokens(lns):
    for ln in lns:
    # for ln in test:
        for t in ln.split():
            yield t


def count_tokens(it):
    bag = Counter()
    for t in it:
        bag.update([t])
    return bag

def char_counts(token_bag):
    counts = Counter()
    for tok, cnt in token_bag.items():
        for c in tok:
            counts[c] += cnt
    return counts

def filtered(it):
    include_engine = re.compile('^[' + include + ']+$',)
    force_engine = re.compile(f'[{force}]')
    for tok in it:
        if (len(tok) >= min_len
                and include_engine.match(tok)
                # and force_engine.match(tok)
                and not (len(set(tok)) <= 2 and len(tok) >= 3)):
            yield tok


def give_score(token_count_iter):
    include_engine = re.compile('^[' + include + ']+$',)
    force_engine = re.compile(f'[{force}]')

    for tok, cnt in token_count_iter:
        if cnt < 5:
            continue
        # if len(tok) < min_len:
        #     continue
        # if not include_engine.match(tok):
        #     continue
        # if not force_engine.match:
        #     continue
        score = 0
        for c in tok:
            if c in force:
                score += 1
        yield score, tok



def find_good_set(scored_tokens):
    # cnts = dict(zip(force.lowered, itertools.cycle([0])))

    # take_from = scored_tokens[0:]


    tgt_len = 50


    tgts = list(set(force.lower()))
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
        nonlocal scored_tokens
        print(f'starting loop: tgt len {target_len}')

        did_something = True
        while len(good_toks) < target_len and did_something:
            did_something = False
            for score, tok in scored_tokens:
                if not len(good_toks) < target_len-1:
                    break
                # if lowest_c in tok :
                if predicate(tok) and tok not in good_toks:
                    add_tok(tok)
                    did_something = True
        print(f'itercount: {iter_count}, good_toks: {len(good_toks)}')
        print(f'tgt: {tgts}, char_scores: {char_scores}')

    force_engine = re.compile(f'[{force}]')

    loop(lambda tok: lowest_c in tok,
        3,
        )
    loop(lambda tok: lowest_c in tok and not highest_c in tok,
        tgt_len,
        )
    loop(lambda tok: lowest_c in tok,
        tgt_len,
        )
    loop(lambda tok: highest_c not in tok and force_engine.match(tok),
        min(tgt_len, len(good_toks)*2),
        )

    # loop(lambda tok: force_engine.match(tok),
    #     tgt_len,
    #     )

    # loop(lambda tok: True,
    #     tgt_len,
    #     )


    # print('\n\n')
    # for tok in good_toks:
    #     print(tok)

    return good_toks









def main():
    # readfiles()
    token_bag = count_tokens(filtered(read_tokens(read_file_lines())))
    # for token, count in token_bag.items():
    #     print(token, count)

    scored = list(give_score(token_bag.items()))
    scored = sorted(scored, reverse=True)

    words = list(find_good_set(scored))


    while True:
        s = ''
        while len(s) < 300:
            s += random.choice(words)
            s += ' '
        interactive.main_basic(s, False, None, False, None)



if __name__ == '__main__':
    main()
