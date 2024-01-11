import asyncio
import curses
import time
import random
from types import coroutine

STARS = ['+', '*', '.', ':']
TIC_TIMEOUT = 0.1
SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258


def read_controls(canvas):
    """Read keys pressed and returns tuple witl controls state."""

    rows_direction = columns_direction = 0
    space_pressed = False

    while True:
        pressed_key_code = canvas.getch()

        if pressed_key_code == -1:
            # https://docs.python.org/3/library/curses.html#curses.window.getch
            break

        if pressed_key_code == UP_KEY_CODE:
            rows_direction = -1

        if pressed_key_code == DOWN_KEY_CODE:
            rows_direction = 1

        if pressed_key_code == RIGHT_KEY_CODE:
            columns_direction = 1

        if pressed_key_code == LEFT_KEY_CODE:
            columns_direction = -1

        if pressed_key_code == SPACE_KEY_CODE:
            space_pressed = True

    return rows_direction, columns_direction, space_pressed


def draw_frame(canvas, start_row, start_column, text, negative=False):
    """Draw multiline text fragment on canvas, erase text instead of drawing if negative=True is specified."""

    rows_number, columns_number = canvas.getmaxyx()

    for row, line in enumerate(text.splitlines(), round(start_row)):
        if row < 0:
            continue

        if row >= rows_number:
            break

        for column, symbol in enumerate(line, round(start_column)):
            if column < 0:
                continue

            if column >= columns_number:
                break

            if symbol == ' ':
                continue

            # Check that current position it is not in a lower right corner of the window
            # Curses will raise exception in that case. Don`t ask why…
            # https://docs.python.org/3/library/curses.html#curses.window.addch
            if row == rows_number - 1 and column == columns_number - 1:
                continue

            symbol = symbol if not negative else ' '
            canvas.addch(row, column, symbol)


def get_frame_size(text):
    """Calculate size of multiline text fragment, return pair — number of rows and colums."""

    lines = text.splitlines()
    rows = len(lines)
    columns = max([len(line) for line in lines])
    return rows, columns


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 1 < row < max_row and 1 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def animate(canvas, start_row, start_column, frames):
    while True:
        for frame_number, frame in enumerate(frames):
            draw_frame(canvas, start_row, start_column, frames[frame_number-1], negative=True)
            draw_frame(canvas, start_row, start_column, frame, negative=False)
            canvas.refresh()
            await asyncio.sleep(0)




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

    coroutines = [
        fire(canvas, max_row // 2, max_column // 2, rows_speed=-0.3, columns_speed=0),
        animate(canvas, max_row // 2 - 2, max_column // 2 - 2, ROCKET_ANIMATIONS)
    ]
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
    with open('Animations/rocket_frame_1.txt', 'r') as f:
        rocket_frame_1 = f.read()
    with open('Animations/rocket_frame_2.txt', 'r') as f:
        rocket_frame_2 = f.read()
    ROCKET_ANIMATIONS = [
        rocket_frame_1,
        rocket_frame_2
    ]

    curses.update_lines_cols()
    curses.wrapper(draw)