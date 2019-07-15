"""
An improved program that plays Shannon's Game.

Author: Quinlan Meyerink 41818513 
Date: 19/1/18
"""

import re
import doctest
import time
import sys


DEFAULT_CORPUS = 'corpus.txt'


def _c_mul(num_a, num_b):
    '''Substitute for c multiply function'''
    return (int(num_a) * int(num_b)) & 0xFFFFFFFF


def nice_hash(input_string):
    """ Takes a string name and returns a hash for the string. This hash value
    will be os independent, unlike the default Python hash function.
    It will also be stable across runs of Python, unlike the default.
    """
    if input_string is None:
        return 0  # empty
    value = ord(input_string[0]) << 7
    for char in input_string:
        value = _c_mul(1000003, value) ^ ord(char)
    value = value ^ len(input_string)
    if value == -1:
        value = -2
    return value


class Frequency(object):
    """
    Stores a letter:frequency pair.
    The repr for printing will be of the form <item, frequency>
    See the example below
    >>> f = Frequency('c', 2)
    >>> f.letter
    'c'
    >>> f.frequency
    2
    >>> print(f)
    <'c': 2>
    """

    def __init__(self, letter, frequency):
        self.letter = letter
        self.frequency = frequency
        self.next = None

    def __repr__(self):
        return ('<' +
                repr(self.letter) + ': ' + str(self.frequency) +
                '>')


