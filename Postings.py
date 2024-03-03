from SkipLinkedList import SkipLinkedList

class Postings:
    def __init__(self, file_dir, dictionary):
        '''
        initializes, making a file available for seeking
        '''
        self.file = open(file_dir)
        self.dictionary = dictionary

    def get_doc_ids(self, term):
        '''
        from a pointer, seek the line and convert it into a posting
        '''
        if term not in self.dictionary.keys():
            return None

    def word_in_postings(self, term):
        '''
        checks if a given term is in the postings
        '''
        return term in self.dictionary.keys()

    def get_df(self, term):
        '''
        retrieves the document frequency for a given term
        '''
        if self.word_in_postings(term):
            return self.dictionary[term][0]
        else:
            return 0

    def get_posting(self, term):
        '''
        retrieve the posting for a term
        returns an empty SkipLinkedList if term not found
        '''
        if not self.word_in_postings(term):
            return SkipLinkedList()
        else:
            pointer = self.dictionary[term][1]
            self.file.seek(pointer)
            return SkipLinkedList(self.file.readline())

    def close(self):
        self.file.close()