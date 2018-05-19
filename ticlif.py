import os
import sys
import time
import msvcrt
import shutil
from enum import Enum, unique, auto
from collections import deque, namedtuple

CLEAR_CMD = 'cls'
AUTO_REFRESH_INTERVAL = 0


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


class DroppingList:
    def __init__(self, capacity):
        self.capacity = capacity
        self.values = deque()

    def __str__(self):
        return str(self.values)

    def append(self, x):
        if len(self.values) == self.capacity:
            self.values.popleft()
        self.values.append(x)


_Point = namedtuple('Point', ['x', 'y'])


class Point(_Point):
    def __add__(self, other):
        if isinstance(other, Point):
            return Point(self.x + other.x, self.y + other.y)
        if isinstance(other, tuple) and len(other) == 2:
            return Point(self.x + other[0], self.y + other[1])
        elif isinstance(other, int):
            return Point(self.x + other, self.y + other)
        else:
            raise Exception("cannot add Point to {}".format(other))

    def __sub__(self, other):
        if isinstance(other, Point):
            return Point(self.x - other.x, self.y - other.y)
        if isinstance(other, tuple) and len(other) == 2:
            return Point(self.x - other[0], self.y - other[1])
        elif isinstance(other, int):
            return Point(self.x - other, self.y - other)
        else:
            raise Exception("cannot add Point to {}".format(other))

    def __str__(self):
        return '(' + str(self.x) + ',' + str(self.y) + ')'

    #     def __init__(self, x, y):
    #         self.x = x
    #         self.y = y
    #
    #     def __iter__(self):
    #         return iter((self.x, self.y))


def get_window_size() -> Point:
    w, h = shutil.get_terminal_size()
    return Point(w, h - 2)


def flow_text(text: str, width: int) -> list:
    result = []
    for line in text.expandtabs(tabsize=2).splitlines():
        block_start = 0
        while block_start + width < len(line):
            result.append(line[block_start:block_start + width])
            block_start += width
        result.append(line[block_start:].ljust(width))
    return result


def clear():
    os.system(CLEAR_CMD)


def do_draw(elem, state):
    if 'frame' not in state.properties:
        state.properties['frame'] = 0
    state.properties['frame'] += 1
    clear()
    (w, h) = get_window_size()

    s = ""
    for row in range(h):
        line = elem.get_content(row)
        if row == state.cursor.y:
            line = line[:max(0, state.cursor.x)] + "$" + line[state.cursor.x + 1:]
        s += line + '\n'

    print(s)


class State:
    def __init__(self):
        self._window_size = Point(0, 0)
        self.cursor = Point(0, 0)
        self.properties = {}

    @property
    def window_size(self):
        return self._window_size

    @window_size.setter
    def window_size(self, size: Point):
        # make sure cursor is inside new window
        self.cursor = Point._make(min(now, new) for now, new in zip(self.cursor, size - 1))
        self._window_size = size


