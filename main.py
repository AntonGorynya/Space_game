import asyncio
import curses
import time
import random
import os

from physics import update_speed
from obstacles import Obstacle, has_collision, show_obstacles
from curses_tools import draw_frame, read_controls, get_frame_size


STARS = ['+', '*', '.', ':']
SPACE_GARBAGE = []
OBSTACLES = []
COROUTINES = []
TIC_TIMEOUT = 0.1


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
    row_speed, column_speed = 0, 0
    while True:
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        if space_pressed:
            COROUTINES.append(
                fire(canvas, row, column + 2)
            )

        row_speed, column_speed = update_speed(row_speed, column_speed, rows_direction, columns_direction)
        next_row = min(max(1, row + row_speed), max_row - frame_rows - 1)
        next_colum = min(max(1, column + column_speed), max_column - frame_columns - 1)

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
    column = min(column, columns_number - frame_columns - 1)

    row = 2
    obstacle = Obstacle(row, column, 1, frame_columns)
    OBSTACLES.append(obstacle)
    while row <= frame_rows:
        tmp_frame = "\n".join(garbage_frame.split("\n")[-int(row):])
        draw_frame(canvas, 1, column, tmp_frame)
        obstacle.rows_size = int(row)
        await asyncio.sleep(0)
        draw_frame(canvas, 1, column, tmp_frame, negative=True)
        row += speed

    row = 1
    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        obstacle.row = int(row)
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
    init_garbage_number = max(int((max_row - 2) * p), 1)
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
    COROUTINES.append(show_obstacles(canvas, OBSTACLES))

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
