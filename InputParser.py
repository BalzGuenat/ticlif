from Command import Command


class InputParser:
    def __init__(self):
        self.queue = b''

    def push(self, key):
        self.queue += key

    def get(self):
        while len(self.queue) > 0:
            fst = self.queue[:1]
            if 32 <= fst[0] <= 126:
                yield fst.decode()
            if fst == b'\x03':
                raise KeyboardInterrupt
            if fst == b'\x1b':
                yield Command.BACK
            if fst == b'\r':
                yield Command.OK
            if fst == b'`':
                yield Command.SWITCH
            if fst == b'\t':
                yield Command.NEXT
            if fst == b'\x08':
                yield Command.DELETE_BEFORE
            if fst == b'\xe0':
                if len(self.queue) < 2:
                    return
                snd = self.queue[1:2]
                if snd == b'P':
                    yield Command.DOWN
                if snd == b'H':
                    yield Command.UP
                if snd == b'M':
                    yield Command.RIGHT
                if snd == b'K':
                    yield Command.LEFT
                if snd == b'S':
                    yield Command.DELETE
                self.queue = self.queue[2:]
                continue
            self.queue = self.queue[1:]
