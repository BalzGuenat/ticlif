import os
import time
import msvcrt
import shutil
from collections import deque

CLEAR_CMD = 'cls'


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


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __iter__(self):
        return iter((self.x, self.y))

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


terminal_size = Point(*shutil.get_terminal_size()) + -2


def flow_text(str: str, width: int) -> list:
    result = []
    for line in str.expandtabs(tabsize=2).splitlines():
        block_start = 0
        while block_start + width < len(line):
            result.append(line[block_start:block_start+width])
            block_start += width
        result.append(line[block_start:].ljust(width))
    return result


def clear():
    os.system(CLEAR_CMD)


def draw(elem, state):
    if 'frame' not in state.properties:
        state.properties['frame'] = 0
    state.properties['frame'] += 1
    clear()
    (w, h) = terminal_size

    elem.resize(w, h)
    s = ""
    for row in range(elem.cur_size.y):
        line = elem.get_content(row)
        if row == state.pos.y:
            line = line[:max(0, state.pos.x)] + "$" + line[state.pos.x + 1:]
        s += line + '\n'

    print(s)


def make_buf(state):
    s = ""
    if state.debug:
        s += str(state.debug) + "\n"
    s += "\n" * state.pos.y
    if state.pos.x > 0:
        s += " " * state.pos.x
    s += "#"
    return s


