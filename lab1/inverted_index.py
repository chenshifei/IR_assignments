'''This module builds an inverted index from a text file,
and is capable of searching multiple terms inside that index'''

import sys
import argparse
import math

PARSER = argparse.ArgumentParser()
PARSER.add_argument('filename', help='the file name of the sorted index file.')
PARSER.add_argument('-s', '--stopword',
                    action='store_true',
                    help='''set the top 10 most frequent terms \\
                        as the stop words (which means to remove them).''')
PARSER.add_argument('-k', '--skippointer',
                    dest='enable_skip',
                    action='store_true',
                    help='Enable skip pointers.')
PARSER.add_argument('queries', nargs='*', help='query terms')

ARGS = None

class InvertedIndex():
    '''Class for the in-memory inverted index'''
    def __init__(self, enable_stop_words=False, filename=None):
        self._inverted_idx = {}
        self.enable_stop_words = enable_stop_words
        if filename:
            self._init_from_file(filename)

    def _init_from_file(self, filename):
        with open(filename, 'r') as source_file:
            for _, line in enumerate(source_file):
                term, docid = line.split()
                if not self._inverted_idx.get(term):
                    self._inverted_idx[term] = []
                self._inverted_idx[term].append(int(docid))

        if self.enable_stop_words:
            top10 = sorted(self._inverted_idx.items(), key=lambda d: len(d[1]), reverse=True)
            top10 = top10[:10]
            for item in top10:
                del self._inverted_idx[item[0]]

    def vocabulary(self):
        '''Returns the vocabulary list of the inverted index'''
        return self._inverted_idx.keys()

    def postings(self):
        '''Returns the postings list of the inverted index'''
        result = set()
        for postings in self._inverted_idx.values():
            for post in postings:
                result.add(post)
        return result

    def query(self, syntax):
        ''' Searchs the inverted index for some terms

        Args:
            syntax (str): A single term or multiple terms.
            Only conjunctive queries are supported with multiple terms.
            They should be conjected by the word "AND", e.g "school AND class".

        Returns:
            tuple (list, int): The result list and the number of comparisons made.
        '''
        terms = self._terms_from_syntax(syntax)
        if not terms or not self._inverted_idx.get(terms[0]):
            return ([], 0)

        result = list(self._inverted_idx[terms[0]])
        total_compare = 0
        for term in terms[1:]:
            if not self._inverted_idx.get(term):
                return ([], 0)

            result, num_compare = self._intersect(result, self._inverted_idx[term])
            result = sorted(result)
            total_compare += num_compare
        return (result, total_compare)

    def _intersect(self, p_1, p_2):
        '''Returns the intersection of two posting lists'''
        result = []
        num_compare = 0
        i = 0
        j = 0
        while i < len(p_1) and j < len(p_2):
            doc1 = p_1[i]
            doc2 = p_2[j]
            if doc1 == doc2:
                num_compare += 1
                result.append(doc1)
                i += 1
                j += 1
            elif doc1 < doc2:
                num_compare += 1
                # Seek skip pointers for the posting list p_1
                i_skip = self._skip(p_1, i)
                while i_skip != -1 and p_1[i_skip] <= doc2:
                    num_compare += 1
                    i = i_skip
                    i_skip = self._skip(p_1, i)
                # If there's no skip pointer or it's out of range, continue with next docId
                i += 1
            else:
                num_compare += 1
                # Seek skip pointers for the posting list p_2
                j_skip = self._skip(p_2, j)
                while j_skip != -1 and p_2[j_skip] <= doc1:
                    num_compare += 1
                    j = j_skip
                    j_skip = self._skip(p_1, j)
                # If there's no skip pointer or it's out of range, continue with next docId
                j += 1
        return (result, num_compare)

    @staticmethod
    def _skip(postings, i):
        '''A help method to check if the pointer(index) i has a skip pointer.
        If so, returns its skip pointer.

        Args:
            postings (list): The list that holds all the postings of a term.
                The skip step is determind by the square root of its length.
            i (int): the current index to a docId.

        Returns:
            int: Returns the next skip pointer(index), -1 if there is no skip pointer.
        '''
        if ARGS.enable_skip:
            step = int(math.sqrt(len(postings)))
            if i + step < len(postings):
                return i + step
        return -1

    @staticmethod
    def _terms_from_syntax(syntax):
        '''A help method to remove all the "AND" from the raw query syntax.'''
        return syntax[::2]

def is_valid_query_syntax(queries):
    ''' A method to check if the query syntax is valid.
    It should be an empty string, a single term, or N (N > 2) terms connected by the word "AND".
    '''
    if len(queries) < 2:
        return True
    if len(queries) == 2:
        return False

    for operator in queries[1::2]:
        if operator != 'AND':
            return False
    return True

if __name__ == "__main__":
    ARGS = PARSER.parse_args(sys.argv[1:])
    INDEX = InvertedIndex(ARGS.stopword, ARGS.filename)
    print('Total vocabulary: {}'.format(len(INDEX.vocabulary())))
    print('Total postings: {}'.format(len(INDEX.postings())))

    if ARGS.queries:
        QUERIES = ARGS.queries
        if not is_valid_query_syntax(QUERIES):
            print('Invalid syntax: {}'.format(' '.join(QUERIES)))
        else:
            QUERY_RESULT, TOTAL_COMPARE = INDEX.query(QUERIES)
            print('Query "{}" returned {} results after {} comparisons:\n{}'.format(
                ' '.join(QUERIES), len(QUERY_RESULT), TOTAL_COMPARE, QUERY_RESULT))
