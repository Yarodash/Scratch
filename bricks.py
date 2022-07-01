from typing import *

import logic
import random
import scratch_exceptions
import useful
import pygame
import constants
import colorsys


class ManipulatedByUser(pygame.Rect):

    def __init__(self, x: int, y: int, width: int, height: int):
        super().__init__(x, y, width, height)

    def is_cursor_inside(self, x: int, y: int) -> bool:
        return super().collidepoint(x, y)

    def keyboard_press(self, key: int):
        raise NotImplementedError

    def relative_move(self, dx: int, dy: int):
        raise NotImplementedError


class ExpandingRect(pygame.Rect):

    def expanded_with(self, other: pygame.Rect) -> 'ExpandingRect':
        left = min(self.x, other.x)
        top = min(self.y, other.y)
        right = max(self.x + self.width, other.x + other.width)
        bottom = max(self.y + self.height, other.y + other.height)

        return ExpandingRect(left, top, right - left, bottom - top)


class Block(ManipulatedByUser):

    def __init__(self, app: 'App', x: int, y: int, width: int, height: int):
        super().__init__(x, y, width, height)

        self.color = useful.color_generator.new_color()

        self.app: 'App' = app
        self.owner: Optional['BlockSpot'] = None
        self.depth: int = self.app.get_current_top_depth()

    def get_center(self) -> Tuple[int, int]:
        return self.x + self.width // 2, self.y + self.height // 2

    def get_full_content_rect(self) -> ExpandingRect:
        return ExpandingRect(self.x, self.y, self.width, self.height)

    def draw(self, surface: pygame.Surface, is_selected: bool) -> None:
        pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height))

    def draw_for_app(self, surface: pygame.Surface, transparent_surface: pygame.Surface, is_selected: bool,
                     is_dragged: bool) -> None:
        if is_dragged:
            transparent_surface.fill((111, 231, 51))
            self.draw(transparent_surface, is_selected)
            transparent_surface.set_alpha(127)
            transparent_surface.set_colorkey((111, 231, 51))
            surface.blit(transparent_surface, (0, 0))

        else:
            self.draw(surface, is_selected)

    def update_depth(self):
        self.depth = self.app.get_current_top_depth()

    def update_location(self, x: int, y: int) -> None:
        self.x, self.y = x, y

    def update_size(self) -> None:
        pass

    def is_recursive_contain_block_spot(self, block_spot: 'BlockSpot') -> bool:
        return False

    def keyboard_press(self, key: int) -> None:
        pass

    def relative_move(self, dx: int, dy: int) -> None:
        self.x += dx
        self.y += dy
        self.update_location(self.x, self.y)


class BlockSpot(pygame.Rect):

    def __init__(self, app: 'App', owner: Block, x: int, y: int, width: int, height: int):
        super().__init__(x, y, width, height)

        self.default_width: int = width
        self.default_height: int = height

        self.app = app
        self.owner: Block = owner
        self.inner: Optional[Block] = None

        self.app.add_new_block_spot(self)

    def is_recursive_contain_block(self, block_spot: 'BlockSpot') -> bool:
        if self is block_spot:
            return True

        if self.inner:
            return self.inner.is_recursive_contain_block_spot(block_spot)

        return False

    def update_depth(self):
        if self.inner:
            self.inner.update_depth()

    def get_full_content_rect(self) -> ExpandingRect:
        return ExpandingRect(self.x, self.y, self.width, self.height)

    def check_other_insert_conditions(self, block: Block) -> bool:
        return True

    def can_insert(self, block: Block, cursor_x: int, cursor_y: int) -> bool:
        if self.inner:
            return False

        if block.is_recursive_contain_block_spot(self):
            return False

        if self.collidepoint(cursor_x, cursor_y) and self.check_other_insert_conditions(block):
            return True

        return False

    def insert(self, block: Block) -> None:
        assert self.inner is None
        self.inner = block
        self.update_location(self.x, self.y)
        block.owner = self

    def extract(self) -> None:
        if self.inner:
            self.inner.owner = None
        self.inner = None

    def update_location(self, x: int, y: int) -> None:
        self.x, self.y = x, y
        if self.inner:
            self.inner.update_location(x, y)

    def update_size(self) -> None:
        if self.inner:
            self.inner.update_size()
            inner_size = self.inner.get_full_content_rect()

            self.width, self.height = inner_size.width, inner_size.height

        else:
            self.width = self.default_width
            self.height = self.default_height

    def draw(self, surface: pygame.Surface) -> None:
        #pygame.draw.rect(surface, (255, 255, 255), (self.x, self.y, self.width, self.height), 3)
        pygame.draw.rect(surface, (255, 255, 255), (self.x - 1, self.y - 1, self.width + 2, self.height + 2), 3)

        if self.inner:
            self.inner.draw(surface, False)


