#!/usr/bin/python3
import os
import pickle
import re
import nltk
import sys
import getopt

from Postings import Postings
from QueryParser import QueryParser
from SkipLinkedList import SkipLinkedList


def usage():
    print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")


def initialize(dict_path, postings_path, full_list_path):
    '''
    initializes dictionary and a file object for the postings file for seeking and reading from
    also initializes a full_list as a SkipLinkedList if it doesn't already exist
    '''
    with open(dict_path, 'rb') as f:
        dictionary = pickle.load(f)

    if os.path.exists(full_list_path):
        with open(full_list_path, 'rb') as f:
            full_list = SkipLinkedList(pickle.load(f))
    else:
        all_items = set()
        with open(postings_path) as f:
            line = f.readline()
            while line:
                term, doc_ids = line.split(" ", 1)
                all_items.update([int(doc_id.split("^")[0]) for doc_id in doc_ids.split()])
        full_list = sorted(all_items)

    postings = Postings(postings_path, dictionary)

    return postings, full_list


def run_search(dict_file, postings_file, queries_file, results_file):
    full_list_dir = "full_list.txt"
    postings, full_list = initialize(dict_file, postings_file, full_list_dir)
    query_parser = QueryParser(postings, full_list)
    with open(queries_file) as f, open(os.path.join(results_file), 'w+') as w:
        for line in f:
            w.write(f"{query_parser.resolve_query(line)}\n")

    print("Search complete!")



dictionary_file = postings_file = file_of_queries = output_file_of_results = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-d':
        dictionary_file  = a
    elif o == '-p':
        postings_file = a
    elif o == '-q':
        file_of_queries = a
    elif o == '-o':
        file_of_output = a
    else:
        assert False, "unhandled option"

if dictionary_file == None or postings_file == None or file_of_queries == None or file_of_output == None :
    usage()
    sys.exit(2)

run_search(dictionary_file, postings_file, file_of_queries, file_of_output)
