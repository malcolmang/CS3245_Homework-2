import sys


class OutputBuffer:
    def __init__(self, file, buffer_size):
        self.buffer_size = buffer_size
        self.file_object = file
        self.buffer = []

    def insert(self, posting):
        """
        insert to buffer. writes buffer to disk and clears if full
        from assumption of sorted lists, inserted item can only be the same
        or larger than the last object in buffer
        """

        if self.buffer and self.buffer[-1][0] == posting[0]:
            self.buffer[-1] = (self.buffer[-1][0], self.buffer[-1][1].merge(posting[1]))
        else:
            self.buffer.append(posting)

        if sys.getsizeof(self.buffer) >= self.buffer_size:
            self.flush()

    def flush(self):
        """
        write contents of buffer to file
        """
        if self.buffer:
            strings = [f"{term} {doc_ids}\n" for term, doc_ids in self.buffer]
            self.file_object.writelines(strings)
            self.buffer.clear()

    def close(self):
        """
        flush and close file
        """
        self.flush()
        self.file_object.close()