class App:
    class QuitException(Exception):
        pass

    def __init__(self, width: int, height: int, fps: int):
        self.width: int = width
        self.height: int = height
        self.fps: int = fps

        self.selected_block: Optional[Block] = None
        self.dragged_block: Optional[Block] = None
        self.current_top_depth = 0

        self.blocks: List[Block] = []
        self.block_spots: List[BlockSpot] = []
        self.variable_scope: logic.VariableScope = logic.VariableScope()

        self.default_in_block_font = pygame.font.SysFont('Consolas', 24)

    def get_current_top_depth(self):
        self.current_top_depth += 1
        return self.current_top_depth

    @property
    def depth_sorted_blocks(self):
        return sorted(self.blocks, key=lambda block: block.depth, reverse=True)

    def add_new_block_spot(self, new_block_spot: BlockSpot) -> None:
        self.block_spots.append(new_block_spot)

    def handle_event(self, event) -> None:
        if event.type == pygame.QUIT:
            raise self.QuitException

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == constants.LEFT_MOUSE_BUTTON:
            self.selected_block = self.dragged_block = None

            for block in self.depth_sorted_blocks:
                if block.is_cursor_inside(*event.pos):
                    self.selected_block = self.dragged_block = block
                    break

            if self.selected_block:
                self.selected_block.update_depth()

                for block_spot in self.block_spots:
                    if block_spot.inner == self.selected_block:
                        block_spot.extract()

        if event.type == pygame.MOUSEBUTTONUP and event.button == constants.LEFT_MOUSE_BUTTON:
            if self.dragged_block:
                for block_spot in self.block_spots:
                    if block_spot.can_insert(self.dragged_block, *event.pos):
                        block_spot.insert(self.dragged_block)
                        break

            self.dragged_block = None

        if event.type == pygame.MOUSEMOTION and self.dragged_block:
            self.dragged_block.relative_move(*event.rel)

        if event.type == pygame.KEYDOWN:
            if self.selected_block:
                self.selected_block.keyboard_press(event.key)

    def handle_events(self) -> None:
        for event in pygame.event.get():
            self.handle_event(event)

    def draw(self, drawable: pygame.Surface, drawable_transparent: pygame.Surface) -> None:
        for block in reversed(self.depth_sorted_blocks):
            if block.owner:
                continue

            block.draw_for_app(drawable,
                               drawable_transparent,
                               block is self.selected_block,
                               block is self.dragged_block)

    def update_blocks(self) -> None:
        for block in self.blocks:
            block.update_location(block.x, block.y)
            block.update_size()

    def run(self) -> None:

        self.blocks.append(PrintBlock(self, 0, 0))
        self.blocks.append(PrintBlock(self, 0, 0))
        self.blocks.append(PrintBlock(self, 0, 0))
        self.blocks.append(IntPlusIntBlock(self, 0, 0))
        self.blocks.append(IntPlusIntBlock(self, 0, 50))
        self.blocks.append(IntPlusIntBlock(self, 0, 100))
        self.blocks.append(IntSubIntBlock(self, 100, 0))
        self.blocks.append(IntSubIntBlock(self, 100, 50))
        self.blocks.append(IntSubIntBlock(self, 100, 100))
        self.blocks.append(IntMultiplyIntBlock(self, 200, 0))
        self.blocks.append(IntMultiplyIntBlock(self, 200, 50))
        self.blocks.append(IntMultiplyIntBlock(self, 200, 100))
        self.blocks.append(IntDivIntBlock(self, 300, 0))
        self.blocks.append(IntDivIntBlock(self, 300, 50))
        self.blocks.append(IntDivIntBlock(self, 300, 100))

        for i in range(48):
            self.blocks.append(NumberBlock(self, i * 20, 200))

        screen = pygame.display.set_mode((self.width, self.height))
        drawable = pygame.Surface((self.width, self.height), pygame.SRCALPHA, 32)
        drawable_transparent = pygame.Surface((self.width, self.height), pygame.SRCALPHA, 32)

        try:
            clock = pygame.time.Clock()

            while True:
                self.handle_events()
                self.update_blocks()

                for block in self.blocks:
                    try:
                        if isinstance(block, PrintBlock):
                            block.execute()
                    except scratch_exceptions.ScratchRuntimeException:
                        pass

                self.update_blocks()

                screen.fill(constants.BACKGROUND_COLOR)
                drawable.fill(constants.BACKGROUND_COLOR)

                self.draw(drawable, drawable_transparent)
                screen.blit(drawable, (0, 0))
                pygame.display.update()

                clock.tick(self.fps)

        except self.QuitException:
            pass

        finally:
            pygame.display.quit()


