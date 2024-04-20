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

ALL_CHARS = 'abcdefghijklmnopqrstuvwxyz0123456789`~!@#$%^&*()_-+={}|:"<>?-=[]\\;\',./'


def get_files_from_search_paths(search_paths):
    for path in search_paths:
        print(f'  searching {path}')
        files = glob.glob(path, recursive=True)
        print(f'    found {len(files)} files')
        for fname in files:
            yield fname

def read_lns_from_files(fnames):
    fnames = list(fnames)
    dbg(f'reading {len(fnames)} files.')
    num_lines = 0
    for fname in fnames:
        try:
            with open(fname) as f:
                lns = f.readlines()
                num_lines += len(lns)
                for ln in lns:
                    yield ln
        except UnicodeDecodeError as ude:
            dbg('got UDE from file: ' + fname)
    dbg('num lines: ' + str(num_lines))

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

        self.include_engine = re.compile('^[' + re.escape(self.include_chars) + ']+$',)
        self.force_engine = re.compile(f'[{re.escape(force_chars)}]')

        print(f'Allowed chars: {self.include_chars}')
        print(f'Required chars: {self.force_chars}')

        print()

        print('Searching files for tokens:')
        self.token_set = set(self.filtered(
                tokenize_lns(
                    read_lns_from_files(
                        get_files_from_search_paths(search_paths)))))

        print()

        print(f'Total Allowed Tokens found: {len(self.token_set)}')

        self.subset = set()

    def filtered(self, it):
        for tok in it:
            if (len(tok) >= self.min_len
                    and self.include_engine.match(tok)
                    and self.force_engine.match(tok)
                    and not (len(set(tok)) / len(tok) <= 0.5 and len(tok) > 3)
                    ):
                yield tok


    def find_good_subset(self, tgt_len, tgt_easy_len):
        dbg('>>> FInd good subset')
        tokens = list(self.token_set)
        random.shuffle(tokens)
        dbg(f'{len(tokens)}')



        print(f'Trying to find a good subset with {tgt_len} tokens.')


        tgts = set(self.force_chars.lower())
        # dbg(tgts)
        # tgt_idx = dict(zip(tgts, range(len(tgts))))
        # dbg(tgt_idx)
        # char_scores = [0] * len(tgts)
        char_scores = dict(zip(tgts, itertools.repeat(0)))

        highest_c = ''
        lowest_c = ''

        def update_lowest_and_highest():
            nonlocal lowest_c
            nonlocal highest_c
            lowest_cnt = float('inf')
            highest_cnt = 0
            # for i, (char, cnt) in enumerate(zip(tgts, char_scores)):
            for char, cnt in char_scores.items():
                if cnt < lowest_cnt:
                    lowest_cnt = cnt
                    lowest_c = char
                if cnt > highest_cnt:
                    highest_cnt = cnt
                    highest_c = char
            # dbg(f'update lowest and highest: lowest {lowest_c} {lowest_cnt} highest {highest_c} {highest_cnt}')


        update_lowest_and_highest()

        def tok_genl_score(tok):
            good = 0
            for c in tok:
                if c in tgts:
                    good += 1
            return good / len(tok)

        def add_tok(tok):
            for c in tok:
                # idx = tgt_idx.get(c, None)
                # if idx is not None:
                #     char_scores[idx] += 1
                if c in char_scores:
                    char_scores[c] += 1
            good_toks.add(tok)
            update_lowest_and_highest()

        good_toks = set()

        iter_count = 0

        def loop(predicate, cur_tgt_len, label='xxx'):
            nonlocal lowest_c
            nonlocal iter_count
            nonlocal highest_c
            nonlocal tokens
            # dbg(f'starting loop[{label}]: tgt len {cur_tgt_len}')
            # print(f'starting loop[{label}]: tgt len {cur_tgt_len}')

            did_something = True
            while len(good_toks) < cur_tgt_len and did_something:
                did_something = False
                for tok in tokens:
                    if  len(good_toks) >= cur_tgt_len:
                        break
                    # if lowest_c in tok :
                    if predicate(tok) and tok not in good_toks:
                        add_tok(tok)
                        # dbg(f'adding tok: {tok}')
                        did_something = True
            # dbg(f'itercount: {iter_count}, good_toks: {len(good_toks)}')
            # dbg(f'tgt: {tgts}, char_scores: {char_scores}')

        for c_num in range(len(char_scores)):
            last_c = None
            while True:
                # c =  sorted([(char_scores[idx], c) for c, idx in tgt_idx.items()])[c_num][1]
                sorted_scores = sorted(char_scores.items(), key=lambda item: item[1])

                # print(f'{sorted_scores=}')
                # print(f'sum of scores: {sum([s for c, s in sorted_scores])}')

                c, c_score = sorted_scores[0]

                c1, c1_score = sorted_scores[1]

                if c == last_c and c_score == last_c_score:
                    break
                last_c = c
                last_c_score = c_score
                # loop(lambda tok: c in tok, tgt_len)
                tgt_len_this_iter = min(tgt_len, len(good_toks) + c1_score - c_score + 1)

                random.shuffle(tokens)
                # loop(lambda tok: c in tok and tok_genl_score(tok) > 0.5, tgt_len_this_iter, label = '0.5')
                # loop(lambda tok: c in tok and tok_genl_score(tok) > 0.4, tgt_len_this_iter, label = '0.4')
                # loop(lambda tok: c in tok and tok_genl_score(tok) > 0.3, tgt_len_this_iter, label = '0.3')
                loop(lambda tok: c in tok and tok_genl_score(tok) > 0.25, tgt_len_this_iter, label = '0.25')
                loop(lambda tok: c in tok and tok_genl_score(tok) > 0.15, tgt_len_this_iter, label = '0.15')
                loop(lambda tok: c in tok, tgt_len_this_iter)


        print(f'After phase 0, subset contains {len(good_toks)} tokens')

        num_normal_toks = len(good_toks)

        loop(lambda tok: tok_genl_score(tok) < .1, num_normal_toks + tgt_easy_len, label = 'easy')
        print(f'After phase 1, subset contains {len(good_toks)} tokens')

        # print(tokens)
        # loop(lambda tok: lowest_c in tok,
        #     3, 'A'
        #     )
        # print(f'After phase A, subset contains {len(good_toks)} tokens')
        # loop(lambda tok: lowest_c in tok and not highest_c in tok,
        #     tgt_len, 'B'
        #     )
        # print(f'After phase B, subset contains {len(good_toks)} tokens')
        # loop(lambda tok: lowest_c in tok,
        #     tgt_len, 'C'
        #     )
        # print(f'After phase C, subset contains {len(good_toks)} tokens')
        # loop(lambda tok: highest_c not in tok and self.force_engine.match(tok),
        #     min(tgt_len, len(good_toks)*2), 'D'
        #     )
        # print(f'After phase D, subset contains {len(good_toks)} tokens')

        self.subset = list(good_toks)



    def random_string_from_current_subset(self, tgt_len):
        assert self.subset
        s = ''
        while len(s) < tgt_len:
            s += random.choice(list(self.subset))
            s += ' '
        return s[:-1]



