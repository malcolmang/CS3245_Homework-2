#!/usr/bin/python3
import math
import os
import re
import nltk
import shutil
import sys
import getopt
import pickle

import linecache

from nltk.tokenize import word_tokenize
from nltk.tokenize import sent_tokenize
from nltk.stem import PorterStemmer
from InputBuffer import InputBuffer
from OutputBuffer import OutputBuffer
from SkipLinkedList import SkipLinkedList

ps = PorterStemmer()

def usage():
    print("usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file")


def normalize_word(word, ps):
    return ps.stem(word).lower()

def tokenize(document, ps):
    '''
    generates a list of tokens
    '''
    wordlist = set()
    for sentence in sent_tokenize(document):
        for word in word_tokenize(sentence):
            wordlist.add(normalize_word(word, ps))
    return wordlist

def ensure_directory_exists(directory):
    '''
    creates directory if it doesn't already exist
    '''
    if not os.path.exists(directory):
        os.makedirs(directory)


def get_write_index(directory):
    '''
    finds the next number in a sequence of files for writing a new file
    assumes all files in a directory are sequential and integers
    '''
    current_index = 0
    if len(os.listdir(directory)) != 0:
        latest_file = sorted(os.listdir(directory), reverse=True, key=int)[0]
        current_index = int(latest_file) + 1
    return current_index


def write_to_disk(posting):
    directory = "temp"
    ensure_directory_exists(directory)
    with open(directory + os.sep + str(get_write_index(directory)), 'x') as f:
        for term, doc_id_list in posting.items():
            doc_ids = SkipLinkedList(" ".join([str(i) for i in doc_id_list]))
            doc_ids.update_skip_pointers()
            f.write(f"{term} {doc_ids}\n")

def flush_memory(posting):
    write_to_disk(dict(sorted(posting.items())))
    posting.clear()


def memory_limit_reached(term, posting, document_id, memory_limit):
    posting_size = sys.getsizeof(posting)
    term_size = sys.getsizeof(term)
    document_id_size = sys.getsizeof(document_id)
    if posting_size + term_size + document_id_size > memory_limit:
        return True
    return False


def process_document(filename, posting, memory_limit, document_id, ps):
    with open(filename) as f:
        wordlist = tokenize(f.read(), ps)
        for term in wordlist:
            if memory_limit_reached(term, posting, document_id, memory_limit):
                flush_memory(posting)

            if term not in posting:
                posting[term] = []
            if document_id not in posting[term]:
                posting[term].append(document_id)


def get_lines(file_path, start, number_of_lines):
    '''
    gets the n number of lines from a starting point and converts each line into a tuple of (term, doc_ids)
    '''
    postings = []
    for i in range(start, start + number_of_lines):
        line = linecache.getline(file_path, i)
        if not line:
            break
        term, doc_ids = line.strip().split(" ", 1)
        postings.append((term, SkipLinkedList(doc_ids)))
    return postings

def print_progress(progress, total_iterations):
    print_interval = total_iterations // 100
    if print_interval != 0 and progress % print_interval == 0:
        progress_percent = (progress / total_iterations) * 100
        print(f'Progress: {progress_percent:.1f}%', end='\r')


def select_minimum_posting(inputs):
    valid_inputs = []
    for input in inputs:
        term = input.peek_next_term()
        if term is not None:
            valid_inputs.append((term, input))

    if not valid_inputs:
        return None

    # find the index of the minimum term in the list of valid terms/inputs
    minimum_index = min(range(len(valid_inputs)), key=lambda i: valid_inputs[i][0])

    _, selected_input = valid_inputs[minimum_index]
    return selected_input.pop_next_posting()