class State:
    pos = Point(0, 0)
    debug = None
    properties = {}


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
        self.content = lambda self: None
        self.children = []
        self.event_handler = None

    def resize(self, w, h):
        self.cur_size = Point(w, h)
        if len(self.children) > 0:
            if self.direction == 'vertical':
                space_left = h
                if self.separate:
                    space_left -= len(self.children) - 1
                child_size = Point(w, space_left // len(self.children))
                last_child_size = child_size + Point(0, space_left % len(self.children))
                self.children[-1].resize(*last_child_size)
            else:
                space_left = w
                if self.separate:
                    space_left -= len(self.children) - 1
                child_size = Point(space_left // len(self.children), h)
                last_child_size = child_size + Point(space_left % len(self.children), 0)
                self.children[-1].resize(*last_child_size)
            for child in self.children[:-1]:
                child.resize(*child_size)

    def action(self, event):
        if self.event_handler:
            self.event_handler(self, event)
        else:
            child = self.child_at(*event.pos)
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

    def child_at(self, x, y):
        """
        Returns the child at the specified coordinates
        which are relative to this element.
        Returns None if this element has no children or
        the given coordinates are used for border, separator, etc.
        :param x:
        :param y:
        :return:
        """
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
            return child

    def element_at(self, x, y):
        """
        Returns the deepest element at the specified coordinates
        which are relative to this element.
        The caller must ensure that this element contains the coordinates
        :param x: The x coordinate relative to this element
        :param y: The y coordinate relative to this element
        :return: The deepest element at the coordinate
        """
        child = self.child_at(x, y)
        if child:
            child_pos = self.pos_of_child(child)
            return child.element_at(x - child_pos.x, y - child_pos.y)
        else:
            return self


    def element_at_old(self, x, y):
        """
        Returns the deepest element at the specified coordinates
        which are relative to this element.
        The caller must ensure that this element contains the coordinates
        :param x: The x coordinate relative to this element
        :param y: The y coordinate relative to this element
        :return: The deepest element at the coordinate
        """
        if len(self.children) == 0:
            return self
        if self.direction == 'vertical':
            # find which child must write row
            start_of_child = 0
            for child in self.children:
                row_after_child = start_of_child + child.cur_size.y
                if y < row_after_child:
                    return child.element_at(x, y - start_of_child)
                if self.separate:
                    if y == row_after_child and child is not self.children[-1]:
                        return self
                    else:
                        start_of_child = row_after_child + 1
                else:
                    start_of_child = row_after_child
            return child.element_at(x, y - start_of_child + child.cur_size.y)
            # children_sum = 0
            # for child in self.children:
            #     if children_sum + child.cur_size.y >= y + 1:
            #         # end of child is after y
            #         break
            #     children_sum += child.cur_size.y
            # return child.element_at(x, y - (children_sum - child.cur_size.y))
        else:
            children_sum = 0
            for child in self.children:
                if children_sum + child.cur_size.x >= x + 1:
                    # end of child is after x
                    break
                children_sum += child.cur_size.x
                if self.separate:
                    children_sum += 1
            return child.element_at(x - (children_sum - child.cur_size.x), y)

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
        return self

    def with_content(self, content):
        self.content = content
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

        content_str = self.content()
        if content_str:
            start = row*self.cur_size.x
            end = (row+1)*self.cur_size.x
            if isinstance(content_str, list):
                content_str = "\n".join([str(c) for c in content_str])
            flown = flow_text(content_str, self.cur_size.x)
            return flown[row] if row < len(flown) else self.empty_row()
        return "?" * self.cur_size.x

    def empty_row(self):
        return " " * self.cur_size.x

    def with_border(self, border_char='#'):
        return Border(self, border_char)


class BorderedElement(Element):
    def __init__(self, border_char='#'):
        super(BorderedElement, self).__init__()
        self.border = border_char

    def resize(self, w, h):
        self.cur_size = Point(w, h)
        w -= 2
        h -= 2
        if len(self.children) > 0:
            if self.direction == 'vertical':
                child_size = Point(w, h // len(self.children))
            else:
                child_size = Point(w // len(self.children), h)
            for child in self.children:
                child.resize(*child_size)

    def get_content(self, row):
        if row == 0 or row == self.cur_size.y - 1:
            # first and last rows are border
            return self.border * self.cur_size.x
        row -= 1
        if len(self.children) != 0:
            if self.direction == 'vertical':
                # find which child must write row
                childern_sum = 0
                for child in self.children:
                    if childern_sum + child.cur_size.y >= row + 1:
                        # end of child is after current row
                        break
                    childern_sum += child.cur_size.y
                return self.border + child.get_content(row - childern_sum) + self.border
            else:
                s = self.border
                for child in self.children:
                    s += child.get_content(row)
                return s + self.border
        if self.content:
            start = row*(self.cur_size.x-2)
            end = (row+1)*(self.cur_size.x-2)
            return self.border + str(self.content)[start:end].ljust(self.cur_size.x - 2) + self.border
        return self.border + ("?" * (self.cur_size.x - 2)) + self.border


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

    def resize(self, w, h):
        self.cur_size = Point(w, h)
        self.children[0].resize(w-2, h-2)

    def get_content(self, row):
        if row == 0 or row == self.cur_size.y - 1:
            # first and last rows are border
            return self.border * self.cur_size.x
        else:
            return self.border + self.children[0].get_content(row - 1) + self.border


class Event:
    pos = None
    key = None


def inc(state):
    state.properties['counter'] += 1


def debug_info():
    return ['absolute cursor position: {}'.format(state.pos),
            'elem under cursor: {}'.format(root.element_at(*state.pos)),
            'first child under cursor: {}'.format(root.child_at(*state.pos)),
            'frame: {}'.format(state.properties['frame']),
            'debug: {}'.format(state.debug)]


def getch_timeout(timeout_millis: int = 500) -> bytes:
    start_time = time.perf_counter()
    while not (msvcrt.kbhit() or (time.perf_counter() - start_time) * 1000 > timeout_millis):
        time.sleep(0.001)
    if msvcrt.kbhit():
        return msvcrt.getch()
    else:
        return None


class TerminationRequestedException(Exception):
    pass


def process_user_input(state, user_input):
    state.debug.append(user_input)

    if user_input == b'\x03':
        raise KeyboardInterrupt
    if user_input in [b'\000', b'\xe0']:
        pass

    if user_input in [b'r', b'M']:
        state.pos.x = min(terminal_size.x - 1, state.pos.x + 1)
    elif user_input in [b'l', b'K']:
        state.pos.x = max(0, state.pos.x - 1)
    elif user_input in [b'd', b'P']:
        state.pos.y = min(terminal_size.y - 1, state.pos.y + 1)
    elif user_input in [b'u', b'H']:
        state.pos.y = max(0, state.pos.y - 1)
    elif user_input == b'\r':
        event = Event()
        event.pos = state.pos
        event.key = user_input
        root.action(event)
    elif user_input == b'\x1b':
        raise TerminationRequestedException
    # else:
    #     print("exiting. input was: " + str(user_input))
    #     break


if __name__ == '__main__':
    # input("Press the return key to continue...")
    state = State()
    state.debug = DroppingList(10)
    state.properties['counter'] = 0

    root = (Element()
            .with_direction('horizontal')
            .with_child(Element().with_content(debug_info))
            .with_child(Element()
                        .with_child(Element().with_content(lambda: str(state.pos)))
                        .with_child(Element().with_content(lambda: str(root.pos_of_child(1))))
                        .with_child(Element()
                                    .with_content(lambda: "counter: {}".format(state.properties['counter']))
                                    .with_handler(lambda elem, event: inc(state)))
                        )
            )

    while True:
        draw(root, state)
        user_input = getch_timeout()
        if user_input:
            try:
                process_user_input(state, user_input)
            except TerminationRequestedException:
                break