# search_dirs = ['/home/alex/Projects/typing_practice/source_code/boost/**/']
# search_dirs = [
#     '/home/alex/Projects/typing_practice/source_code/abseil-cpp/**/',
#     '/home/alex/Projects/typing_practice/source_code/spdlog/**/',
# ]

# extensions = ['*.h', '*.cpp', '*.cc', '*.cxx', '*.c++', '*.C']


# def test_version():
#     # search_paths = [
#     #     # '/home/alex/Projects/qmk_firmware/**/*.h',
#     #     # '/home/alex/Projects/qmk_firmware/**/*.cpp',
#     # ]

#     def iter():
#         for dir, ext in itertools.product(search_dirs, extensions):
#             assert dir[-1] == '/'
#             print('---->>>', dir+ext )
#             yield dir+ext

#     search_paths = iter()
#     include_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ,.?:;!'
#     force_chars = '&@p_wg#!/?;:\\^\\\\()*zq'
#     min_len = 1
#     return TextGen(search_paths, include_chars, force_chars, min_len)



def create_from_profile(profile):
    search_dirs = [
        '/home/alex/Projects/typing_practice/source_code/abseil-cpp/**/',
        '/home/alex/Projects/typing_practice/source_code/spdlog/**/',
        '/home/alex/Projects/typing_practice/source_code/librdkafka/**/',
        '/home/alex/Projects/typing_practice/source_code/boost/**/',
        # '/home/alex/Projects/typing_practice/source_code/linux/**/',
        '/home/alex/Projects/typing_practice/source_code/django/**/',
        ]

    extensions = ['*.h', '*.c', '*.cpp', '*.cc', '*.cxx', '*.c++', '*.C', '*.py']

    def iter():
        for dir, ext in itertools.product(search_dirs, extensions):
            assert dir[-1] == '/'
            # print(f'\t{dir}{ext}')
            yield dir+ext

    search_paths = iter()
    include_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ,.?:;!#'
    # include_chars = ALL_CHARS
    # force_chars = '&@p_wg#!/?;:\\^\\\\()*zq'


    print('Char Stats:')
    for c in ALL_CHARS:
        seen = profile.times_seen(c)
        if seen:
            percent = 100 * profile.times_correct(c) / seen
            percent_str = f'{percent:5.1f}% of'
        else:
            percent_str = ''
        print(f'  {c}: {percent_str:9s} {seen:4d} times seen.')

    percentages = profile.percentages()

    print()

    to_add_to_include = ''

    for c in ALL_CHARS:
        if profile.percentage(c) and profile.percentage(c) > 0.95 and profile.times_seen(c) > 125 and c not in include_chars:
            to_add_to_include += c


    if to_add_to_include:
        print(f'Adding  {to_add_to_include} to include chars, because you\'re good enough at them/it')
        print()

    include_chars += to_add_to_include


    if percentages:
        force_chars = ''.join([char for percent, char in percentages[ : min(2, len(percentages))]])
        print(f'Setting {force_chars} as required chars because they are the lowest percentage.')
    else:
        force_chars = ''


    times_seen = profile.all_times_seen()
    if times_seen:
        chars = [char for n_seen, char in times_seen[ : min(2, len(times_seen))]]
        dbg(f'2 chars{chars}')
        not_seen_enough = ''.join(chars)
        print(f'Setting {not_seen_enough} as required chars because they are the least practiced.')
        force_chars += not_seen_enough

    print()

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