class SortedFrequencyList(object):
    """
    Stores a collection of Frequency objects as a sorted linked list.
    Items are sorted from the highest frequency to the lowest.
    """

    def __init__(self):
        self.head = None

    def move_node_to_place(self, freq_node):
        """Scans through the linked list and adds
        the freq_node into the correct place based on its frequency
        """
        freq_of_letter = freq_node.frequency  
        current = self.head
        added = False
            
        if freq_of_letter > self.head.frequency:
            freq_node.next = self.head
            self.head = freq_node
            added = True

        while current.next is not None and not added:
            if freq_of_letter > current.next.frequency:
                freq_node.next = current.next
                current.next = freq_node
                added = True
            else:
                current = current.next
        if not added:
            current.next = freq_node
                    
    def add(self, letter, frequency=1):
        """
        Adds the given letter and frequency combination as a Frequency object
        to the list. If the given letter is already in the list, the given
        frequency is added to its frequency.

        If the updated frequency is greater than the frequency of the previous
        node then it should be moved into order, ie, so that it is after
        all items with the same or greater frequency.

        >>> f = SortedFrequencyList()
        >>> f.add('a', 1)
        >>> f
        SFL(<'a': 1>)
        >>> f.add('b', 1)
        >>> f
        SFL(<'a': 1>, <'b': 1>)
        >>> f.add('c', 1)
        >>> f
        SFL(<'a': 1>, <'b': 1>, <'c': 1>)
        >>> f.add('d', 1)
        >>> f
        SFL(<'a': 1>, <'b': 1>, <'c': 1>, <'d': 1>)
        >>> f.add('d', 1)
        >>> f
        SFL(<'d': 2>, <'a': 1>, <'b': 1>, <'c': 1>)
        >>> f.add('c', 1)
        >>> f
        SFL(<'d': 2>, <'c': 2>, <'a': 1>, <'b': 1>)
        >>> f.add('d', 1)
        >>> f
        SFL(<'d': 3>, <'c': 2>, <'a': 1>, <'b': 1>)
        >>> f.add('a', 1)
        >>> f
        SFL(<'d': 3>, <'c': 2>, <'a': 2>, <'b': 1>)
        >>> f.add('b', 2)
        >>> f
        SFL(<'d': 3>, <'b': 3>, <'c': 2>, <'a': 2>)
        >>> f.add('a', 4)
        >>> f
        SFL(<'a': 6>, <'d': 3>, <'b': 3>, <'c': 2>)
        >>> f.add('r', 4)
        >>> f
        SFL(<'a': 6>, <'r': 4>, <'d': 3>, <'b': 3>, <'c': 2>)
        >>> f.add('t', 3)
        >>> f
        SFL(<'a': 6>, <'r': 4>, <'d': 3>, <'b': 3>, <'t': 3>, <'c': 2>)
        >>> f.add('z', 1)
        >>> f
        SFL(<'a': 6>, <'r': 4>, <'d': 3>, <'b': 3>, <'t': 3>, <'c': 2>, <'z': 1>)
        >>> t = SortedFrequencyList()
        >>> t.add('a', 4)
        >>> t.add('a', 2)
        >>> t.add('c', 2)
        >>> t.add('r', 1)
        >>> t.add('r')
        >>> t
        SFL(<'a': 6>, <'c': 2>, <'r': 2>)
        
        """
        current = self.head
        previous = self.head
        stop = False
        temp = Frequency(letter, frequency)
        
        while current is not None and not stop:
            if current.letter == letter:
                current.frequency += frequency                   
                if current.frequency > previous.frequency:
                    previous.next = current.next
                    self.move_node_to_place(current)
                stop = True
            else:
                previous = current
                current = current.next
                
        if stop is False:
            if previous is not None:
                if frequency > 1:
                    self.move_node_to_place(temp)
                else:
                    previous.next = temp
            else:
                self.head = temp      

    def remove(self, letter):
        """
        Removes the Frequency object with the given `letter` from the list.
        Does nothing if `letter` is not in the list.

        >>> f = SortedFrequencyList()
        >>> f.add('a', 3)
        >>> f.add('b', 2)
        >>> f.add('c', 1)
        >>> f
        SFL(<'a': 3>, <'b': 2>, <'c': 1>)
        >>> f.remove('b')
        >>> f
        SFL(<'a': 3>, <'c': 1>)
        >>> f.add('c', 5)
        >>> f.add('g', 2)
        >>> f
        SFL(<'c': 6>, <'a': 3>, <'g': 2>)
        >>> f.remove('c')
        >>> f.remove('g')
        >>> f
        SFL(<'a': 3>)
        >>> f.remove('a')
        >>> f.head is None
        True
        >>> f
        SFL()
        """
        if self.head.letter == letter:
            self.head = self.head.next
            return
        current_node = self.head
        previous_node = None
        while current_node != None:
            if current_node.letter == letter:
                previous_node.next = current_node.next
                return
            previous_node = current_node
            current_node = current_node.next      

    def find(self, letter):
        """
        Returns the Frequency object for the given `letter` in the list, or
        None if the `letter` doesn't appear in the list.
        
        >>> f = SortedFrequencyList()
        >>> f.add('a', 3)
        >>> f.find('a')
        <'a': 3>
        >>> print(f.find('b'))
        None
        >>> f.add('r', 4)
        >>> f.add('c', 2)
        >>> f.add('e', 4)
        >>> f.remove('r')
        >>> print(f.find('f'))
        None
        >>> f.find('e')
        <'e': 4>
        """

        current_node = self.head
        while current_node != None:
            if current_node.letter == letter:
                return current_node
            current_node = current_node.next
        return None        


    def __contains__(self, item):
        # you should use the find method here

        return self.find(item) is not None


    def __iter__(self):
        """ Returns a simple list of Frequency items
        eg, list(my_sorted_frequency_list)
        """
        current = self.head
        while current is not None:
            yield current.letter
            current = current.next

    def __repr__(self):
        """ Returns a string representation of the list, eg, SFL(<'e': 2>, <'d': 1>))
        """
        item_strs = []
        current = self.head
        while current is not None:
            item_strs.append(repr(current))
            current = current.next
        return 'SFL(' + ', '.join(item_strs) + ')'



class PrefixItem(object):
    """
    Stores a prefix:possibles pair.

    >>> p = PrefixItem('th', SortedFrequencyList())
    >>> p.possibles.add('e', 40)
    >>> p.possibles.add('o', 10)
    >>> p
    PfI('th': SFL(<'e': 40>, <'o': 10>))
    """

    def __init__(self, prefix, possibles):
        """
        Initialises a new PrefixItem with the given letter `prefix` and
        SortedFrequencyList of `possibles`.
        """
        self.prefix = prefix
        self.possibles = possibles

    def __hash__(self):
        return nice_hash(self.prefix)

    def __repr__(self):
        return 'PfI(' + repr(self.prefix) + ': ' + repr(self.possibles) + ')'


