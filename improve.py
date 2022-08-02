import curses
import math
from itertools import chain, repeat
import string
from collections import defaultdict

import text_gen

from dbg_log import dbg


TOP_LEFT_WIDTH = 20
TOP_LEFT_HEIGHT = 3


TOP_RIGHT_WIDTH = 20
TOP_RIGHT_HEIGHT = 3

MIDDLE_WIDTH = 70
MIDDLE_HEIGHT = 15







WRONG_NOW = None
WRONG_BEFORE = None
CURSOR = None
WRONG_BEFORE_CURSOR = None
RIGHT = None

def init_colors():
    curses.start_color()
    WRONG_NOW_COLOR = 1
    WRONG_BEFORE_COLOR = 2
    WRONG_BEFORE_CURSOR_COLOR = 4
    RIGHT_COLOR = 5
    curses.init_pair(WRONG_NOW_COLOR, curses.COLOR_BLACK, curses.COLOR_RED)
    curses.init_pair(WRONG_BEFORE_COLOR, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(WRONG_BEFORE_CURSOR_COLOR, curses.COLOR_RED, curses.COLOR_WHITE)
    curses.init_pair(RIGHT_COLOR, curses.COLOR_GREEN, curses.COLOR_BLACK)



    global WRONG_NOW
    global WRONG_BEFORE
    global CURSOR
    global WRONG_BEFORE_CURSOR
    global RIGHT


    WRONG_NOW = curses.color_pair(WRONG_NOW_COLOR)
    WRONG_BEFORE = curses.color_pair(WRONG_BEFORE_COLOR)
    CURSOR = curses.A_REVERSE
    WRONG_BEFORE_CURSOR = curses.color_pair(WRONG_BEFORE_CURSOR_COLOR)
    RIGHT = curses.color_pair(RIGHT_COLOR)

class Frame:
    def __init__(self, scr, y_pos, x_pos, HEIGHT, WIDTH):
        self.scr = scr
        self.y_pos = y_pos
        self.x_pos = x_pos
        self.HEIGHT = HEIGHT
        self.WIDTH = WIDTH
        self.pad = curses.newpad(HEIGHT,WIDTH)
        self._s_parts = []


    def clear(self):
        self._s_parts =[]


    def addstr(self, s, attr=None):
        self._s_parts.append((s,attr))


    def refresh(self):
        self.pad.clear()
        y_pos = self.y_pos
        x_pos = self.x_pos

        Y, X = self.scr.getmaxyx()
        if y_pos < 0:
            y_pos += Y
        if x_pos < 0:
            x_pos += X
        avail_width = min(self.WIDTH, Y-y_pos)
        avail_height = min(self.HEIGHT, X-x_pos)
        col = 0
        row = 0

        # dbg(f'refresh {Y} {X}')


        for c, attr in chain.from_iterable(
            [ zip(s, repeat(attr))
                for s, attr
                in self._s_parts
            ]
        ):
            if row >= self.HEIGHT:
                dbg('frame exit early')
                break
            if row == self.HEIGHT-1 and col == self.WIDTH - 1: # funny last spot case
                dbg('frame exit early')
                break
            if c == '\n':
                row += 1
                # if col == 0 and row != 0:
                #     continue
            else:
                col += 1
                if col == self.WIDTH:
                    col = 0
                    row += 1

            try:
                if attr is not None:
                    self.pad.addch(c, attr)
                else:
                    self.pad.addch(c)
            except curses.error as e:
                dbg(e)
        try:
            self.pad.noutrefresh(0,0, y_pos, x_pos, Y,X)
        except curses.error as e:
            dbg(e)




class GameState:
    def __init__(self):
        self.tgt_str = ''
        self.num_fails = [0]*len(self.tgt_str)
        self.actually_typed = ''
        self.generator = text_gen.test_version()
        self.generator.find_good_subset()

        self.total_correct = 0
        self.total_seen = 0

        self.letter_correct = defaultdict(lambda: 0)
        self.letter_seen = defaultdict(lambda: 0)

        self.init_next()

    def init_next(self):
        self.tgt_str = self.generator.random_string_from_current_subset(100)
        self.num_fails = [0]*len(self.tgt_str)
        self.actually_typed = ''


    @property
    def include_chars(self):
        return self.generator.include_chars


    @property
    def pos(self):
        return len(self.actually_typed)

    def update_scores(self):
        for num in self.num_fails:
            if not num:
                self.total_correct += 1
        self.total_seen += len(self.num_fails)

        for c, num_fails in zip(self.tgt_str, self.num_fails):
            if not num_fails:
                self.letter_correct[c.lower()] += 1
            self.letter_seen[c.lower()] += 1

    def handle_key(self, c):
        done = self._handle_key_inner(c)
        if done:
            self.update_scores()
            self.init_next()


    def _handle_key_inner(self, c):
        dbg('handle key: ', c)
        if len(self.actually_typed) >= len(self.tgt_str):
            return self.actually_typed == self.tgt_str
        if self.tgt_str[self.pos] != c:
            self.num_fails[len(self.actually_typed)] += 1
        self.actually_typed += c
        return self.actually_typed == self.tgt_str

    def backspace(self):
        if self.actually_typed:
            self.actually_typed = self.actually_typed[:-1]


class GameInterface:
    def __init__(self):
        pass

    def setup(self, scr):
        self.scr = scr
        self.score_area = Frame(scr,0,0, 2, 20)
        self.main_area = Frame (scr, 4, 8, 15, 60)
        # self.side_area = Frame (scr, 4, 8, 15, 32)
        self.side_area = Frame(scr, 1, -41, 20, 40 )



    def render(self, gamestate):
        self.render_main_area(gamestate)
        self.render_score_area(gamestate)
        self.render_side_area(gamestate)
        curses.doupdate()

    def render_score_area(self, gamestate):
        acc = '?'
        if gamestate.total_seen:
            acc = 100.0 * gamestate.total_correct / gamestate.total_seen
            acc  = f'{acc:.1f}'
        self.score_area.clear()
        self.score_area.addstr(f'Accuracy: {acc}%\n')
        self.score_area.refresh()


    def render_main_area(self, gamestate):
        self.main_area.clear()
        for i,c in enumerate(gamestate.tgt_str):
            if i > len(gamestate.actually_typed):
                self.main_area.addstr(c, WRONG_BEFORE if gamestate.num_fails[i] else None)
                continue
            if i == len(gamestate.actually_typed):
                self.main_area.addstr(c, WRONG_BEFORE_CURSOR
                                        if gamestate.num_fails[i]
                                        else CURSOR)
                continue
            if gamestate.actually_typed[i] != c:
                self.main_area.addstr(gamestate.actually_typed[i],  WRONG_NOW)
            elif gamestate.num_fails[i]:
                self.main_area.addstr(c , WRONG_BEFORE)
            else:
                self.main_area.addstr(c, RIGHT)
        self.main_area.refresh()


    def render_side_area(self, gamestate):
        dbg('render side area')
        entry_len = len('q: 100%   ')
        ncols = self.side_area.WIDTH // entry_len

        chars  = sorted(set(gamestate.include_chars.lower()))


        ncols = 3
        nrows = math.ceil(len(chars) / ncols)
        s = ''
        for i in range(len(chars)):
            col = i % ncols
            row = i // ncols
            j = row + col*nrows
            c = chars[j]

            n_correct = gamestate.letter_correct[c]
            n_seen = gamestate.letter_seen[c]

            acc = '?%'
            if n_seen:
                acc = 100.0 * n_correct / n_seen
                acc  = f'{acc:.0f}%'

            s += f'{c}: {acc:4s}'
            if col == ncols-1 and row != nrows -1:
                s+= '\n'
            elif col != ncols -1:
                s += '  '

        dbg(s)

        self.side_area.clear()
        self.side_area.addstr(s)
        self.side_area.refresh()




class Game:

    def __init__(self):
        self.state = GameState()
        self.interface = GameInterface()


    def loop(self):
        i = 0
        while True:
            self.interface.render(self.state)
            key = self.scr.getkey()
            if key in ('KEY_BACKSPACE', '\b', '\x7f'):
                self.state.backspace()
                continue
            if key in string.printable and len(key) == 1:
                self.state.handle_key(key)





    def setup(self):
        self.interface.setup(self.scr)
        self.loop()



    def start(self):
        try:
            self.scr = curses.initscr()
            curses.noecho()
            curses.cbreak()
            self.scr.keypad(True)
            curses.curs_set(False)
            self.scr.clear()
            self.scr.refresh()
            init_colors()
            self.setup()
            self.main_loop()
        finally:
            curses.endwin()


if __name__ == '__main__':
    game= Game()
    game.start()
