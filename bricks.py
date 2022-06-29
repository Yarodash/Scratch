from typing import *

import logic
import random
import scratch_exceptions
import useful
import pygame
import constants


class ManipulatedByUser(pygame.Rect):

    def __init__(self, x: int, y: int, width: int, height: int):
        super().__init__(x, y, width, height)

    def is_cursor_inside(self, x: int, y: int) -> bool:
        return super().collidepoint(x, y)

    def keyboard_press(self, key: int):
        raise NotImplementedError

    def relative_move(self, dx: int, dy: int):
        raise NotImplementedError


class Block(ManipulatedByUser):

    def __init__(self, app: 'App', x: int, y: int, width: int, height: int):
        super().__init__(x, y, width, height)

        self.color = [random.randint(0, 255) for _ in range(3)]

        self.app: 'App' = app
        self.depth: int = self.app.get_current_top_depth()

    def get_center(self) -> Tuple[int, int]:
        return self.x + self.width // 2, self.y + self.height // 2

    def draw(self, surface: pygame.Surface, is_selected: bool, is_dragged: bool) -> None:
        pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height))

    def update_depth(self):
        self.depth = self.app.get_current_top_depth()

    def update_location(self, x, y) -> None:
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

    def check_other_insert_conditions(self, block: Block) -> bool:
        return True

    def can_insert(self, block: Block) -> bool:
        if self.inner:
            return False

        if block.is_recursive_contain_block_spot(self):
            return False

        if self.collidepoint(block.get_center()) and self.check_other_insert_conditions(block):
            return True

        return False

    def insert(self, block: Block) -> None:
        assert self.inner is None
        self.inner = block
        self.update_location(self.x, self.y)

    def extract(self) -> None:
        self.inner = None

    def update_location(self, x: int, y: int) -> None:
        self.x, self.y = x, y
        if self.inner:
            self.inner.update_location(x, y)

    def update_size(self) -> None:
        if self.inner:
            self.inner.update_size()
            self.width, self.height = self.inner.width, self.inner.height

        else:
            self.width = self.default_width
            self.height = self.default_height

    def draw(self, surface: pygame.Surface, is_dragged: bool) -> None:
        pygame.draw.rect(surface, (255, 255, 0), (self.x, self.y, self.width, self.height), 3)
        if self.inner:
            self.inner.draw(surface, False, is_dragged)


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
                    if block_spot.can_insert(self.dragged_block):
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

    def draw(self, screen: pygame.Surface) -> None:
        for block in reversed(self.depth_sorted_blocks):
            block.draw(screen, block is self.selected_block, block is self.dragged_block)

    def update_blocks(self) -> None:
        for block in self.blocks:
            block.update_location(block.x, block.y)
            block.update_size()

    def run(self) -> None:

        self.blocks.append(BlockWithTwoSpots(self, 200, 200))
        self.blocks.append(BlockWithTwoSpots(self, 300, 200))
        self.blocks.append(BlockWithTwoSpots(self, 400, 200))
        self.blocks.append(BlockWithTwoSpots(self, 500, 200))
        self.blocks.append(BlockWithTwoSpots(self, 600, 200))

        screen = pygame.display.set_mode((self.width, self.height))

        try:
            clock = pygame.time.Clock()

            while True:
                self.handle_events()
                self.update_blocks()

                screen.fill(constants.BACKGROUND_COLOR)
                self.draw(screen)
                pygame.display.update()

                clock.tick(self.fps)

        except self.QuitException:
            pass

        finally:
            pygame.display.quit()


class BlockWithTwoSpots(Block):

    def __init__(self, app: 'App', x: int, y: int):
        super().__init__(app, x, y, 200, 100)

        self.first_block_spot: BlockSpot = BlockSpot(app, self, x + 40, y + 25, 40, 50)
        self.second_block_spot: BlockSpot = BlockSpot(app, self, x + 120, y + 25, 40, 50)

    def is_recursive_contain_block_spot(self, block_spot: 'BlockSpot'):
        return any([self.first_block_spot.is_recursive_contain_block(block_spot),
                   self.second_block_spot.is_recursive_contain_block(block_spot)])

    def update_depth(self):
        super().update_depth()
        self.first_block_spot.update_depth()
        self.second_block_spot.update_depth()

    def draw(self, surface: pygame.Surface, is_selected: bool, is_dragged: bool):
        super().draw(surface, is_selected, is_dragged)

        if is_selected:
            pygame.draw.rect(surface, (255, 255, 255), (self.x, self.y, self.width, self.height), 3)

        self.first_block_spot.draw(surface, is_dragged)
        self.second_block_spot.draw(surface, is_dragged)

    def update_location(self, x, y) -> None:
        super().update_location(x, y)

        self.first_block_spot.update_location(self.x + 40, self.y + 25)
        self.second_block_spot.update_location(self.x + 80 + self.first_block_spot.width, self.y + 25)

    def update_size(self) -> None:
        self.first_block_spot.update_size()
        self.second_block_spot.update_size()

        self.width = self.first_block_spot.width + self.second_block_spot.width + 120
        self.height = max(self.first_block_spot.height, self.second_block_spot.height) + 50
