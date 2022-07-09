from typing import *

import random
import scratch_exceptions
import useful
import pygame
import constants
import collections


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


class UpdatableRect(ExpandingRect):

    def __init__(self, x: int, y: int, width: int, height: int):
        super().__init__(x, y, width, height)
        self.full_content_rect: ExpandingRect = ExpandingRect(x, y, width, height)

    def calculate_full_content_rect(self) -> None:
        raise NotImplementedError

    def update_depth(self) -> None:
        raise NotImplementedError

    def update_location(self, x, y) -> None:
        self.x, self.y = x, y

    def update_size(self) -> None:
        raise NotImplementedError

    def update_all(self) -> None:
        self.update_size()
        self.calculate_full_content_rect()

    def draw(self, surface: pygame.Surface, is_selected: bool) -> None:
        raise NotImplementedError

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


class Block(UpdatableRect, ManipulatedByUser):

    def __init__(self, app: 'App', x: int, y: int, width: int, height: int):
        super().__init__(x, y, width, height)
        self.color = useful.color_generator.new_color()

        self.app: 'App' = app
        self.owner: Optional['BlockSpot'] = None
        self.depth: int = self.app.get_current_top_depth()

    def calculate_full_content_rect(self) -> None:
        self.full_content_rect = ExpandingRect(self.x, self.y, self.width, self.height)

    def draw(self, surface: pygame.Surface, is_selected: bool) -> None:
        pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height))

    def update_depth(self):
        self.depth = self.app.get_current_top_depth()

    def update_size(self) -> None:
        pass

    def is_recursive_contain_block_spot(self, block_spot: 'BlockSpot') -> bool:
        return False

    def keyboard_press(self, key: int) -> None:
        pass

    def relative_move(self, dx: int, dy: int) -> None:
        self.update_location(self.x + dx, self.y + dy)


class BlockSpot(UpdatableRect):

    def __init__(self, app: 'App', owner: Block, x: int, y: int, width: int, height: int):
        super().__init__(x, y, width, height)

        self.default_width: int = width
        self.default_height: int = height

        self.app = app
        self.owner: Block = owner
        self.inner: Optional[Block] = None

        self.app.add_new_block_spot(self)

    def is_recursive_contain_block_spot(self, block_spot: 'BlockSpot') -> bool:
        if self is block_spot:
            return True

        if self.inner:
            return self.inner.is_recursive_contain_block_spot(block_spot)

        return False

    def update_depth(self):
        if self.inner:
            self.inner.update_depth()

    def calculate_full_content_rect(self) -> None:
        self.full_content_rect = ExpandingRect(self.x, self.y, self.width, self.height)

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
            self.inner.update_all()
            inner_size = self.inner.full_content_rect

            self.width, self.height = inner_size.width, inner_size.height

        else:
            self.width = self.default_width
            self.height = self.default_height

    def draw(self, surface: pygame.Surface, is_selected: bool) -> None:
        #pygame.draw.rect(surface, (255, 255, 255), (self.x, self.y, self.width, self.height), 1)
        # pygame.draw.rect(surface, (255, 255, 255), (self.x - 1, self.y - 1, self.width + 2, self.height + 2), 3)

        if self.inner:
            self.inner.draw(surface, False)