class BlockWithOneSpot(Block):

    def __init__(self, app: 'App', x: int, y: int):
        super().__init__(app, x, y, 200, 100)

        self.first_block_spot: BlockSpot = BlockSpot(app, self, x, y + 100, 200, 50)

    def is_recursive_contain_block_spot(self, block_spot: 'BlockSpot'):
        return any([self.first_block_spot.is_recursive_contain_block(block_spot)])

    def get_full_content_rect(self) -> ExpandingRect:
        return ExpandingRect(self.x, self.y, self.width, self.height) \
            .expanded_with(self.first_block_spot.get_full_content_rect())

    def update_depth(self):
        super().update_depth()
        self.first_block_spot.update_depth()

    def draw(self, surface: pygame.Surface, is_selected: bool):
        super().draw(surface, is_selected)

        if is_selected:
            pygame.draw.rect(surface, (255, 255, 255), (self.x, self.y, self.width, self.height), 3)

        self.first_block_spot.draw(surface)

    def update_location(self, x, y) -> None:
        super().update_location(x, y)

        self.first_block_spot.update_location(self.x, self.y + 100)

    def update_size(self) -> None:
        self.first_block_spot.update_size()


class BlockWithTwoSpots(Block):

    def __init__(self, app: 'App', x: int, y: int):
        super().__init__(app, x, y, 80, 40)

        self.first_block_spot: BlockSpot = BlockSpot(app, self, x + 5, y + 5, 30, 30)
        self.second_block_spot: BlockSpot = BlockSpot(app, self, x + 45, y + 5, 30, 30)

    def is_recursive_contain_block_spot(self, block_spot: 'BlockSpot'):
        return any([self.first_block_spot.is_recursive_contain_block(block_spot),
                    self.second_block_spot.is_recursive_contain_block(block_spot)])

    def update_depth(self):
        super().update_depth()
        self.first_block_spot.update_depth()
        self.second_block_spot.update_depth()

    def draw(self, surface: pygame.Surface, is_selected: bool):
        super().draw(surface, is_selected)

        if is_selected:
            pygame.draw.rect(surface, (255, 255, 255), (self.x, self.y, self.width, self.height), 3)

        self.first_block_spot.draw(surface)
        self.second_block_spot.draw(surface)

    def update_location(self, x, y) -> None:
        super().update_location(x, y)

        self.first_block_spot.update_location(self.x + 5, self.y + 5)
        self.second_block_spot.update_location(self.x + 15 + self.first_block_spot.width, self.y + 5)

    def update_size(self) -> None:
        self.first_block_spot.update_size()
        self.second_block_spot.update_size()

        self.width = self.first_block_spot.width + self.second_block_spot.width + 20
        self.height = max(self.first_block_spot.height, self.second_block_spot.height) + 10


class ReturnsBool(Block):
    pass


class ReturnsInt(Block):

    def calculate(self) -> int:
        raise NotImplementedError


class OnlyBoolBlockSpot(BlockSpot):

    def check_other_insert_conditions(self, block: Block) -> bool:
        return isinstance(block, ReturnsBool)


class OnlyIntBlockSpot(BlockSpot):

    def check_other_insert_conditions(self, block: Block) -> bool:
        return isinstance(block, ReturnsInt)


class NumberBlock(ReturnsInt):

    def __init__(self, app: 'App', x: int, y: int):
        super().__init__(app, x, y, 20, 20)

        self.text: str = ''

    def draw(self, surface: pygame.Surface, is_selected: bool) -> None:
        super().draw(surface, is_selected)

        text_surface = self.app.default_in_block_font.render(self.text, True, (0, 0, 0))
        surface.blit(text_surface, (self.x + 10, self.y + 10))

    def update_size(self) -> None:
        text_surface = self.app.default_in_block_font.render(self.text, True, (0, 0, 0))
        self.width = 20 + text_surface.get_width()
        self.height = 20 + text_surface.get_height()

    def keyboard_press(self, key: int) -> None:
        self.text = useful.apply_key(self.text, key)

    def calculate(self) -> int:
        if useful.represents_integer(self.text):
            return int(self.text)

        raise scratch_exceptions.InvalidNumberException