class Controller:
    def __init__(self):
        self.state = State()
        # self.roots = set()
        self.last_roots = deque()
        # self._active_root = None

    @property
    def active_root(self):
        return self.last_roots[-1] if len(self.last_roots) > 0 else None

    @active_root.setter
    def active_root(self, root):
        try:
            self.last_roots.remove(root)
        except ValueError:
            pass
        self.last_roots.append(root)
        root.controller = self

    def add_root(self, root):
        if root not in self.last_roots:
            self.last_roots.appendleft(root)
        root.controller = self

    def remove_active(self):
        self.last_roots.pop()

    def remove_root(self, root):
        try:
            self.last_roots.remove(root)
        except ValueError:
            pass

    def switch_to_next_root(self):
        try:
            self.last_roots.appendleft(self.last_roots.pop())
        except IndexError:
            # happens if there are no roots
            pass

    def update(self):
        win_size = get_window_size()
        if win_size != self.state.window_size:
            self.state.window_size = win_size
            for root in self.last_roots:
                root.resize(win_size)
        for root in self.last_roots:
            root.update()

    def process_user_input(self, user_input):
        root = self.active_root
        state = self.state
        Debug.recent_inputs.append(user_input)

        if user_input == b'\x03':
            raise KeyboardInterrupt
        if user_input in [b'\000', b'\xe0']:
            pass

        if user_input in [b'r', b'M']:
            state.cursor = Point(min(get_window_size().x - 1, state.cursor.x + 1), state.cursor.y)
        elif user_input in [b'l', b'K']:
            state.cursor = Point(max(0, state.cursor.x - 1), state.cursor.y)
        elif user_input in [b'd', b'P']:
            state.cursor = Point(state.cursor.x, min(get_window_size().y - 1, state.cursor.y + 1))
        elif user_input in [b'u', b'H']:
            state.cursor = Point(state.cursor.x, max(0, state.cursor.y - 1))
        elif user_input == b'`':
            self.switch_to_next_root()
        elif user_input == b'\t':
            controller.move_cursor_to_next()
        elif user_input == b'\r':
            event = Event()
            event.pos = state.cursor
            event.key = user_input
            root.action(event)
        elif user_input == b'\x1b':
            raise TerminationRequestedException
        # else:
        #     print("exiting. input was: " + str(user_input))
        #     break

    def element_under_cursor(self):
        return self.active_root.element_at(self.state.cursor)

    def move_cursor_to_next(self):
        current = self.element_under_cursor()
        next = self.element_after(current)
        self.move_cursor_to(next)

    def element_after(self, elem):
        if elem is self.active_root:
            # roots have no next element
            return elem

        return elem.next_sibling or self.element_after(elem.parent)

    def move_cursor_to(self, elem):
        new_position = elem.absolute_position()
        self.state.cursor = new_position