class TextBlock(Block):

    def __init__(self, app: 'App', x: int, y: int, text: str, text_color: Tuple[float, float, float] = (0, 0, 0)):
        super().__init__(app, x, y, 0, 0)

        self.text_color = text_color
        self.text_surface = self.app.default_in_block_font.render(text, True, self.text_color)

    def set_text(self, text):
        self.text_surface = self.app.default_in_block_font.render(text, True, self.text_color)

    def update_size(self) -> None:
        self.width = self.text_surface.get_width()
        self.height = self.text_surface.get_height()

    def draw(self, surface: pygame.Surface, is_selected: bool) -> None:
        # pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height))
        surface.blit(self.text_surface,
                     (self.x + (self.width - self.text_surface.get_width()) // 2,
                      self.y + (self.height - self.text_surface.get_height()) // 2))


class GridBlock(Block):

    def __init__(self, app: 'App', x: int, y: int, content: List[Dict[str, Any]]):
        super().__init__(app, x, y, 0, 0)

        self.content: List[Dict[str, Any]] = content

    def update_depth(self):
        super().update_depth()

        for single_inner in self.content:
            instance = single_inner['instance']
            instance.update_depth()

    def calculate_full_content_rect(self) -> None:
        self.full_content_rect = ExpandingRect(self.x, self.y, self.width, self.height)

    def self_draw(self, surface: pygame.Surface, is_selected: bool) -> None:
        super().draw(surface, is_selected)

        if is_selected:
            pygame.draw.rect(surface, (255, 255, 255), (self.x, self.y, self.width, self.height), 3)

    def draw(self, surface: pygame.Surface, is_selected: bool) -> None:
        self.self_draw(surface, is_selected)

        for single_inner in self.content:
            single_inner['instance'].draw(surface, False)

    def calculate_content(self):
        for single_inner in self.content:
            single_inner['instance'].update_all()

        content_converted = [(single_inner['instance'],
                              *single_inner['instance'].full_content_rect.size,
                              single_inner.get('row', 0),
                              single_inner.get('column', 0),
                              single_inner.get('rowspan', 1),
                              single_inner.get('columnspan', 1)) for single_inner in self.content]

        total_rows = total_columns = 0

        for _, _, _, row, column, rowspan, columnspan in content_converted:
            total_rows = max(total_rows, row + rowspan)
            total_columns = max(total_columns, column + columnspan)

        rows_size = [0] * total_rows
        columns_size = [0] * total_columns

        for _, width, height, row, column, rowspan, columnspan in content_converted:
            row_height = height // rowspan + 10
            column_width = width // columnspan + 10

            for i in range(row, row + rowspan):
                rows_size[i] = max(rows_size[i], row_height)

            for i in range(column, column + columnspan):
                columns_size[i] = max(columns_size[i], column_width)

        for instance, width, height, row, column, rowspan, columnspan in content_converted:
            total_height = sum(rows_size[row: row + rowspan])
            total_width = sum(columns_size[column: column + columnspan])

            shift_top = sum(rows_size[:row])
            shift_left = sum(columns_size[:column])

            instance.update_location(self.x + shift_left + (total_width - width) // 2,
                                     self.y + shift_top + (total_height - height) // 2)

        self.width = sum(columns_size)
        self.height = sum(rows_size)

    def __getattr__(self, item):
        for single_inner in self.content:
            if single_inner.get('name', None) == item:
                return single_inner['instance']

        return self.__getattribute__(item)

    def update_size(self) -> None:
        self.calculate_content()

    def is_recursive_contain_block_spot(self, block_spot: 'BlockSpot') -> bool:
        for single_inner in self.content:
            if single_inner['instance'].is_recursive_contain_block_spot(block_spot):
                return True

        return False


class VariableScope:

    def __init__(self):
        self.variables: dict[str, Any] = {}

    def set_variable(self, var_name: str, value: Any) -> None:
        self.variables[var_name] = value

    def get_variable(self, var_name: str) -> Any:
        try:
            return self.variables[var_name]
        except KeyError:
            raise scratch_exceptions.InvalidVariableNameException


class App:
    class QuitException(Exception):
        pass

    def __init__(self, width: int, height: int, fps: int):
        self.width: int = width
        self.height: int = height
        self.fps: int = fps

        self.default_in_block_font: pygame.font.Font = pygame.font.SysFont('Consolas', 16)

        self.variable_scope: VariableScope = VariableScope()

        self.selected_block: Optional[Block] = None
        self.dragged_block: Optional[Block] = None
        self.current_top_depth = 0

        self.blocks: List[Block] = []
        self.block_spots: List[BlockSpot] = []

        self.event_handlers: collections.defaultdict[constants.TriggeredEvent, List['EventBrick']] \
            = collections.defaultdict(list)

        self.triggered_events: List[constants.TriggeredEvent] = []
        self.executing_bricks: List['Brick'] = []

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
            else:
                if event.key == pygame.K_SPACE:
                    self.triggered_events.append(constants.TriggeredEvent.SPACE_PRESSED_EVENT)

    def handle_events(self) -> None:
        for event in pygame.event.get():
            self.handle_event(event)

    def update_blocks(self) -> None:
        for block in self.blocks:
            if not block.owner:
                block.update_all()

    def draw(self, drawable: pygame.Surface, drawable_transparent: pygame.Surface) -> None:
        for block in reversed(self.depth_sorted_blocks):
            if block.owner:
                continue

            block.draw_for_app(drawable,
                               drawable_transparent,
                               block is self.selected_block,
                               block is self.dragged_block)

    def register_event_handler(self, event_name: constants.TriggeredEvent, event_handler_brick: 'EventBrick') -> None:
        self.event_handlers[event_name].append(event_handler_brick)

    def execute_bricks(self) -> None:
        if self.executing_bricks:
            try:
                executable = self.executing_bricks[0]
                executable_next = executable.execute()
                self.executing_bricks = executable_next + self.executing_bricks[1:]

            except scratch_exceptions.ScratchRuntimeException as e:
                print('Error', str(e))
                self.executing_bricks = []

    def execute_triggered_events(self) -> None:
        if self.executing_bricks:
            return

        for event_name in self.triggered_events:
            for event_brick in self.event_handlers[event_name]:
                self.executing_bricks.append(event_brick)

        self.triggered_events = []

    def spawn_n_times(self, constructor, n, x, y, dx=5, dy=15):
        for i in range(n):
            self.blocks.append(constructor(self, x + dx * i, y + dy * i))

    def run(self) -> None:

        # for i in range(7):
        #     self.blocks.append(PressSPACEEventBrick(self, 0, i * 30))
        #     self.blocks.append(ConditionBrick(self, 100, i * 30))
        #     self.blocks.append(WhileBrick(self, 200, i * 30))
        #     self.blocks.append(PrintBrick(self, 300, i * 30))
        #     self.blocks.append(AssignIntBrick(self, 400, i * 30))
        #     self.blocks.append(IntPlusIntBlock(self, 500, i * 30))
        #     self.blocks.append(IntSubIntBlock(self, 600, i * 30))
        #     self.blocks.append(IntMultiplyIntBlock(self, 700, i * 30))
        #     self.blocks.append(IntDivIntBlock(self, 800, i * 30))
        #     self.blocks.append(IntModIntBlock(self, 900, i * 30))
        #     self.blocks.append(IntGreaterEqualIntBlock(self, 1000, i * 30))
        #     self.blocks.append(IntLessIntBlock(self, 1100, i * 30))
        #     self.blocks.append(IntGreaterIntBlock(self, 1200, i * 30))

        # for i in range(48):
        #    self.blocks.append(NumberBlock(self, i * 20, 200))
        #    self.blocks.append(VariableNameBlock(self, i * 20, 250))

        self.spawn_n_times(IntPlusIntBlock, 3, 100, 250)
        self.spawn_n_times(PressSPACEEventBrick, 1, 0, 0)
        self.spawn_n_times(NumberBlock, 19, 0, 90, 4, 7)
        self.spawn_n_times(VariableNameBlock, 7, 50, 90)
        self.spawn_n_times(IntModIntBlock, 1, 100, 90)
        self.spawn_n_times(IntLessIntBlock, 2, 150, 150)
        self.spawn_n_times(AssignIntBrick, 7, 200, 210)
        self.spawn_n_times(IntPlusIntBlock, 2, 100, 250)
        self.spawn_n_times(PrintBrick, 1, 0, 370)
        self.spawn_n_times(WhileBrick, 2, 0, 450)
        self.spawn_n_times(ConditionWithoutElseBrick, 2, 130, 450)
        self.spawn_n_times(IntEqualIntBlock, 2, 130, 350)

        screen = pygame.display.set_mode((self.width, self.height))
        drawable = pygame.Surface((self.width, self.height), pygame.SRCALPHA, 32)
        drawable_transparent = pygame.Surface((self.width, self.height), pygame.SRCALPHA, 32)

        try:
            clock = pygame.time.Clock()

            while True:
                self.handle_events()
                self.update_blocks()

                self.execute_triggered_events()
                self.execute_bricks()

                screen.fill(constants.BACKGROUND_COLOR)
                drawable.fill(constants.BACKGROUND_COLOR)

                self.draw(drawable, drawable_transparent)
                screen.blit(drawable, (0, 0))
                pygame.display.update()

                clock.tick(self.fps)
                pygame.display.set_caption('FPS: %d' % clock.get_fps())

        except self.QuitException:
            pass

        finally:
            pygame.display.quit()


class ReturnsValue:

    def calculate(self) -> Any:
        raise NotImplementedError


class ReturnsBool(ReturnsValue):

    def calculate(self) -> bool:
        raise NotImplementedError


class ReturnsString(ReturnsValue):

    def calculate(self) -> str:
        raise NotImplementedError


class ReturnsInt(ReturnsValue):

    def calculate(self) -> int:
        raise NotImplementedError


class OnlyBoolBlockSpot(BlockSpot):

    def check_other_insert_conditions(self, block: Block) -> bool:
        return isinstance(block, ReturnsBool)


class OnlyStringBlockSpot(BlockSpot):

    def check_other_insert_conditions(self, block: Block) -> bool:
        return isinstance(block, ReturnsString)


class OnlyVariableNameBlockSpot(BlockSpot):

    def check_other_insert_conditions(self, block: Block) -> bool:
        return isinstance(block, VariableNameBlock)


class OnlyIntBlockSpot(BlockSpot):

    def check_other_insert_conditions(self, block: Block) -> bool:
        return isinstance(block, ReturnsInt)


class NumberBlock(Block, ReturnsInt):

    def __init__(self, app: 'App', x: int, y: int):
        super().__init__(app, x, y, 20, 20)

        self.text: str = ''

    def draw(self, surface: pygame.Surface, is_selected: bool) -> None:
        super().draw(surface, is_selected)

        text_surface = self.app.default_in_block_font.render(self.text, True, (0, 0, 0))
        surface.blit(text_surface, (self.x + 5, self.y + 5))

    def update_size(self) -> None:
        text_surface = self.app.default_in_block_font.render(self.text, True, (0, 0, 0))
        self.width = 10 + text_surface.get_width()
        self.height = 10 + text_surface.get_height()

    def keyboard_press(self, key: int) -> None:
        self.text = useful.apply_key(self.text, key)

    def calculate(self) -> int:
        if useful.represents_integer(self.text):
            return int(self.text)

        return self.app.variable_scope.get_variable(self.text)


class VariableNameBlock(Block, ReturnsString):

    def __init__(self, app: 'App', x: int, y: int):
        super().__init__(app, x, y, 20, 20)

        self.text: str = ''

    def draw(self, surface: pygame.Surface, is_selected: bool) -> None:
        super().draw(surface, is_selected)
        pygame.draw.rect(surface, (90, 200, 90), (self.x, self.y, self.width, self.height), 1)

        text_surface = self.app.default_in_block_font.render(self.text, True, (0, 0, 0))
        surface.blit(text_surface, (self.x + 5, self.y + 5))

    def update_size(self) -> None:
        text_surface = self.app.default_in_block_font.render(self.text, True, (0, 0, 0))
        self.width = 10 + text_surface.get_width()
        self.height = 10 + text_surface.get_height()

    def keyboard_press(self, key: int) -> None:
        self.text = useful.apply_key(self.text, key)

    def calculate(self) -> str:
        if useful.represents_variable_name(self.text):
            return self.text

        raise scratch_exceptions.InvalidVariableNameException(self.text)


class BinaryIntOperation(GridBlock, ReturnsInt):

    def __init__(self, app: 'App', x: int, y: int, op_text: str, op_function: Callable[[int, int], int]):
        super().__init__(app, x, y,
                         [{'instance': OnlyIntBlockSpot(app, self, 0, 0, 30, 30),
                           'name'    : 'left_spot',
                           'row'     : 0,
                           'column'  : 0},
                          {'instance': TextBlock(app, 0, 0, op_text),
                           'name'    : 'text_block',
                           'row'     : 0,
                           'column'  : 1},
                          {'instance': OnlyIntBlockSpot(app, self, 0, 0, 30, 30),
                           'name'    : 'right_spot',
                           'row'     : 0,
                           'column'  : 2}])

        self.op_function = op_function

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


class IntModIntBlock(BinaryIntOperation):

    def __init__(self, app: 'App', x: int, y: int):
        super().__init__(app, x, y, '%', lambda a, b: a % b)


class IntCompareOperation(GridBlock, ReturnsBool):

    def __init__(self, app: 'App', x: int, y: int, op_text: str, op_function: Callable[[int, int], bool]):
        super().__init__(app, x, y,
                         [{'instance': OnlyIntBlockSpot(app, self, 0, 0, 30, 30),
                           'name'    : 'left_spot',
                           'row'     : 0,
                           'column'  : 0},
                          {'instance': TextBlock(app, 0, 0, op_text),
                           'name'    : 'text_block',
                           'row'     : 0,
                           'column'  : 1},
                          {'instance': OnlyIntBlockSpot(app, self, 0, 0, 30, 30),
                           'name'    : 'right_spot',
                           'row'     : 0,
                           'column'  : 2}])

        self.op_function = op_function

    def calculate(self) -> bool:
        if self.left_spot.inner and self.right_spot.inner:
            return self.op_function(self.left_spot.inner.calculate(), self.right_spot.inner.calculate())

        raise scratch_exceptions.EmptyArgumentException


class IntGreaterIntBlock(IntCompareOperation):

    def __init__(self, app: 'App', x: int, y: int):
        super().__init__(app, x, y, '>', lambda a, b: a > b)


class IntLessIntBlock(IntCompareOperation):

    def __init__(self, app: 'App', x: int, y: int):
        super().__init__(app, x, y, '<', lambda a, b: a < b)


class IntEqualIntBlock(IntCompareOperation):

    def __init__(self, app: 'App', x: int, y: int):
        super().__init__(app, x, y, '=', lambda a, b: a == b)


class IntGreaterEqualIntBlock(IntCompareOperation):

    def __init__(self, app: 'App', x: int, y: int):
        super().__init__(app, x, y, '≥', lambda a, b: a >= b)


class IntLessEqualIntBlock(IntCompareOperation):

    def __init__(self, app: 'App', x: int, y: int):
        super().__init__(app, x, y, '≤', lambda a, b: a <= b)


class IntNotEqualIntBlock(IntCompareOperation):

    def __init__(self, app: 'App', x: int, y: int):
        super().__init__(app, x, y, '≠', lambda a, b: a != b)


class Brick(Block):

    def __init__(self, app: App, x: int, y: int, width: int, height: int):
        super().__init__(app, x, y, width, height)

    def execute(self) -> List['Brick']:
        raise NotImplementedError


class OnlyBrickSpot(BlockSpot):

    def check_other_insert_conditions(self, block: Block) -> bool:
        return isinstance(block, Brick) and not isinstance(block, EventBrick)


class EventBrick(Brick):

    def __init__(self, app: App, x: int, y: int, width: int, height: int,
                 event_name: constants.TriggeredEvent, displayed_event_name: str):
        super().__init__(app, x, y, width, height)

        app.register_event_handler(event_name, self)

        self.next_spot = OnlyBrickSpot(app, self, 0, 0,
                                       constants.EMPTY_BRICK_SLOT_WIDTH, constants.EMPTY_BRICK_SLOT_HEIGHT)
        self.text_surface = self.app.default_in_block_font.render(displayed_event_name, True, (0, 0, 0))

    def is_recursive_contain_block_spot(self, block_spot: 'BlockSpot'):
        return self.next_spot.is_recursive_contain_block_spot(block_spot)

    def calculate_full_content_rect(self) -> None:
        self.full_content_rect = ExpandingRect(self.x, self.y, self.width, self.height)\
            .expanded_with(self.next_spot.full_content_rect)

    def update_depth(self):
        super().update_depth()
        self.next_spot.update_depth()

    def draw(self, surface: pygame.Surface, is_selected: bool):
        super().draw(surface, is_selected)

        if is_selected:
            pygame.draw.rect(surface, (255, 255, 255), (self.x, self.y, self.width, self.height), 3)

        self.next_spot.draw(surface, False)

        location = self.text_surface.get_rect(center=self.center)
        surface.blit(self.text_surface, location)

    def update_size(self) -> None:
        self.next_spot.update_size()

        self.width = self.text_surface.get_width() + 20
        self.height = self.text_surface.get_height() + 10

        self.next_spot.update_location(self.x, self.bottom)

    def execute(self) -> List['Brick']:
        if self.next_spot.inner:
            return [self.next_spot.inner]

        return []


class PressSPACEEventBrick(EventBrick):

    def __init__(self, app: App, x: int, y: int):
        super().__init__(app, x, y, 200, 50, constants.TriggeredEvent.SPACE_PRESSED_EVENT, 'Press SPACE to execute')


class GridBrick(GridBlock, Brick):

    def __init__(self, app: 'App', x: int, y: int, content: List[Dict[str, Any]], have_next: bool = True):
        super().__init__(app, x, y, content)

        self.next_spot: Optional[OnlyBrickSpot] = None
        if have_next:
            self.next_spot = OnlyBrickSpot(app, self, x, y,
                                           constants.EMPTY_BRICK_SLOT_WIDTH, constants.EMPTY_BRICK_SLOT_HEIGHT)

    def update_depth(self):
        super().update_depth()
        if self.next_spot:
            self.next_spot.update_depth()

    def calculate_full_content_rect(self) -> None:
        super().calculate_full_content_rect()

        if self.next_spot:
            self.full_content_rect = self.full_content_rect.expanded_with(self.next_spot)

    def draw(self, surface: pygame.Surface, is_selected: bool) -> None:
        super().draw(surface, is_selected)
        if self.next_spot:
            self.next_spot.draw(surface, False)

    def calculate_content(self):
        super().calculate_content()
        if self.next_spot:
            self.next_spot.update_location(self.x, self.bottom)
            self.next_spot.update_all()

    def is_recursive_contain_block_spot(self, block_spot: 'BlockSpot') -> bool:
        return super().is_recursive_contain_block_spot(block_spot) \
               or self.next_spot.is_recursive_contain_block_spot(block_spot)

    def execute(self) -> List['Brick']:
        raise NotImplementedError


class PrintBrick(GridBrick):

    def __init__(self, app: 'App', x: int, y: int):
        super().__init__(app, x, y,
                         [{'instance': TextBlock(app, 0, 0, 'Print'),
                           'row'     : 0,
                           'column'  : 0},
                          {'instance': OnlyIntBlockSpot(app, self, 0, 0, 40, 20),
                           'name'    : 'spot',
                           'row'     : 0,
                           'column'  : 1}])

    def execute(self) -> List['Brick']:
        if self.spot.inner:
            result = self.spot.inner.calculate()
            print('PRINT: {}'.format(result))

        else:
            raise scratch_exceptions.EmptyArgumentException

        if self.next_spot.inner:
            return [self.next_spot.inner]

        return []


class ConditionBrick(GridBrick):

    def __init__(self, app: 'App', x: int, y: int):
        super().__init__(app, x, y,
                         [{'instance': TextBlock(app, 0, 0, 'if'),
                           'row'     : 0,
                           'column'  : 0},
                          {'instance': OnlyBoolBlockSpot(app, self, 0, 0, 40, 20),
                           'name'    : 'condition_spot',
                           'row'     : 0,
                           'column'  : 1},
                          {'instance': TextBlock(app, 0, 0, 'then'),
                           'row'     : 1,
                           'column'  : 0},
                          {'instance': OnlyBrickSpot(app, self, 0, 0, 40, 20),
                           'name'    : 'true_spot',
                           'row'     : 1,
                           'column'  : 1},
                          {'instance': TextBlock(app, 0, 0, 'else'),
                           'row'     : 2,
                           'column'  : 0},
                          {'instance': OnlyBrickSpot(app, self, 0, 0, 40, 20),
                           'name'    : 'false_spot',
                           'row'     : 2,
                           'column'  : 1}])

    def execute(self) -> List['Brick']:
        if not self.condition_spot.inner:
            raise scratch_exceptions.EmptyArgumentException

        condition_result: bool = self.condition_spot.inner.calculate()
        next_bricks = []

        if condition_result:
            if self.true_spot.inner:
                next_bricks.append(self.true_spot.inner)
            else:
                raise scratch_exceptions.EmptyArgumentException

        else:
            if self.false_spot.inner:
                next_bricks.append(self.false_spot.inner)
            else:
                raise scratch_exceptions.EmptyArgumentException

        if self.next_spot.inner:
            next_bricks.append(self.next_spot.inner)

        return next_bricks


class ConditionWithoutElseBrick(GridBrick):

    def __init__(self, app: 'App', x: int, y: int):
        super().__init__(app, x, y,
                         [{'instance': TextBlock(app, 0, 0, 'if'),
                           'row'     : 0,
                           'column'  : 0},
                          {'instance': OnlyBoolBlockSpot(app, self, 0, 0, 40, 20),
                           'name'    : 'condition_spot',
                           'row'     : 0,
                           'column'  : 1},
                          {'instance': TextBlock(app, 0, 0, 'then'),
                           'row'     : 1,
                           'column'  : 0},
                          {'instance': OnlyBrickSpot(app, self, 0, 0, 40, 20),
                           'name'    : 'true_spot',
                           'row'     : 1,
                           'column'  : 1}])

    def execute(self) -> List['Brick']:
        if not self.condition_spot.inner:
            raise scratch_exceptions.EmptyArgumentException

        condition_result: bool = self.condition_spot.inner.calculate()
        next_bricks = []

        if condition_result:
            if self.true_spot.inner:
                next_bricks.append(self.true_spot.inner)
            else:
                raise scratch_exceptions.EmptyArgumentException

        if self.next_spot.inner:
            next_bricks.append(self.next_spot.inner)

        return next_bricks


class WhileBrick(GridBrick):

    def __init__(self, app: 'App', x: int, y: int):
        super().__init__(app, x, y,
                         [{'instance': TextBlock(app, 0, 0, 'while'),
                           'row'     : 0,
                           'column'  : 0},
                          {'instance': OnlyBoolBlockSpot(app, self, 0, 0, 40, 20),
                           'name'    : 'condition_spot',
                           'row'     : 0,
                           'column'  : 1},
                          {'instance'  : OnlyBrickSpot(app, self, 0, 0, 40, 20),
                           'name'      : 'true_spot',
                           'row'       : 1,
                           'column'    : 0,
                           'columnspan': 2}])

    def execute(self) -> List['Brick']:
        if not self.condition_spot.inner:
            raise scratch_exceptions.EmptyArgumentException

        condition_result: bool = self.condition_spot.inner.calculate()

        if condition_result:
            if self.true_spot.inner:
                return [self.true_spot.inner, self]
            else:
                raise scratch_exceptions.EmptyArgumentException

        if self.next_spot.inner:
            return [self.next_spot.inner]

        return []


class AssignIntBrick(GridBrick):

    def __init__(self, app: 'App', x: int, y: int):
        super().__init__(app, x, y,
                         [{'instance': OnlyVariableNameBlockSpot(app, self, 0, 0, 40, 20),
                           'name': 'variable_spot', 'row': 0, 'column': 0},
                          {'instance': TextBlock(app, 0, 0, ':='),
                           'row': 0, 'column': 1},
                          {'instance': OnlyIntBlockSpot(app, self, 0, 0, 40, 20),
                           'name': 'int_spot', 'row': 0, 'column': 2}])

    def execute(self) -> List['Brick']:
        if self.variable_spot.inner:
            var_name = self.variable_spot.inner.calculate()
        else:
            raise scratch_exceptions.EmptyArgumentException

        if self.int_spot.inner:
            value = self.int_spot.inner.calculate()
        else:
            raise scratch_exceptions.EmptyArgumentException

        self.app.variable_scope.set_variable(var_name, value)

        if self.next_spot.inner:
            return [self.next_spot.inner]

        return []