class PrefixTable(object):
    """
    A simple hash table for storing prefix:possible combinations using
    PrefixItems internally.
    """

    def __init__(self, slots):
        """
        Initialises the PrefixTable with a number of `slots`. The table cannot
        store more items than the number of slots specified here.
        """
        self.data = [None] * slots
        self.n_slots = slots
        self.n_items = 0

    def store(self, prefix, possibles):
        """
        Stores the given letter `prefix` and list of `possibles` (a
        SortedFrequencyList) in the hash table using a PrefixItem. If the
        item is successfully stored in the table, this method returns
        True, otherwise (for example, if there is no more room left in the
        table) it returns False.

        >>> p = PrefixTable(1)
        >>> p.store('th', SortedFrequencyList())
        True
        >>> p
        Prefix hash Table
        -----------------
            0: PfI('th': SFL())
        >>> p.store('ca', SortedFrequencyList())
        False
        >>> r = PrefixTable(5)
        >>> r.store('aa', SortedFrequencyList())
        True
        >>> r.store('ab', SortedFrequencyList())
        True
        >>> r.store('ac', SortedFrequencyList())
        True
        >>> r.store('ac', SortedFrequencyList())
        True
        >>> r.store('ad', SortedFrequencyList())
        True
        >>> r.store('ae', SortedFrequencyList())
        False
        >>> r.store('af', SortedFrequencyList())
        False
        
        """
        if self.n_slots == self.n_items:
            return False
        prefix_pair = PrefixItem(prefix, possibles)
        index = nice_hash(prefix) % self.n_slots
        while self.data[index] is not None:
            index += 1
            if index == self.n_slots:
                index = 0
        self.data[index] = prefix_pair
        self.n_items += 1
        return True

    def fetch(self, prefix):
        """"
        Returns the SortedFrequencyList of possibles associated with the given
        letter `prefix', or None if the `prefix` isn't stored in the table.

        >>> prefix = 'th'
        >>> possibles = SortedFrequencyList()
        >>> possibles.add('e', 40)
        >>> possibles.add('o', 10)
        >>> p = PrefixTable(1)
        >>> p.store(prefix, possibles)
        True
        >>> p.fetch('th')
        SFL(<'e': 40>, <'o': 10>)
        >>> print(p.fetch('ca'))
        None
        >>> prefix = 'aa'
        >>> possibles = SortedFrequencyList()
        >>> possibles.add('e', 20)
        >>> possibles.add('r', 10)
        >>> possibles.add('a', 15)
        >>> t = PrefixTable(5)
        >>> t.store(prefix, possibles)
        True
        >>> prefix = 'ab'
        >>> possibles = SortedFrequencyList()
        >>> possibles.add('r', 30)
        >>> possibles.add('w', 20)
        >>> t.store(prefix, possibles)
        True
        >>> t.fetch('ab')
        SFL(<'r': 30>, <'w': 20>)
        >>> print(t.fetch('rr'))
        None
        """

        index = nice_hash(prefix) % self.n_slots
        for _ in range(0, self.n_slots):
            table_pos = self.data[index]       
            if table_pos is None or table_pos.prefix != prefix:
                index += 1
                if index == self.n_slots:
                    index = 0                   
            else:
                return self.data[index].possibles
        return None


    def __contains__(self, prefix):
        """ Returns True if prefix is in the table, otherwise False"""

        return self.fetch(prefix) is not None


    def __repr__(self):
        ans = 'Prefix hash Table\n'
        ans += '-----------------'
        for i, item in enumerate(self.data):
            ans += '\n{:5}: {}'.format(i, repr(item))
        return ans



