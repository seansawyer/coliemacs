from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple
import time

import tcod
import tcod.event

CONSOLE_WIDTH = 21
CONSOLE_HEIGHT = 12


@dataclass
class Game:
    # drawing context
    root_console: tcod.console.Console
    draw_console: tcod.console.Console
    # game state
    loop_text = ''
    quit_count = 0


class State(Enum):
    TITLE = 'title'
    LOOP = 'loop'


def blit_and_flush(
        from_console: tcod.console.Console,
        to_console: tcod.console.Console
) -> None:
    from_console.blit(
        to_console,
        width=from_console.width,
        height=from_console.height
    )
    tcod.console_flush()


def draw_title(game: Game) -> None:
    game.draw_console.clear()
    game.draw_console.print(0, 0, 'Hello!')


def draw_loop(game: Game) -> None:
    game.draw_console.clear()
    y = 0
    for i in range(0, len(game.loop_text), CONSOLE_WIDTH):
        line = game.loop_text[i:i+CONSOLE_WIDTH]
        game.draw_console.print(0, y, line.upper())
        y += 1


class StateHandler(tcod.event.EventDispatch):

    def __init__(self, next_state: Optional[State], game: Game) -> None:
        """Constructor"""
        self.next_state = next_state
        self.game = game

    def handle(self) -> Tuple[Optional[State], Game]:
        """
        Dispatch pending input events to handler methods, and then return the
        next state and a game instance to use in that state.
        """
        for event in tcod.event.wait():
            self.dispatch(event)
        return self.next_state, self.game

    def draw(self) -> None:
        """Override this to draw the screen for this state."""
        pass

    def on_enter_state(self) -> None:
        self.draw()
        blit_and_flush(self.game.draw_console, self.game.root_console)

    def on_reenter_state(self) -> None:
        self.draw()
        blit_and_flush(self.game.draw_console, self.game.root_console)


class TitleStateHandler(StateHandler):

    def draw(self):
        draw_title(self.game)

    def ev_quit(self, event: tcod.event.Quit) -> None:
        self.next_state = None

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        if event.sym == tcod.event.K_ESCAPE:
            self.next_state = None
        else:
            self.next_state = State.LOOP


class LoopStateHandler(StateHandler):

    def draw(self):
        draw_loop(self.game)

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        if event.sym == tcod.event.K_ESCAPE:
            self.game.quit_count += 1
            if self.game.quit_count == 10:
                self.next_state = None
        elif event.sym == tcod.event.K_BACKSPACE:
            self.game.loop_text = self.game.loop_text[0:-1]
        elif tcod.event.K_a <= event.sym <= tcod.event.K_z:
            self.game.loop_text += chr(event.sym)

    def ev_quit(self, event: tcod.event.Quit) -> None:
        self.next_state = None


def run_fsm(
        state_handlers: Dict[State, StateHandler],
        state: State,
        game: Game
) -> None:
    last_state = None
    while state is not None:
        handler_class = state_handlers[state]
        handler = handler_class(state, game)
        if state == last_state:
            handler.on_reenter_state()
        else:
            handler.on_enter_state()
        last_state = state
        state, game = handler.handle()


def main():
    font_filename = 'Hack_square_64x64.png'
    font_flags = tcod.FONT_LAYOUT_CP437 | tcod.FONT_TYPE_GREYSCALE
    tcod.console_set_custom_font(font_filename, font_flags)
    with tcod.console_init_root(
            CONSOLE_WIDTH,
            CONSOLE_HEIGHT,
            order='F',
            renderer=tcod.RENDERER_SDL2,
            title='ColiEmacs',
            vsync=True
    ) as root_console:
        tcod.console_set_fullscreen(True)
        draw_console = tcod.console.Console(
            CONSOLE_WIDTH,
            CONSOLE_HEIGHT,
            order='F'
        )
        my_state_handlers = {
            State.TITLE: TitleStateHandler,
            State.LOOP: LoopStateHandler,
        }
        game = Game(root_console, draw_console)
        run_fsm(my_state_handlers, State.TITLE, game)


if __name__ == '__main__':
    main()