class BinaryIntOperation(ReturnsInt):

    def __init__(self, app: 'App', x: int, y: int, op_text: str, op_function: Callable[[int, int], int]):
        super().__init__(app, x, y, 80, 40)

        self.left_spot: OnlyIntBlockSpot = OnlyIntBlockSpot(app, self, 0, 0, 30, 30)
        self.right_spot: OnlyIntBlockSpot = OnlyIntBlockSpot(app, self, 0, 0, 30, 30)

        self.op_text_surface = self.app.default_in_block_font.render(op_text, True, (0, 0, 0))
        self.op_function = op_function

    def is_recursive_contain_block_spot(self, block_spot: 'BlockSpot'):
        return any([self.left_spot.is_recursive_contain_block(block_spot),
                    self.right_spot.is_recursive_contain_block(block_spot)])

    def update_depth(self):
        super().update_depth()
        self.left_spot.update_depth()
        self.right_spot.update_depth()

    def draw(self, surface: pygame.Surface, is_selected: bool):
        super().draw(surface, is_selected)

        if is_selected:
            pygame.draw.rect(surface, (255, 255, 255), (self.x, self.y, self.width, self.height), 3)

        self.left_spot.draw(surface)
        self.right_spot.draw(surface)

        op_location = self.op_text_surface.get_rect(
            center=pygame.Rect(self.left_spot.right, self.y, self.right_spot.left - self.left_spot.right,
                               self.height).center)
        surface.blit(self.op_text_surface, op_location)

    def update_location(self, x, y) -> None:
        super().update_location(x, y)

        self.left_spot.update_location(self.x + 5,
                                       self.y + 5 + (self.height - self.left_spot.height - 10) // 2)
        self.right_spot.update_location(self.x + 15 + self.left_spot.width + self.op_text_surface.get_width(),
                                        self.y + 5 + (self.height - self.right_spot.height - 10) // 2)

    def update_size(self) -> None:
        self.left_spot.update_size()
        self.right_spot.update_size()

        self.width = self.left_spot.width + self.op_text_surface.get_width() + self.right_spot.width + 20
        self.height = max(self.left_spot.height, self.right_spot.height) + 10

    def calculate(self) -> int:
        if self.left_spot.inner and self.right_spot.inner:
            return self.op_function(self.left_spot.inner.calculate(), self.right_spot.inner.calculate())

        raise scratch_exceptions.EmptyArgumentException


class IntPlusIntBlock(BinaryIntOperation):

    def __init__(self, app: 'App', x: int, y: int):
        super().__init__(app, x, y, '+', lambda a, b: a + b)


class IntSubIntBlock(BinaryIntOperation):

    def __init__(self, app: 'App', x: int, y: int):
        super().__init__(app, x, y, '-', lambda a, b: a - b)


class IntMultiplyIntBlock(BinaryIntOperation):

    def __init__(self, app: 'App', x: int, y: int):
        super().__init__(app, x, y, '×', lambda a, b: a * b)


class IntDivIntBlock(BinaryIntOperation):

    def __init__(self, app: 'App', x: int, y: int):
        super().__init__(app, x, y, '÷', lambda a, b: a // b)


class PrintBlock(Block):

    def __init__(self, app: 'App', x: int, y: int):
        super().__init__(app, x, y, 80, 40)

        self.spot: OnlyIntBlockSpot = OnlyIntBlockSpot(app, self, 0, 0, 30, 30)

        self.text_surface = self.app.default_in_block_font.render('Print', True, (0, 0, 0))
        self.result_surface = pygame.Surface((0, 0))

    def is_recursive_contain_block_spot(self, block_spot: 'BlockSpot'):
        return self.spot.is_recursive_contain_block(block_spot)

    def update_depth(self):
        super().update_depth()
        self.spot.update_depth()

    def draw(self, surface: pygame.Surface, is_selected: bool):
        super().draw(surface, is_selected)

        if is_selected:
            pygame.draw.rect(surface, (255, 255, 255), (self.x, self.y, self.width, self.height), 3)

        self.spot.draw(surface)

        location = self.text_surface.get_rect(center=pygame.Rect(self.left, self.y,
                                                                 self.text_surface.get_width() + 10, self.height)
                                              .center)
        surface.blit(self.text_surface, location)

        location = self.text_surface.get_rect(center=pygame.Rect(self.spot.right, self.y,
                                                                 self.result_surface.get_width() + 10, self.height)
                                              .center)
        surface.blit(self.result_surface, location)

    def update_location(self, x, y) -> None:
        super().update_location(x, y)

        self.spot.update_location(self.x + self.text_surface.get_width() + 10, self.y + 5)

    def update_size(self) -> None:
        self.spot.update_size()

        self.width = self.text_surface.get_width() + self.spot.width + self.result_surface.get_width() + 20
        self.height = self.spot.height + 10

    def execute(self) -> None:
        if self.spot.inner:
            text = ' = {}'.format(self.spot.inner.calculate())
            self.result_surface = self.app.default_in_block_font.render(text, True, (0, 0, 0))

        else:
            self.result_surface = pygame.Surface((0, 0))
            raise scratch_exceptions.EmptyArgumentException