def process_corpus(corpus, unique_chars):
    """
    Returns a PrefixTable populated with the possible characters that follow
    each character pair in `corpus`. `unique_chars` is the number of unique
    characters in `corpus`.

    The size of the PrefixTable should be chosen by calculating the maximum
    number of character pairs (the square of `unique_chars`). In practice,
    the actual number of unique paris in the corpus will be considerably less
    than this, so we are guaranteed a low load factor.


    >>> process_corpus('lazy languid line', 11) #doctest: +ELLIPSIS
    Prefix hash Table
    -----------------
        0: None
       ...
       19: None
       20: PfI('ui': SFL(<'d': 1>))
       21: None
       ...
       41: None
       42: PfI('la': SFL(<'z': 1>, <'n': 1>))
       43: None
       44: PfI('an': SFL(<'g': 1>))
       45: None
       ...
       49: None
       50: PfI('li': SFL(<'n': 1>))
       51: None
       ...
       55: None
       56: PfI('az': SFL(<'y': 1>))
       57: PfI('y ': SFL(<'l': 1>))
       58: None
       59: None
       60: None
       61: PfI('ng': SFL(<'u': 1>))
       62: None
       63: None
       64: PfI('gu': SFL(<'i': 1>))
       65: None
       66: None
       67: None
       68: None
       69: PfI(' l': SFL(<'a': 1>, <'i': 1>))
       70: None
       ...
       93: None
       94: PfI('d ': SFL(<'l': 1>))
       95: None
       96: PfI('in': SFL(<'e': 1>))
       97: None
       98: None
       99: None
      100: None
      101: PfI('zy': SFL(<' ': 1>))
      102: PfI('id': SFL(<' ': 1>))
      103: None
      ...
      120: None
    >>> process_corpus('pitter patter', 7) #doctest: +ELLIPSIS
    Prefix hash Table
    -----------------
        0: None
        1: None
        2: None
        3: PfI('tt': SFL(<'e': 2>))
        4: None
       ...
       19: None
       20: PfI('te': SFL(<'r': 2>))
       21: None
       ...
       29: None
       30: PfI('er': SFL(<' ': 1>))
       31: None
       ...
       33: None
       34: PfI('pa': SFL(<'t': 1>))
       35: None
       ...
       37: None
       38: PfI(' p': SFL(<'a': 1>))
       39: PfI('it': SFL(<'t': 1>))
       40: PfI('r ': SFL(<'p': 1>))
       41: None
       42: PfI('pi': SFL(<'t': 1>))
       43: PfI('at': SFL(<'t': 1>))
       44: None
       ...
       48: None
    >>> process_corpus('riff raff', 5)  #doctest: +ELLIPSIS
    Prefix hash Table
    -----------------
        0: PfI(' r': SFL(<'a': 1>))
        1: None
        2: PfI('ra': SFL(<'f': 1>))
        3: None
        4: None
        5: None
        6: PfI('if': SFL(<'f': 1>))
        7: None
        8: None
        9: None
       10: PfI('ri': SFL(<'f': 1>))
       11: PfI('af': SFL(<'f': 1>))
       12: None
       13: None
       14: None
       15: None
       16: PfI('ff': SFL(<' ': 1>))
       17: None
       18: None
       19: None
       20: None
       21: PfI('f ': SFL(<'r': 1>))
       22: None
       23: None
       24: None
    >>> process_corpus('through tough thorough thought though', 7)
    Prefix hash Table
    -----------------
        0: None
        1: PfI('hr': SFL(<'o': 1>))
        2: PfI('or': SFL(<'o': 1>))
        3: None
        4: PfI('h ': SFL(<'t': 3>))
        5: None
        6: None
        7: PfI('ht': SFL(<' ': 1>))
        8: None
        9: None
       10: PfI('to': SFL(<'u': 1>))
       11: None
       12: None
       13: None
       14: PfI('ug': SFL(<'h': 5>))
       15: PfI('th': SFL(<'o': 3>, <'r': 1>))
       16: PfI('ho': SFL(<'u': 2>, <'r': 1>))
       17: None
       18: None
       19: PfI('gh': SFL(<' ': 3>, <'t': 1>))
       20: None
       21: None
       22: None
       23: None
       24: None
       25: None
       26: None
       27: None
       28: None
       29: None
       30: None
       31: PfI('ro': SFL(<'u': 2>))
       32: None
       33: None
       34: None
       35: None
       36: None
       37: None
       38: PfI('t ': SFL(<'t': 1>))
       39: None
       40: None
       41: None
       42: PfI(' t': SFL(<'h': 3>, <'o': 1>))
       43: None
       44: None
       45: None
       46: None
       47: PfI('ou': SFL(<'g': 5>))
       48: None
    
    """
    table = PrefixTable(unique_chars**2)
    for counter in range(0, len(corpus)-2):
        pair = corpus[counter] + corpus[counter+1]
        prefix_item = table.fetch(pair)
        new_char = corpus[counter+2]
        if prefix_item is None:
            possibles = SortedFrequencyList()
            possibles.add(new_char)
            table.store(pair, possibles)
        else:
            prefix_item.add(new_char)
            
    return table


