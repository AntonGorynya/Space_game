import asyncio
import curses
import time
import random
import os


STARS = ['+', '*', '.', ':']
SPACE_GARBAGE = []
COROUTINES = []
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


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


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


async def blink(canvas, row, column, symbol='*', timers=None, initial_delay=None):
    states = [
        curses.A_DIM,
        curses.A_NORMAL,
        curses.A_BOLD,
        curses.A_NORMAL
    ]
    if timers is None:
        timers = [2, 0.3, 0.5, 0.5]
    if initial_delay:
        await sleep(tics=initial_delay)
    while True:
        for state, timer in zip(states, timers):
            canvas.addstr(row, column, symbol, state)
            for _ in range(int(timer/0.1)):
                await asyncio.sleep(0)


async def afly_ship(canvas, row, column, max_row, max_column):
    frame_rows, frame_columns = get_frame_size(ROCKET_ANIMATIONS[1])
    prev_frame_number = 0
    next_row = row
    next_colum = column
    while True:
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        if space_pressed:
            COROUTINES.append(
                fire(canvas, row , column + 2)
            )
        if rows_direction ** 2 or columns_direction ** 2:
            next_row = min(max(1, row + rows_direction), max_row - frame_rows - 1)
            next_colum = min(max(1, column + columns_direction), max_column - frame_columns - 1)

        for iteration in range(len(ROCKET_ANIMATIONS)):
            draw_frame(canvas, row, column, ROCKET_ANIMATIONS[prev_frame_number], negative=True)
            next_frame_number = (prev_frame_number + iteration) % 2
            draw_frame(canvas, next_row, next_colum, ROCKET_ANIMATIONS[next_frame_number], negative=False)
            prev_frame_number = next_frame_number
            row = next_row
            column = next_colum
            await asyncio.sleep(0)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()
    frame_rows, frame_columns = get_frame_size(garbage_frame)

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 1
    while row <= frame_rows:
        tmp_frame = "\n".join(garbage_frame.split("\n")[-int(row):])
        draw_frame(canvas, 1, column, tmp_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, 1, column, tmp_frame, negative=True)
        row += speed

    row = 1
    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        if row + frame_rows + 1 >= rows_number:
            garbage_frame = "\n".join(garbage_frame.split("\n")[:-1])
        row += speed


async def fill_orbit_with_garbage(canvas, p=0.05):
    rows_number, columns_number = canvas.getmaxyx()
    while True:
        if random.random() > (1 - p):
            frame = random.choice(SPACE_GARBAGE)
            frame_rows, frame_columns = get_frame_size(frame)
            COROUTINES.append(
                fly_garbage(canvas, random.randint(1, columns_number - frame_columns - 2), frame)
            )
        await asyncio.sleep(0)


def draw(canvas):
    max_row, max_column = canvas.getmaxyx()
    p = 0.05  # коэффицент заполности звездого неба
    star_number = int((max_row - 2) * (max_column - 2) * p)
    init_garbage_number = int((max_row - 2) * p )
    row = max_row // 2
    column = max_column // 2
    canvas.border()
    canvas.timeout(int(TIC_TIMEOUT*1000))
    canvas.nodelay(True)
    curses.curs_set(False)

    COROUTINES.extend([
        fire(canvas, row, column + 2, rows_speed=-0.3, columns_speed=0),
        afly_ship(canvas, row, column, max_row, max_column),
        fill_orbit_with_garbage(canvas),
    ])
    for _ in range(star_number):
        COROUTINES.append(blink(
            canvas,
            random.randint(1, max_row - 2),
            random.randint(1, max_column - 2),
            symbol=random.choice(STARS),
            initial_delay=int(round(random.uniform(0., 2.), 1) / TIC_TIMEOUT)
        ))
    for _ in range(init_garbage_number):
        garbage_frame = random.choice(SPACE_GARBAGE)
        frame_rows, frame_columns = get_frame_size(garbage_frame)
        COROUTINES.append(
            fly_garbage(canvas, random.randint(1, max_column - frame_rows - 2), garbage_frame)
        )

    while True:
        for coroutine in COROUTINES.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                COROUTINES.remove(coroutine)
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
    for file in os.listdir('Animations/space_garbage'):
        with open(os.path.join('Animations/space_garbage', file), 'r') as f:
            SPACE_GARBAGE.append(f.read())

    curses.update_lines_cols()
    curses.wrapper(draw)
