import re
import nltk

from SkipLinkedList import SkipLinkedList


class QueryParser:
    '''
    handles queries. stores postings and other relevant information to resolve queries
    '''
    def __init__(self, postings, full_list):
        '''
        initialises with postings and a full list
        '''
        self.operators = operators = ('AND', 'OR', 'NOT')
        self.postings = postings
        self.full_list = full_list
        self.ps = nltk.PorterStemmer()

    def is_invalid_query(self, query):
        '''
        checks if query is valid or not
        '''
        invalid_substrings = [
            'AND OR',
            'OR AND',
            'NOT AND',
            'NOT OR',
            'AND AND',
            'OR OR',
            'NOT NOT',
            '(OR',
            '(AND',
            '( OR',
            '( AND'
            'AND)',
            'OR)',
            'AND )',
            'OR )',
            'NOT)',
            'NOT )'
        ]

        for invalid_substring in invalid_substrings:
            if invalid_substring in query:
                return True

        # valid queries cannot start or end in AND or OR, but can begin with NOT
        for operator in ['AND', 'OR']:
            if query.strip().startswith(operator) or query.strip().endswith(operator):
                return True

        if query.strip().endswith('NOT'):
            return True
        return False

    def normalize_word(self, word):
        return self.ps.stem(word).lower()

    def tokenize_query(self, query):
        # splits queries based on operators
        wordlist = []
        if self.is_invalid_query(query):
            raise ValueError("Invalid Query")
        operators = ('AND', 'OR', 'NOT', '(', ')')
        regex_pattern = '|'.join(map(re.escape, operators))
        wordlist = re.split(f'({regex_pattern})', query)

        query_tokens = []
        for word in wordlist:
            word = word.strip()
            if word:
                if word in operators:
                    query_tokens.append(word)
                else:
                    query_tokens.append(self.normalize_word(word))
        return query_tokens

    def parse_query(self, query):
        '''
        converts query into RPN
        '''

        operator_stack = []
        output_queue = []
        operators = {'AND', 'OR', 'NOT', '(', ')'}
        precedence = {'NOT': 3, 'AND': 2, 'OR': 1}
        if self.is_invalid_query(query):
            raise ValueError("Invalid Query")
        tokens = self.tokenize_query(query)
        for token in tokens:
            if " " in token:
                raise ValueError("Invalid Query")

        # shunting yard
        for token in tokens:
            if token in {'AND', 'OR', 'NOT', '(', ')'}:
                if token == '(':
                    operator_stack.append(token)
                elif token == ')':
                    while operator_stack and operator_stack[-1] != '(':
                        output_queue.append(operator_stack.pop())
                    if not operator_stack or operator_stack[-1] != '(':
                        raise ValueError("Mismatched parentheses")
                    operator_stack.pop()
                else:
                    while (operator_stack and operator_stack[-1] != '(' and
                           precedence.get(token, 0) <= precedence.get(operator_stack[-1], 0)):
                        output_queue.append(operator_stack.pop())
                    operator_stack.append(token)
            else:
                output_queue.append(token)

        while operator_stack:
            if operator_stack[-1] == '(':
                raise ValueError("Mismatched parentheses")
            output_queue.append(operator_stack.pop())
        return output_queue

    def AND(self, list1, list2):
        return list1.AND(list2)

    def OR(self, list1, list2):
        return list1.OR(list2)

    def NOT(self, list):
        return self.full_list.NOT(list)



    def organize_query(self, query):
        '''
        converts each query into a tuple (df, query) for optimization
        '''
        term_df_query = []
        operators = ['AND', 'NOT', 'OR']
        for term in query:
            if term in operators:
                term_df_query.append(term)
            else:
                term_df_query.append((term, self.postings.get_df(term)))
        return term_df_query

    def capture_brackets(self, query):
        return re.findall(r'\((.*?)\)', query)

    def split_by_separator(self, list_to_split, sep, include_separator = False):
        '''
        splits a list of tuples into sublists via a separator (the separator can also be added back into list)
        '''
        sublists = []
        chunk = []
        for val in list_to_split:
            if val == sep:
                sublists.append(chunk)
                if include_separator:
                    sublists.append(sep)
                chunk = []
            else:
                chunk.append(val)
        sublists.append(chunk)
        return sublists

    def optimize_and_score_flat_query(self, query):
        ''' Given a list of tuples of (term, df) and operators,
        optimizes the AND statements and consolidates into a single big term with df score
        '''
        chunks = self.split_by_separator(query, 'OR')

        # chunks are guaranteed to have no OR operators
        # consolidate all NOT:
        NOT_consolidated_chunks = []
        for chunk in chunks:
            consolidated_chunk = []
            for index, token in enumerate(chunk):
                if index > 0 and chunk[index - 1] == 'NOT' and token != 'AND':
                    new_df = self.full_list.length - token[1]
                    consolidated_chunk.append((f'NOT {token[0]}', new_df))
                elif token != 'NOT' and token != 'AND':
                    consolidated_chunk.append(token)
            NOT_consolidated_chunks.append(consolidated_chunk)

        # terms between AND operators can freely move around
        # maximum df scored for chunk is the minimum of all AND operators
        consolidated_chunks = []
        for chunk in NOT_consolidated_chunks:
            df = min([token[1] for token in chunk])
            consolidated_chunks.append(
                (" AND ".join([str(tuple[0]) for tuple in sorted(chunk, key=lambda x: x[1])]), df))

        # df score is sum of all OR terms
        return f'({" OR ".join([token for token, df in consolidated_chunks])})', \
               min(self.full_list.length, sum([df for token, df in consolidated_chunks]))

    def replace_brackets(self, query, bracket_queries):
        '''
        replace the items between brackets in tokenized query with consolidated ones
        '''
        flat_query = []
        bracket_index = 0
        in_bracket = False
        for token in query:
            if token[0] == ')':
                in_bracket = False
                continue
            elif in_bracket:
                continue

            if token[0] == '(':
                flat_query.append(bracket_queries[bracket_index])
                bracket_index += 1
                in_bracket = True
            else:
                flat_query.append(token)
        return flat_query

    def optimize_query(self, query):
        '''
        infix optimization of AND terms assuming no nested brackets
        takes a string
        '''
        bracket_queries = []
        for subquery in self.capture_brackets(query):
            tokens = self.organize_query(self.tokenize_query(subquery))
            bracket_queries.append(self.optimize_and_score_flat_query(tokens))

        final_query = self.replace_brackets(self.organize_query(self.tokenize_query(query)), bracket_queries)
        return self.optimize_and_score_flat_query(final_query)[0][1:-1]

    def evaluate_query(self, query):
        operators = ['AND', 'NOT', 'OR']
        stack = []
        for term in query:
            if term not in operators:
                stack.append(self.postings.get_posting(term))
            else:
                # If token is operator, perform the operation on operands from the stack
                if term == 'NOT':
                    operand = stack.pop()
                    result = self.NOT(operand)
                else:
                    operand1 = stack.pop()
                    operand2 = stack.pop()
                    if term == 'AND':
                        result = self.AND(operand1, operand2)
                    elif term == 'OR':
                        result = self.OR(operand1, operand2)
                    else:
                        result = None
                # Push the result of the operation back onto the stack
                stack.append(result)
        return stack.pop()

    def resolve_query(self, query_string):
        try:
            optimized_query = self.optimize_query(query_string)
            postfix = self.parse_query(optimized_query)
        except ValueError:
            return SkipLinkedList()
        return self.evaluate_query(postfix).get_value_string()