""" def run_time_trials():
    """""" A good place to write code for time trials
    Make sure you use this docstring to explain your code and that
    you write comments in your code to help explain the process.
    """"""
    corpus_filename = 'le-rire.txt'
    with open(corpus_filename) as infile:
        print('Loading corpus... '+corpus_filename)
        full_corpus = format_document(infile.read())
        phrase = 'The big dog'
        phrase = 'Hello isn\'t it a lovely day today.'
        phrase = 'The quick brown fox jumps over the lazy dog'
        results = []
        start = 1000
        end = 240000
        step = 10000
        for i in range(start, end, step):
            slice_of_corpus = full_corpus[0:i]
            len_of_slice = len(slice_of_corpus)
            unique_chars = len(set(slice_of_corpus))
            table = process_corpus(slice_of_corpus, unique_chars)
            print(table)
            guesses, time_taken = play_game(table, phrase)   #autorun
            print('{} {}'.format(len_of_slice , time_taken))
            results.append((len_of_slice , guesses, time_taken))
            print('{:>10}\t{:>6}\t{:>12}'.format('size', 'guesses', 'time'))
            for size, guesses, time in results:
                print('{:10}\t{:6}\t{:12.8f}'.format(size, guesses, time))
                print()
                print('Full size = {}'.format(len(full_corpus)))

"""
    
def run_some_trials():
    """ Play some games with various test phrases and settings """
    # play game using whatever you like
    # maybe put an input statement here
    # so you can enter the corpus
    # and settings
    # or just run various games with various settings

    test_phrases = ['dead war', 'through tough thorough thought though',
    'Hello isn\'t it a lovely day today.']

    # MAKE SURE you test with various phrases!

    test_files = ['the-yellow-wall-paper.txt', 'hamlet.txt', 'le-rire.txt',
    'war-of-the-worlds.txt', 'ulysses.txt', 'war-and-peace.txt']

    #Uncomment the block below to run trials based on the lists of phrases and files above
    for test_phrase in test_phrases:
        for corpus_filename in test_files:
            phrase_length = 0   # for auto-run
            load_corpus_and_play(corpus_filename, test_phrase, phrase_length)
            print('\n'*3)

    # load_corpus_and_play(corpus_filename, 'ba', 7)


def test():
    """ Runs doctests """
    # uncomment various doctest runs to check each method/function
    # MAKE sure your submitted code doesn't run tests except
    # MAKE SURE you add some doctests of your own to the docstrings

    # doctest.run_docstring_examples(Frequency, globs=None)
    # doctest.run_docstring_examples(FrequencyList.add, globs=None)
    # doctest.run_docstring_examples(FrequencyList.remove, globs=None)
    # doctest.run_docstring_examples(FrequencyList.find, globs=None)

    # doctest.run_docstring_examples(filter_possible_chars, globs=None)
    # doctest.run_docstring_examples(count_frequencies, globs=None)
    # doctest.run_docstring_examples(select_next_guess, globs=None)

    # you can leave the following line uncommented as long as your code
    # passes all the tests the line won't produce any output
    doctest.testmod()  # run all doctests - this is helpful before you submit

    # Uncomment the call to run_some_trials below to run
    # whatever trials you have setup in that function
    # IMPORTANT: comment out the run_some_trials() line below
    # before you submit your code
    run_some_trials()

    # IMPORTANT: comment out the run_time_trials() line below
    # before you submit your code
    run_time_trials()



def fallback_guesses(possibles):
    """
    Returns all characters from a--z, and some punctuation that don't appear in
    `possibles`.
    """
    all_fallbacks = [chr(c) for c in range(ord('a'), ord('z') + 1)] + \
                    [' ', ',', '.', "'", '"', ';', '!', '?']
    return [x for x in all_fallbacks if x not in possibles]


def format_document(doc):
    """
    Re-formats `d` by collapsing all whitespace characters into a space and
    stripping all characters that aren't letters or punctuation.
    """
    from unicodedata import category
    # http://www.unicode.org/reports/tr44/#General_Category_Values
    allowed_types = ('Lu', 'Ll', 'Lo', 'Po', 'Zs')
    #d = unicode(d, 'utf-8')
    #d = str(d, 'utf-8')
    # Collapse whitespace
    doc = re.compile(r'\s+', re.UNICODE).sub(' ', doc)
    doc = u''.join([cat.lower()
                    for cat in doc if category(cat) in allowed_types])
    # Remove .encode() to properly process a unicode corpus
    return doc


def confirm(prompt):
    """
    Asks the user to confirm a yes/no question.
    Returns True/False based on their answer.
    """
    ans = ' '
    while ans[0] not in ('Y', 'y', 'n', 'N'):
        ans = input(prompt + ' (y/n) ')
    return True if ans[0] in ('Y', 'y') else False


def check_guess(next_char, guess):
    """
    Returns True if `guess` matches `next_char`, or asks the user if
    `next_char` is None.
    """
    if next_char is not None:
        return next_char == guess
    else:
        return confirm(" '{}'?".format(guess))


