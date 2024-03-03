import sys

from SkipLinkedList import SkipLinkedList


class InputBuffer:
    def __init__(self, file, buffer_size):
        '''
        Makes an input buffer that refills itself when empty from the file object
        '''
        self.buffer_size = buffer_size
        self.file = file
        self.buffer = []
        self.eof = False  # Flag to indicate end of file
        self.fill_buffer()

    def fill_buffer(self):
        """
        Fill the buffer by reading lines from the file until the buffer is full or EOF is reached.
        """
        while sys.getsizeof(self.buffer) < self.buffer_size:
            line = self.file.readline()
            if not line:
                self.eof = True
                break
            self.buffer.append(line)

    def pop_next_posting(self):
        """
        get next posting from buffer, and refill if empty
        """
        term = None
        posting = None
        if not self.buffer:
            self.fill_buffer()
            if not self.eof:
                return None
        term, posting = self.buffer.pop(0).split(" ", 1)
        return term, SkipLinkedList(posting)

    def peek_next_term(self):
        if self.buffer:
            return self.buffer[0].split(" ", 1)[0]
        else:
            return None

    def is_file_empty(self):
        '''
        check if file is empty and refill if empty
        returns true if file is empty and buffer is empty
        '''
        if not self.buffer and not self.eof:
            self.fill_buffer()
        return not self.buffer and self.eof

    def close(self):
        '''
        close file
        '''
        self.file.close()
        self.file = None