def n_way_merge(files, next_directory):
    memory_limit = 500000
    ensure_directory_exists(next_directory)
    temp_path = os.path.join(next_directory, str(get_write_index(next_directory)))
    with open(temp_path, 'a+') as f:
        output = OutputBuffer(f, memory_limit)
        inputs = []
        for file in files:
            inputs.append(InputBuffer(open(file, 'r'), memory_limit))
        counter = 0
        while True:
            counter += 1
            if counter % 5000 == 0:
                print(f"{counter} terms sorted!", end='\r')
            if all(input.is_file_empty() for input in inputs):
                for input in inputs:
                    input.close()
                output.flush()
                break
            else:
                output.insert(select_minimum_posting(inputs))



def merge_postings(n, out_postings):
    '''
    do n-way recursive merge for temp files created into a single txt, as well as build a dictionary to wordcount and pointers
    returns dictionary (postings are not read but written to)
    '''
    current_directory = "temp"
    next_directory = os.path.join(current_directory, "temp")

    while len(os.listdir(current_directory)) > 1:
        dir = sorted(os.listdir(current_directory), key=int)
        ensure_directory_exists(next_directory)
        files = []
        for i, file in enumerate(dir):
            files.append(os.path.join(current_directory, file))
            if i % n == 0 and i != 0:
                n_way_merge(files, next_directory)
                files = []
        # take the leftover
        if files:
            n_way_merge(files, next_directory)
        current_directory = next_directory
        next_directory = os.path.join(current_directory, "temp")

    shutil.move(os.path.join(current_directory, "0"), "postings_temp")


def build_dictionary(out_postings, out_dict):
    '''
    build dictionary of term to (df, pointer) from completed posting list
    '''
    dictionary = {}
    position = 0
    all_items = set()
    postings_final = open(out_postings, 'w+')
    with open("postings_temp") as f:
        line = f.readline()
        while line:
            term, doc_ids = line.split(" ", 1)
            postings_final.write(doc_ids)
            doc_ids_list = doc_ids.split()
            all_items.update([int(doc_id.split("^")[0]) for doc_id in doc_ids_list])
            dictionary[term] = (len(doc_ids_list), position)
            position = postings_final.tell()
            line = f.readline()

    with open('full_list.txt', 'wb') as f:
        pickle.dump(sorted(all_items), f, protocol=pickle.HIGHEST_PROTOCOL)

    with open(out_dict, 'wb') as f:
        pickle.dump(dictionary, f, protocol=pickle.HIGHEST_PROTOCOL)
    postings_final.close()
    os.remove("postings_temp")



def build_index(in_dir, out_dict, out_postings):
    """
    build index from documents stored in the input directory,
    then output the dictionary file and postings file
    """
    print('indexing...')
    ps = PorterStemmer()
    memory_limit = 500000
    # sort once first so sorting posting list on insertion is not necessary
    dir = sorted(os.listdir(in_dir), key=int)
    posting = {}
    i = 0
    # clear temp
    if os.path.exists('temp'):
        shutil.rmtree('temp')
    for file in dir:
        i += 1
        if i % (len(dir) // 100) == 0:
            print(f"{round(i / len(dir) * 100)}% of files read", end='\r')
        filename = in_dir + os.sep + file
        process_document(filename, posting, memory_limit, int(file), ps)
    #Flush remaining postings to disk and get pointers
    flush_memory(posting)
    print("temp files created. merging:")
    merge_postings(3, out_postings)
    print("building dictionary:")
    build_dictionary(out_postings, out_dict)
    print(f"dictionary and postings file created at {out_dict} and {out_postings}.\n Indexing complete!")
    if os.path.exists('temp'):
        shutil.rmtree('temp')

input_directory = output_file_dictionary = output_file_postings = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-i': # input directory
        input_directory = a
    elif o == '-d': # dictionary file
        output_file_dictionary = a
    elif o == '-p': # postings file
        output_file_postings = a
    else:
        assert False, "unhandled option"

if input_directory == None or output_file_postings == None or output_file_dictionary == None:
    usage()
    sys.exit(2)

build_index(input_directory, output_file_dictionary, output_file_postings)