class Element:
    def __init__(self):
        self.halign = 'left'
        self.valign = 'top'
        self.min_size = Point(0, 0)
        self.rel_pos = Point(0, 0)
        self.cur_size = Point(0, 0)
        self.direction = 'vertical'
        self.separator_char = None
        self.separate = True
        self.fetch_content = lambda self: ""
        self.content = None
        self.parent: Element = None
        self.__controller = None
        self.children = []
        self.event_handler = None
        self.id = None

    def __str__(self):
        return self.id or super(Element, self).__str__()

    @property
    def controller(self):
        return self.__controller or self.parent.controller

    @controller.setter
    def controller(self, controller):
        self.__controller = controller
        for child in self.children:
            child.controller = controller

    def update(self):
        self.content = self.fetch_content(self)
        self.update_children()

    def update_children(self):
        for child in self.children:
            child.update()

    def is_active_root(self):
        return self.parent is None

    def absolute_position(self) -> Point:
        if self.is_active_root() or self.parent is None:
            return Point(0, 0)

        return self.parent.absolute_position() + self.parent.pos_of_child(self)

    def next_element(self):
        """
        Returns the next element after this element.
        This element may decide the traversal order.
        :return: The next element after this or None if this is the last element.
        """
        return self.parent.next_child(self)

    @property
    def next_sibling(self):
        if self.parent is None:
            return None
        idx_of_next = self.parent.children.index(self) + 1
        if not idx_of_next < len(self.parent.children):
            return None
        return self.parent.children[idx_of_next]


    def next_child(self, child):
        """Returns the child after the specified child"""
        for i in range(len(self.children)):
            if self.children[i] is child:
                if i + 1 < len(self.children):
                    return self.children[i + 1]
                else:
                    return self.parent.next_child(self) if self.parent else None
        raise Exception("given child is not a child of this parent")

    def resize(self, size: Point):
        self.cur_size = size
        if len(self.children) > 0:
            if self.direction == 'vertical':
                space_left = size.y
                if self.separate:
                    space_left -= len(self.children) - 1
                child_size = Point(size.x, space_left // len(self.children))
                last_child_size = child_size + Point(0, space_left % len(self.children))
            else:
                space_left = size.x
                if self.separate:
                    space_left -= len(self.children) - 1
                child_size = Point(space_left // len(self.children), size.y)
                last_child_size = child_size + Point(space_left % len(self.children), 0)

            for child in self.children[:-1]:
                child.resize(child_size)
            self.children[-1].resize(last_child_size)

    def action(self, event):
        if self.event_handler:
            self.event_handler(self, event)
        else:
            child = self.child_at(event.pos)
            if child:
                event.pos -= self.pos_of_child(child)
                child.action(event)

    def separator(self):
        if self.separator_char:
            return self.separator_char
        elif self.direction == 'vertical':
            return '-'
        else:
            return '|'

    def child_at(self, pos: Point):
        """
        Returns the child at the specified coordinates
        which are relative to this element.
        Returns None if this element has no children or
        the given coordinates are used for border, separator, etc.
        :param pos:
        :return:
        """
        x, y = pos
        if x >= self.cur_size.x or y >= self.cur_size.y:
            raise Exception("Specified coordinates are outside of this element.")
        if len(self.children) == 0:
            return None
        if self.direction == 'vertical':
            # find which child must write row
            start_of_child = 0
            for child in self.children:
                row_after_child = start_of_child + child.cur_size.y
                if y < row_after_child:
                    return child
                if self.separate:
                    if y == row_after_child and child is not self.children[-1]:
                        return None
                    else:
                        start_of_child = row_after_child + 1
                else:
                    start_of_child = row_after_child
            return self.children[-1]
        else:
            children_sum = 0
            for child in self.children:
                if x < children_sum + child.cur_size.x:
                    return child
                if self.separate:
                    if x == children_sum + child.cur_size.x and child is not self.children[-1]:
                        return None
                    else:
                        children_sum += 1
                children_sum += child.cur_size.x
            return self.children[-1]

    def element_at(self, pos: Point):
        """
        Returns the deepest element at the specified position
        which are relative to this element.
        The caller must ensure that this element contains the position
        :param pos: The position relative to this element
        :return: The deepest element at the position
        """
        child = self.child_at(pos)
        if child:
            child_pos = self.pos_of_child(child)
            return child.element_at(pos - child_pos)
        else:
            return self

    def with_id(self, id_str: str):
        self.id = id_str
        return self

    def pos_of_child(self, child):
        """
        Get the position of the specified child relative to this element
        :param child: The child of which the position should be returned
        :return:
        """
        if isinstance(child, int):
            child = self.children[child]
        elif child not in self.children:
            raise Exception("Asked for position of an element that is not a child of this element")
        pos = 0
        for c in self.children:
            if c is child:
                if self.direction == 'vertical':
                    return Point(0, pos)
                else:
                    return Point(pos, 0)
            pos += c.cur_size.y if self.direction == 'vertical' else c.cur_size.x
            if self.separate:
                pos += 1

    def with_child(self, child):
        self.children.append(child)
        self.min_size += child.min_size
        child.parent = self
        return self

    def with_content(self, content, update: bool = False):
        """
        Sets the content of this element.
        :param content: Either the content itself or a function or other
        callable that takes no arguments and returns the content
        :param update: If True, self.update() will be called after setting the content
        :return: This element
        """
        if callable(content):
            self.fetch_content = content
        else:
            self.fetch_content = lambda _: content
        if update:
            self.update()
        return self

    def with_direction(self, direction):
        if direction.lower().strip() not in ['horizontal', 'vertical']:
            raise Exception
        self.direction = direction
        return self

    def with_handler(self, handler):
        self.event_handler = handler
        return self

    def get_content(self, row):
        """
        return the contents of the specified row as a string s.
        s must not contain newlines or tabs and len(s) must equal cur_size.x
        :param row: which row of content should be returned
        :return: the content of the row as a string as described
        """
        if len(self.children) > 0:
            if self.direction == 'vertical':
                # find which child must write row
                start_of_child = 0
                for child in self.children:
                    row_after_child = start_of_child + child.cur_size.y
                    if row < row_after_child:
                        return child.get_content(row - start_of_child)
                    if self.separate:
                        if row == row_after_child and child is not self.children[-1]:
                            return self.separator() * self.cur_size.x
                        else:
                            start_of_child = row_after_child + 1
                    else:
                        start_of_child = row_after_child
                return " " * self.cur_size.x
            else:
                joiner = self.separator() if self.separate else ""
                return joiner.join([child.get_content(row) for child in self.children])

        if not self.content:
            return "?" * self.cur_size.x

        if isinstance(self.content, list):
            content_str = "\n".join([str(c) for c in self.content])
        else:
            content_str = str(self.content)
        flown = flow_text(content_str, self.cur_size.x)
        return flown[row] if row < len(flown) else self.empty_row()

    def empty_row(self):
        return " " * self.cur_size.x

    def with_border(self, border_char='#'):
        return Border(self, border_char)


class Border(Element):
    """must always have exactly one child and no content"""

    def __init__(self, elem, border_char='#'):
        super(Border, self).__init__()
        self.children = [elem]
        self.border = border_char
        self.direction = elem.direction
        self.min_size = elem.min_size + 2
        self.halign = elem.halign
        self.valign = elem.valign

    def add_child(self, child):
        self.children[0].add_child(child)

    def set_child(self, child):
        self.children[0] = child

    def resize(self, w, h):
        self.cur_size = Point(w, h)
        self.children[0].resize(w - 2, h - 2)

    def get_content(self, row):
        if row == 0 or row == self.cur_size.y - 1:
            # first and last rows are border
            return self.border * self.cur_size.x
        else:
            return self.border + self.children[0].get_content(row - 1) + self.border


@unique
class EventKind(Enum):
    UNKNOWN = auto()
    USER_INPUT = auto()

    def _generate_next_value_(name, start, count, last_values):
        return name


class Event():
    def __init__(self, kind: EventKind = EventKind.UNKNOWN):
        self.kind = kind
        self.pos = None
        self.key = None

    def at_position(self, x, y):
        self.pos = Point(x, y)


class Debug:
    recent_inputs = DroppingList(10)


def debug_info(elem):
    root = controller.active_root
    state = controller.state
    if 'frame' not in state.properties:
        state.properties['frame'] = 0
    return ['this element: {}'.format(elem),
            'absolute cursor position: {}'.format(state.cursor),
            'elem under cursor: {}'.format(root.element_at(state.cursor)),
            'first child under cursor: {}'.format(root.child_at(state.cursor)),
            'frame: {}'.format(state.properties['frame']),
            'debug: {}'.format(Debug.recent_inputs)]


def getch(timeout_millis: int = 0) -> bytes:
    if timeout_millis <= 0:
        return msvcrt.getch()

    start_time = time.perf_counter()
    while not (msvcrt.kbhit() or (time.perf_counter() - start_time) * 1000 > timeout_millis):
        time.sleep(0.001)
    if msvcrt.kbhit():
        return msvcrt.getch()
    else:
        return None


class TerminationRequestedException(Exception):
    pass


controller = Controller()


def set_root(root):
    controller.active_root = root


def draw(root=None):
    if root:
        controller.active_root = root
    controller.update()
    root = controller.active_root
    do_draw(root, controller.state)


def loop(root=None):
    if root:
        controller.active_root = root
    while True:
        controller.update()
        root = controller.active_root
        do_draw(root, controller.state)
        user_input = getch(AUTO_REFRESH_INTERVAL)
        if user_input:
            try:
                controller.process_user_input(user_input)
            except TerminationRequestedException:
                break


def main():
    print("This is a library module not intended to be run directly.")
    print("Check out the README.md and example.py to learn how to use it.")


if __name__ == '__main__':
    main()