def next_guess(guesses):
    """ Returns the next guess """
    return guesses.pop(0) if len(guesses) else None


def check_guesses(next_char, guesses):
    """
    Runs through `guesses` to check against `next_char` (or asks the user if
    `next_char` is None).
    If a correct guess is found, (guess, count) is returned; otherwise
    (None, count) is returned. Where `count` is the number of guesses
    attempted.
    """
    guess = next_guess(guesses)
    guess_count = 1
    while guess is not None:
        if check_guess(next_char, guess):
            return (guess, guess_count)
        guess = next_guess(guesses)
        guess_count += 1
    # Wasn't able to find a guess
    return (None, guess_count)


def guess_next_char(phrase, progress, table, is_auto):
    """ Takes the full phrase, the progress string, the hash table
    and the is_auto flag and returns the next character once it has
    been guessed successfully. Also returns the number of guesses
    used in this guessing.
    """
    # Figure out what the next character to guess is
    # set it to None if not doing auto
    next_char = phrase[len(progress)].lower() if is_auto else None

    # Find possible guesses
    last_two_chars = progress[-2:].lower()
    guesses = table.fetch(last_two_chars)
    if guesses is None:
        guesses = []
    # Convert guesses into a list
    guesses = list(guesses)

    fallbacks = fallback_guesses(guesses)
    fallbacks = list(fallbacks)

    # Try to guess it from the table
    (guess, guess_count) = check_guesses(next_char, guesses)

    if guess is None:
        # If guessing from the corpus failed, try to guess from the
        # fallbacks
        print(' Exhausted all guesses from the corpus! Just guessing...')
        (guess, current_guess_count) = check_guesses(next_char, fallbacks)
        if guess is None:
            # If that failed, we're screwed!
            print(' Exhaused all fallbacks! Failed to guess phrase.')
            # Give up and exit the program
            sys.exit(1)
        guess_count += current_guess_count
    return guess, guess_count


def play_game(table, phrase, phrase_len=0):
    """
    Plays the game.
      `table` is the table mapping keys to lists of character frequencies.
      `phrase` is the phrase to match, or part of the phrase.
      `phrase_len` is the total length of the phrase or 0 for auto mode
    If `phrase_len` is zero, then the game is played automatically and
    the phrase is treated as the whole phrase. Otherwise the phrase is
    the start of the phrase and the function will ask the user whether
    or not it's guesses are correct - and keep going until phrase_len
    characters have been guessed correctly.

    Given phrase_len is 0 by default leaving out phrase_len from
    calls will auto-run, eg, play_game(table, 'eggs') will auto-run

    Returns the total number of guesses taken and the total time taken
    If in interactive mode the time taken value will be 0.
    """
    start = time.perf_counter()
    # Play the game automatically if phrase_len is 0
    is_auto = phrase_len == 0

    # Set phrase length to length of supplied phrase
    if is_auto:
        phrase_len = len(phrase)

    progress = phrase[0:2]
    gap_line = '_' * (phrase_len - len(progress))
    total_guesses = 0
    print('{}{}  (0)'.format(progress, gap_line))
    while len(progress) < phrase_len:
        guess, count = guess_next_char(phrase, progress, table, is_auto)
        progress += guess
        total_guesses += count
        # Print current progress and guess count for the last letter
        gap_line = '_' * (phrase_len - len(progress))
        print('{}{}  ({})'.format(progress, gap_line, count))
    end = time.perf_counter()
    #print('{}  ({})'.format(progress, count))
    print(' Solved it in {} guesses!'.format(total_guesses))

    # return zero time taken if in interactive mode
    time_taken = end - start if is_auto else 0

    return total_guesses, time_taken


def load_corpus_and_play(corpus_filename, phrase, length=0):
    """ Loads the corpus file and plays the game with the given setttings """
    with open(corpus_filename) as infile:
        print('Loading corpus... ' + corpus_filename)
        corpus = format_document(infile.read())
        print('Corpus loaded. ({} characters)'.format(len(corpus)))
        unique_chars = len(set(corpus))
        table = process_corpus(corpus, unique_chars)
        # print(table)
        _, time_taken = play_game(table, phrase, length)
        if length == 0:
            print('Took {:0.6f} seconds'.format(time_taken))


def main():
    """ Put your calls to testing code here.
    The quiz server will not run this function.
    It will test other functions directly.
    NOTE: also comment out all your tests before submitting
    """
    test()


if __name__ == '__main__':
    main()

