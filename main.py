import asyncio
import curses
import time
import random
from types import coroutine

STARS = ['+', '*', '.', ':']
TIC_TIMEOUT = 0.1


class EventLoopCommand():

    def __await__(self):
        return (yield self)


class Sleep(EventLoopCommand):

    def __init__(self, seconds):
        self.seconds = seconds


async def blink(canvas, row, column, symbol='*', timers=None):
    states = [
        curses.A_DIM,
        curses.A_NORMAL,
        curses.A_BOLD,
        curses.A_NORMAL
    ]
    if timers is None:
        timers = [2, 0.3, 0.5, 0.5]

    for _ in range(int(round(random.uniform(0., 2.), 1) / 0.1)):
        await asyncio.sleep(0)
    while True:
        for state, timer in zip(states, timers):
            canvas.addstr(row, column, symbol, state)
            for _ in range(int(timer/0.1)):
                await asyncio.sleep(0)


def draw(canvas):
    max_row, max_column = canvas.getmaxyx()
    p = 0.05  # коэффицент заполности звездого неба
    star_number = int((max_row - 2) * (max_column - 2) * p)
    canvas.border()
    canvas.timeout(int(TIC_TIMEOUT*1000))
    curses.curs_set(False)

    coroutines = []
    for column_number in range(star_number):
        row = random.randint(1, max_row - 2)
        column = random.randint(1, max_column - 2)
        symbol = random.choice(STARS)
        coroutines.append(blink(canvas, row, column, symbol=symbol))

    while True:
        for coroutine in coroutines.copy():
            try:
                blink_command = coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        time.sleep(TIC_TIMEOUT)
        canvas.refresh()


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
