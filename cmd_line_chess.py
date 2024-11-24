#!/usr/bin/python3

import copy
import itertools
import re
import os

instructions = '''
-------------------------------------
To move a piece, enter the piece code, followed by the column letter
and row number of the square where you want to move. (Example: Qh4)

If move is legal for more than one piece, enter the column letter or row number
as needed after the piece code to specify piece. (Examples: Rad1, R3h3)

To advance a pawn, enter only the column letter and row number
of the square you want to advance it to. (Example: e4)

If capture is possible with more than one pawn, enter the column letter
of the desired pawn and x before the column letter and row number
of the square where you want to capture. (Example: exd5)

It is unnecessary but acceptable to type x when capturing with other pieces (e.g.: cxd4, Nxe4).

To castle kingside, enter OO or O-O (capital O's, not zeros).
To castle queenside, enter OOO or O-O-O.

To see a list of legal moves for a piece, enter ? followed by its column letter
and row number. (Example: ?b8).

To undo last move, type <. To redo move, type >.

To show move log, type m. To save the game, type s.

To quit the game, type q. To resign, type /. To offer a draw type =.

Piece codes: K = king   Q = queen   R = rook   B = bishop   N = knight
-------------------------------------
'''


color_dict = {'*': {'color': 'white', 'back_rank': 1, 'direction': 1}, '-': {'color': 'black', 'back_rank': 8, 'direction': -1}}

#------------------- basic functions
    
# returns opposite color of current player
def opposite_color(color_code):
    if color_code == '*':
        return('-')
    elif color_code == '-':
        return('*')

def relative_dir(a, b):             #relative direction of a from b: 1, -1, or 0
    try:
        direction = (a - b) // abs(a - b)
    except ZeroDivisionError:
        direction = 0
    return direction

# assembles, aligns, and displays board and marks previous move; calls: opposite_color
def display_board(board, color_code, move_log):   #displays command-prompt board
    if len(move_log[opposite_color(color_code)]) > 0:                               # locate starting and ending squares of previous move in order to mark them
        v_mark_a = int(move_log[opposite_color(color_code)][-1]['start_square'][1])
        h_mark_a = ord(move_log[opposite_color(color_code)][-1]['start_square'][0])
        v_mark_b = int(move_log[opposite_color(color_code)][-1]['move_square'][1])
        h_mark_b = ord(move_log[opposite_color(color_code)][-1]['move_square'][0])
    else:                                                                           # disable previous-move marks at beginning of game
        v_mark_a = 0
        h_mark_a = 0
        v_mark_b = 0
        h_mark_b = 0
        
    s = 55                              #identation of chess board
    
    column_labels = ''
    for c in range(8):                  
        column_labels += '' + chr(c + 97) + '   '   # a - h
    rows = ''
    for r in range(9):
        row_divider = ''
        for c in range(8):                                  # construct_row_dividers
            if      ((v_mark_a in range(8 - r, 10 - r) and       
                     h_mark_a == c + 97) or
                    (v_mark_b in range(8 - r, 10 -r) and
                     h_mark_b == c + 97)):
                row_divider += '+-+-'                       # divider with previous-move mark
            else:
                row_divider += '+---'                       # ordinary divider               
        row_divider += '+'
        rows += row_divider.rjust(s) + '\n'
        if r < 8:                                           # no 9th row, only divider
            row_spaces = str(8 - r) + ' '
            for c in range(9):                              # add column dividers and spaces to rows
                if      ((v_mark_a == 8 - r and
                         h_mark_a in range(c + 96, c + 98)) or
                        (v_mark_b == 8 - r and
                         h_mark_b in range(c + 96, c + 98))):
                    row_spaces += '+'                       # divider with previous-move mark
                else:
                    row_spaces += '|'                       # ordinary divider
                if c < 8:                                   # no 9th space, only divider
                    row_spaces += board[chr(c + 97) + str (8 - r)]  # contents of each space
            rows += row_spaces.rjust(s) + '\n'
    display_board = column_labels.rjust(s) + '\n' + rows
    print('\n', display_board)



#--------------- move calculation functions

#vectors to instantiate piece objects 
king_queen_vectors = [(h, v) for h, v in itertools.product(range(-1, 2), repeat=2) if (h, v) != (0, 0)]     #[(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
rook_vectors = list(itertools.chain(*[itertools.permutations([a, 0]) for a in [-1, 1]]))    #[(-1, 0), (0, -1), (1, 0), (0, 1)]   
bishop_vectors = list(itertools.product([-1, 1], repeat=2))     #[(-1, -1), (-1, 1), (1, -1), (1, 1)]
knight_vectors = list(itertools.chain(*[itertools.permutations([a, b]) for a, b\
                                        in itertools.product([1, -1], [2, -2])]))   #[(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1]
pawn_vectors = list(itertools.product([-1, 1], [1]))      #[(-1, 1), (1, 1)]

class Piece:                                                    

    @staticmethod
    def short_reach(distance, blocked_square):                  # defines condition to terminate looping for king, knight, and pawn after 1 loop
        if distance == 1:
            return True

    @staticmethod
    def long_reach(distance, blocked_square):                   # defines condition to terminate looping for queen, rook, and bishop when path blocked
        if blocked_square == False:
            return True
    
    def __init__(self, name, vectors, reach):
        self.name = name
        self.vectors = vectors
        self.reach = reach

    def get_vectors(self, direction):
        if self.name == 'pawn' and direction == -1:
            return [tuple([v * direction for v in p]) for p in self.vectors]      # reverses vectors for black pawns
        else:
            return self.vectors

#instantiate Piece objects for use in piece_scope()
king = Piece('king', king_queen_vectors, 'short_reach')                 
queen = Piece('queen', king_queen_vectors, 'long_reach')
rook = Piece('rook', rook_vectors, 'long_reach')
bishop = Piece('bishop', bishop_vectors, 'long_reach')
knight = Piece('knight', knight_vectors, 'short_reach')
pawn = Piece('pawn', pawn_vectors, 'short_reach')

piece_family_dict = {'K': king, 'Q': queen, 'R': rook, 'B': bishop, 'N': knight, 'i': pawn}     #keys piece code to piece class object

def evaluate_squares(h, v, column, row, piece, reach_type, board, square_list):
    distance = 1
    blocked_square = False
    while (0 < column + h * distance < 9 and
           0 < row + v * distance < 9 and
           getattr(piece_family_dict[piece], reach_type)(distance, blocked_square) == True):
        square = chr(column + 96 + h * distance) + str(row + v * distance)
        square_list.append(square)
        distance += 1
        if board[square] != '   ':
            blocked_square = True

def add_pieces(moved_pieces, position, board):
    for square in moved_pieces:
        column = ord(square[0]) - 96
        row = int(square[1])
        piece = moved_pieces[square]
        color = piece['color_code']
        piece_code = piece['piece_code']
        position[color].setdefault(piece_code, {})
        position[color][piece_code][square] = []
        new_squares_controlled = []
        reach_type = piece_family_dict[piece_code].reach        #piece_family_dict identifies appropriate piece object
        for h, v in piece_family_dict[piece_code].get_vectors(color_dict[color]['direction']):     #loops all pairs of horizontol and vertical vectors of piece object
            evaluate_squares(h, v, column, row, piece_code, reach_type, board, new_squares_controlled)
        position[color][piece_code][square] = new_squares_controlled     #add squares_controlled to new_position dictionary

def delete_pieces(deleted_pieces, position):
    removal_list = []
    for square in deleted_pieces:
        piece = deleted_pieces[square]
        del position[piece['color_code']][piece['piece_code']][square]
        removal_list.append((piece['color_code'], piece['piece_code']))
    for color, piece in removal_list:
        if position[color][piece] == {}:
            del position[color][piece]

# sets initial arragement of pieces on board and populates initial position dictionary
def arrange_board():                                        
    board = {}
    for c, r in itertools.product(range(97, 105), range(1, 9)):     #creates dictionary for empty chess board   97-104 = chr values of column letters
        board[chr(c) + str(r)] = '   '
    piece_positions = {}
    starting_pieces = ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
    for color_code in color_dict:                                         #arranges pieces and pawn in starting position
        for i in range(97, 105):                                    #97-104 = chr values of column letters
            piece_code = starting_pieces[i - 97]
            piece_square = chr(i) + str(color_dict[color_code]['back_rank'])      #column_letter + back_rank
            pawn_square = piece_square[0] + str(color_dict[color_code]['back_rank'] + color_dict[color_code]['direction'])  #column_letter + back_rank+1
            board[piece_square] = color_code + piece_code + color_code     #color_code + <piece_code from list (corresponding to columns)> + color_code
            board[pawn_square] = color_code + 'i' + color_code
            piece_positions[piece_square] = {'color_code': color_code, 'piece_code': piece_code}
            piece_positions[pawn_square] = {'color_code': color_code, 'piece_code': 'i'}
    position = {'*': {}, '-': {}}
    add_pieces(piece_positions, position, board)
    return board, position

def update_position(board, color_code, move_record, moved_pieces, deleted_pieces, current_position, new_position):
    add_pieces(moved_pieces, new_position, board)
    delete_pieces(deleted_pieces, new_position)
    discovery = {}
    obstruction = {}
    for color in new_position:
        for piece in set(new_position[color]).intersection({'Q', 'R', 'B'}):
            for location in new_position[color][piece]:
                
                for change, effect in [(deleted_pieces, discovery), (moved_pieces, obstruction)]:
                    for square in change:
                        if square in new_position[color][piece][location] and location != move_record['move_square']:
                            effect.setdefault(square, [])
                            effect[square].append(location)
    for color in new_position:
        for piece in set(new_position[color]).intersection({'Q', 'R', 'B'}):
            for location in new_position[color][piece]:
                
                for effect, square_control in [(discovery, True), (obstruction, False)]:
                    for square in effect:
                        if location in effect[square]:
                            current_scope = new_position[color][piece][location]
                            altered_squares = []
                            column = ord(square[0]) - 96
                            row = int(square[1])
                            h = relative_dir(ord(square[0]), ord(location[0]))
                            v = relative_dir(int(square[1]), int(location[1]))
                            evaluate_squares(h, v, column, row, piece, 'long_reach', board, altered_squares)
                            if square_control == True:
                                new_position[color][piece][location] = list(set(current_scope) | set(altered_squares))
                            else:
                                new_position[color][piece][location] = list(set(current_scope) - set(altered_squares))

# moves piece on board and adds move record to move_log
def move_piece(board, color_code, move_record, move_log, current_position):
    piece_code = move_record['piece_code']
    moved_pieces = {}
    deleted_pieces = {}
    if piece_code == 'O':                # move rook when castling
        piece_code = 'K'
        back_rank = str(color_dict[color_code]['back_rank'])
        rook_move_file = chr(101 + relative_dir(ord(move_record['castling_rook']), 101))   # 1 file in direction of rook from the e file (101 = ord('e'))
        castled_rook_square = rook_move_file + back_rank
        original_rook_square = move_record['castling_rook'] + back_rank
        board[castled_rook_square] = board[original_rook_square]            # move rook to castling square
        board[original_rook_square] = '   '                                 # clear original rook squares
        deleted_pieces[original_rook_square] = {'color_code': color_code, 'piece_code': 'R'}
        moved_pieces[castled_rook_square] = {'color_code': color_code, 'piece_code': 'R'}
    deleted_pieces[move_record['start_square']] = {'color_code': color_code, 'piece_code': piece_code}
    if move_record['capture_square_contents'] != '   ':
        deleted_pieces[move_record['move_square']] = {'color_code': opposite_color(color_code),
                                                      'piece_code': move_record['capture_square_contents'][1]}
    if piece_code == 'i':
        if move_record['promotion'] != None:            # pawn promotion
            piece_code = move_record['promotion']
        elif    (move_record['start_square'][0] != move_record['move_square'][0] and     #en passant capture
                 board[move_record['move_square']] == '   '):   
            en_passant_square = move_record['move_square'][0] + move_record['start_square'][1]  # column of move square and row of start square
            move_record['en_passant_capture'] = en_passant_square
            board[en_passant_square] = '   '                # remove captured pawn
            deleted_pieces[en_passant_square] = {'color_code': opposite_color(color_code), 'piece_code': 'i'}

    board[move_record['move_square']] = color_code + piece_code + color_code  # place piece on mvoe square  
    board[move_record['start_square']] = '   '          # clear original square
    move_log[color_code].append(move_record)
    moved_pieces[move_record['move_square']] = {'color_code': color_code, 'piece_code': piece_code}
    new_position = copy.deepcopy(current_position)
    update_position(board, color_code, move_record, moved_pieces, deleted_pieces, current_position, new_position)
    for color in current_position:
        current_position[color] = new_position[color]

# checks if king is currently in check; calls: opposite_color
def check(color_code, current_position, king_position):
    for piece in current_position[opposite_color(color_code)]:                  
        for location in current_position[opposite_color(color_code)][piece]:    #locations of all opposing pieces
            if king_position in current_position[opposite_color(color_code)][piece][location]:      #tests if king is attacked by any opposing piece
                return True
    return False

# calculates all possible (not legal) pawn moves and captures; calls: opposite_color
def pawn_moves_func(board, color_code, current_position, move_log):
    pawn_moves = {}                                #{'piece location': ['all', 'moves', 'for', 'this', 'pawn']}
    back_rank = color_dict[color_code]['back_rank']
    for pawn in current_position[color_code]['i']:         #pawn advance       piece_locations = {'color_code': {'piece_code': ['all', 'locations', 'of', 'this', 'piece', 'type']}}
        single_advance = pawn[0] + str(int(pawn[1]) + color_dict[color_code]['direction'])      #adds 1 advance unit to pawn rank
        if board[single_advance] == '   ':
            pawn_moves.setdefault(pawn, [])
            pawn_moves[pawn].append(single_advance)
            double_advance = pawn[0] + str(int(pawn[1]) + (color_dict[color_code]['direction'] * 2))    #adds 2 advance units to pawn rank
            if int(pawn[1]) == back_rank + color_dict[color_code]['direction'] and board[double_advance] == '   ':
                pawn_moves[pawn].append(double_advance)
        if len(move_log[color_code]) > 0:
            last_opposing_move = (move_log[opposite_color(color_code)][-1])
            for capture in current_position[color_code]['i'][pawn]:
                if      (board[capture][0] == opposite_color(color_code) or                                              #standard pawn capture, or...
                        (last_opposing_move['piece_code'] == 'i' and                                                #opposing pawn just moved...
                         int(last_opposing_move['start_square'][1]) == back_rank + color_dict[color_code]['direction'] * 6 and                  #... from starting square,...
                         int(last_opposing_move['move_square'][1]) == back_rank + color_dict[color_code]['direction'] * 4 and                   #... moved ahead two ranks,...
                         capture == last_opposing_move['move_square'][0] + str(back_rank + color_dict[color_code]['direction'] * 5))):          #... and capturing pawn can capture en passant
                    pawn_moves.setdefault(pawn, [])
                    pawn_moves[pawn].append(capture)
    return pawn_moves

def castling_privileges(board, color_code, current_position, move_log):     # determines if current player has kingside and/or queenside castling privileges; calls: check
    castling_options = {}
    back_rank = str(color_dict[color_code]['back_rank'])
    king = {'home': 'e' + back_rank, 'cond': True}
    k_rook = {'home': 'h' + back_rank, 'cond': True}
    q_rook = {'home': 'a' + back_rank, 'cond': True}
    if check(color_code, current_position, king['home']) == True:    #king must not be in check
        king['cond'] = False
    for move in move_log[color_code]:
        if move['piece_code'] == 'K' or move ['piece_code'] == 'O':           #has king moved?
            king['cond'] = False
        elif move['piece_code'] == 'R' and move['start_square'] == q_rook['home']:     #has queen rook moved?
            q_rook['cond'] = False
        elif move['piece_code'] == 'R' and move['start_square'] == k_rook['home']:     #has king rook moved?
            k_rook['cond'] = False
    for rook in (k_rook, q_rook):
        if king['cond'] == True and rook['cond'] == True:
            squares_clear = True
            if not king['home'] in current_position[color_code]['R'][rook['home']]:    #if king in rook's scope, all spaces between are clear
                squares_clear = False
            no_checks = True
            rook_dir = relative_dir(ord(rook['home'][0]), 101)          # ordinals of rook and king files; result = 1 or -1
            for i in (1, 2):
                square = chr(101 + (i * rook_dir)) + back_rank          #squares king moves through
                if check(color_code, current_position, square) == True: no_checks = False
            if squares_clear == True and no_checks == True:
                castling_options[king['home']] = [chr(101 + rook_dir * 2) + back_rank]      #{king_home_square: king_castle_square}
    return castling_options

# calculates all legal moves for current player and returns results in dictionary; calls: pawn_possible_moves, castling_privileges, move_piece, check
def legal_moves_func(board, color_code, current_position, move_log):
    possible_moves = {}
    for piece_code in current_position[color_code]:
        if piece_code != 'i':                           #find moves for all pieces except pawns
            for location in current_position[color_code][piece_code]:
                for controlled_square in current_position[color_code][piece_code][location]:
                    if board[controlled_square][0] != color_code:
                        possible_moves.setdefault(piece_code, {})
                        possible_moves[piece_code].setdefault(location, [])
                        possible_moves[piece_code][location].append(controlled_square)

    if 'i' in current_position[color_code]:         #find pawn moves
        pawn_moves = {}
        pawn_moves = pawn_moves_func(board, color_code, current_position, move_log)        #{'pawn_location': ['all', 'moves', 'for', 'this', 'pawn']}
        for pawn in pawn_moves:
            possible_moves.setdefault('i', {})
            possible_moves['i'][pawn] = pawn_moves[pawn]
    legal_moves = {}            #legal_moves = {'piece_code': {'location': ['moves', 'for', 'this', 'piece']}}
    for piece_code in possible_moves:
        for location in possible_moves[piece_code]:
            for move in possible_moves[piece_code][location]:
                test_move_dict = {'piece_code': piece_code, 'specifier': '', 'promotion': None,
                                  'start_square': location, 'move_square': move, 'capture_square_contents': '   ',
                                  'en_passant_capture': ''}
                test_board = copy.deepcopy(board)
                test_move_log = copy.deepcopy(move_log)
                test_position = copy.deepcopy(current_position)
                move_piece(test_board, color_code, test_move_dict, test_move_log, test_position)   #makes move on test board
                king_position = list(test_position[color_code]['K'].keys())[0]
                if check(color_code, test_position, king_position) == False:        #disallows moves into check
                    legal_moves.setdefault(piece_code, {})
                    legal_moves[piece_code].setdefault(location, [])
                    legal_moves[piece_code][location].append(move)
    castling_moves = castling_privileges(board, color_code, current_position, move_log)
    if castling_moves != {}: legal_moves['O'] = castling_moves      # adds available castling moves
    return legal_moves


# --------------------------- move execution functions

def show_legal_moves(board, piece_square, legal_moves): # shows legal moves for piece on specified square when requested
    if piece_square == 'O':
        if 'O' in legal_moves:
            print('\nCastling options: ', end='')
            for castle in legal_moves['O']:
                print(castle + '  ', end='')
        else:
            print('You cannot castle at this time.')
        print()
    else:
        piece_code = board[piece_square][1]             # middle character in board square
        print('\n' + piece_code + piece_square + ': ', end='')
        if piece_square in legal_moves.get(piece_code, ''):
            for move in legal_moves[piece_code][piece_square]:
                print(move + '  ', end='')
            print()
        else:
            print('There are no legal moves for that piece.')
    print()

def specify_piece(piece_code, piece_option):    # asks player to specify piece when multiple options available
    piece_name = piece_family_dict[piece_code].name
    print('You can make that move with the %s(s) on the following square(s):' % (piece_name,))
    for location in piece_option:
        print(location, '\t', end='')
    game_state = 0
    choice = ''
    while game_state == 0 and choice != '<':
        print(f'''

Please type the location of the {piece_name} you would like to use.
Type < to reenter your move.
''')
        choice = input()
        if choice in piece_option: game_state = 1
        elif choice != '<':
            print('That is not a valid choice. Please try again.')
    return (choice, game_state)

def pawn_promotion():   # asks player to select piece to promote to
    promotion_list = ['Q', 'R', 'B', 'N']
    game_state = 0
    choice = None
    while game_state == 0 and choice != '<':
        print('''Enter the letter of the piece you would like to promote to.
Type ? to see a list of available promotions. Type < to reenter your move.''')
        choice = input()
        if choice in promotion_list: game_state = 1
        elif choice == '?':
            for option in promotion_list:
                print('%s = %s' % (option, piece_family_dict[option].name))
        elif choice != '<': print('That is not a valid choice. Please try again.')
    return(choice, game_state)

def necessary_specifier(piece_option, start_square):    # determines necessary elements in specifier and returns specifier in minimum essential form; favors file over rank
    if len(piece_option) == 1:          # no specifier necessary
        specifier = ''
    else:
        column_dup = False              # column specifier unnecessary if False
        row_dup = False                 # row specifier unnecessary if True
        duplicates = []
        for location in piece_option:               #find duplicates of column and/or row in piece option
            if location[0] in duplicates: column_dup = True
            if location[1] in duplicates: row_dup = True
            duplicates.append(location[0])
            duplicates.append(location[1])
        if column_dup == False: specifier = start_square[0]                    #remove unnecessary element of specifier
        elif row_dup == False: specifier = start_square[1]
        else: specifier = start_square  # if neither unnecessary, use full specifier
    return specifier

# matches interpreted move to eligible pieces and selects appropriate piece based on user input; calls: specify_piece, pawn_promotion, necessary_specifier
def find_matching_moves(legal_moves, piece_code, color_code, specifier, move_square, promotion):
    if specifier == None: specifier = ''
    matching_pieces = legal_moves.get(piece_code, {'empty': ''})    #finds squares with matching piece type; yields dictionary with 'empty: '' as placeholder to type prevent error if no matching pieces
    piece_option = [location for location in matching_pieces if move_square in matching_pieces[location]]        #stores eligible-piece locations[]
    start_square = ''
    game_state = 1    # game play set to proceed unless no move is found
    if len(piece_option) == 0:          # = no eligible piece
        print('That is not a legal move. Please try again.')
        game_state = 0
    elif len(piece_option) == 1 and (specifier == '' or specifier == '-O'):         # only 1 eligible piece
        start_square = piece_option[0]
    elif len(specifier) == 1:      # only one starting coordinate specified     
        if specifier.isalpha():
            match_regex = specifier + r'[1-8]'
        else: match_regex = r'[a-h]' + specifier
        option_match = re.compile(match_regex)
        match = [m for m in piece_option if option_match.search(m) != None]
        if len(match) == 1: start_square = match[0]
    elif len(specifier) == 2:       # both coordinates specified
        if specifier in piece_option: start_square = specifier
    if game_state == 1:       # if there are eligible pieces
        if start_square == '':      # piece not yet specified
            start_square, game_state = specify_piece(piece_code, piece_option)
            specifier = start_square
        if start_square != '':      # must be "if" condition, not "else" because previous conditional may identify start square
            if specifier != '' and specifier != '-O':
                specifier = necessary_specifier(piece_option, start_square)
            if piece_code == 'i':
                if move_square[0] != start_square[0]:   # pawn is capturing
                    specifier = start_square[0]
                if promotion == None and move_square[-1] == str(color_dict[opposite_color(color_code)]['back_rank']):   #promotion not yet specified
                    promotion, game_state = pawn_promotion()             
    return (start_square, specifier, promotion, game_state)

# validates, interprets, identifies, and executes move entered by player; calls: show_legal_moves, find_matching_moves, move_piece
def execute_move(board, color_code, chosen_move, legal_moves, move_log, redo_move_log, current_position):
    piece_move_format = re.compile(r'^([KQRBN])(([a-h])?([1-8])?)(x)?([a-h][1-8])$')
    pawn_move_format = re.compile(r'^(([a-h])x)?([a-h][1-8])(=(Q|R|B|N))?$')
    castling_move_format = re.compile(r'^O((-)?O)?(-)?O$')
    question_format = re.compile(r'^\?(O|[a-h][1-8])$')
    
    piece_move = piece_move_format.search(chosen_move)
    pawn_move = pawn_move_format.search(chosen_move)
    castling_move = castling_move_format.search(chosen_move)
    question = question_format.search(chosen_move)

    specifier = None
    promotion = None
    castling_rook = None
    if piece_move != None:
        piece_code = piece_move.group(1)    # ^([KQRBN])
        specifier = piece_move.group(2)     # (([a-h])?([1-8])?)
        move_square = piece_move.group(6)   # ([a-h][1-8])$
    elif pawn_move != None:
        piece_code = 'i'
        specifier = pawn_move.group(2)      # ^([a-h])?
        move_square = pawn_move.group(3)    # ([a-h][1-8])
        promotion = pawn_move.group(5)      # (=(Q|R|B|N))?$
    elif castling_move != None:
        back_rank = str(color_dict[color_code]['back_rank'])
        piece_code = 'O'
        if castling_move.group(1) == None:
            move_square = 'g' + back_rank
            castling_rook = 'h'
        else:
            specifier = '-O'
            move_square = 'c' + back_rank
            castling_rook = 'a'
    elif question != None:
        piece_code = '?'
        piece_square = question.group(1)    # (O|[a-h][1-8])$
    else:       # fails to match any valid format
        print('That is not a valid move. Please try again.')
        game_state = 0      # restart turn
        return game_state
    
    if piece_code == '?':           # finds and displays legal moves for specific piece
        show_legal_moves(board, piece_square, legal_moves)
        game_state = 0
    else:       # interpret response as move 
        start_square, specifier, promotion, game_state = find_matching_moves(legal_moves, piece_code, color_code, specifier, move_square, promotion)
            
    if game_state == 1:       # execute and record move
        move_record = {'piece_code': piece_code, 'specifier': specifier, 'promotion': promotion, 'castling_rook': castling_rook,
                       'start_square': start_square, 'move_square': move_square, 'capture_square_contents': board[move_square],
                       'en_passant_capture': ''}
        move_piece(board, color_code, move_record, move_log, current_position)
        del redo_move_log[:]        # moves cannot be redone once new line has been initiated
    return game_state            # 0 = restart turn   1 = proceed to next turn


#---------------- auxillary functions

def save_game(move_log):                    # saves move log to text file
    move_table = display_move_log(move_log)
    print('Enter a filename to save the game.')
    filename = input()
    if ':' in filename or filename == '':   # blocks incorrect filenames that won't cause error
        print('That is not a valid filename.')
        return
    folder = os.path.join('.', 'chess_log_files')
    if os.path.isdir(folder) == False: os.makedirs(folder)
    if not filename.endswith('.txt'): filename += '.txt'
    try:
        new_log_file = open(os.path.join(folder, filename), 'w+')
        new_log_file.write(move_table)
        new_log_file.close()
        print('The game has been saved to %s.\n' % (filename,))
    except:
        print('That is not a valid filename.')

# compiles, organizes, and displays log of previous moves; calls: save_game()
def display_move_log(move_log):
    move_table = ''
    for move_number in range(len(move_log['*'])):
        move_table += (str(move_number + 1) + ':').ljust(5)     # adds move number and aligns following text
        for color in move_log:
            move = move_log[color][move_number]                 # next move in log
            move_code = move['move_square']                     # starts building move notation
            if move['capture_square_contents'] != '   ' or move['en_passant_capture'] != '':    # capture took place
                move_code = 'x' + move_code
            if move['specifier'] != '':
                move_code = move['specifier'] + move_code
            if move['piece_code'] in ('K', 'Q', 'R', 'B', 'N', 'O'):
                move_code = move['piece_code'] + move_code       
            if move['promotion'] != None:
                move_code = move_code + '=' + move['promotion']
            if move['piece_code'] == 'O':
                move_code = 'O' + move['specifier'] + '-O'
            if color == '*':
                move_table += move_code.ljust(10)               # adds white's move to table and aligns following text for blacks move      
                if len(move_log['-']) == move_number:           # terminates loop on with white on last move if no corresponding move for black
                    move_table += '\n'
                    break
            else:
                move_table += move_code + '\n'                  # adds black's move
    return(move_table)

# undoes last move in move log; calls: opposite_color
def undo_move(board, color_code, move_log, redo_move_log, current_position):
    if move_log[color_code] == []:
        print('There are no moves to undo.')
        game_state = 0
        return game_state
    game_state = 1
    move = move_log[color_code].pop()                           # retrieves and deletes record of last move for color designated by function call
    piece_code = move['piece_code']
    restored_pieces = {}
    withdrawn_pieces = {}
    if move['capture_square_contents'] != '   ':
        restored_pieces[move['move_square']] = {'color_code': opposite_color(color_code), 'piece_code': move['capture_square_contents'][1]}
    board[move['start_square']] = board[move['move_square']]    # reverses move
    board[move['move_square']] = move['capture_square_contents']
    if piece_code == 'O':                               # reverses castling
        piece_code = 'K'
        rook_move_file = chr(101 + relative_dir(ord(move['castling_rook']), 101))   # --- 1 file in direction of rook from the e file (101 = ord('e'))
        castled_rook_square = rook_move_file + str(color_dict[color_code]['back_rank'])
        original_rook_square = move['castling_rook'] + str(color_dict[color_code]['back_rank'])
        board[original_rook_square] = board[castled_rook_square]                    #move rook to pre-castling position
        board[castled_rook_square] = '   '
        restored_pieces[original_rook_square] = {'color_code': color_code, 'piece_code': 'R'}
        withdrawn_pieces[castled_rook_square] = {'color_code': color_code, 'piece_code': 'R'}
    restored_pieces[move['start_square']] = {'color_code': color_code, 'piece_code': piece_code}
    if move['promotion'] != None:
        board[move['start_square']] = color_code + 'i' + color_code
        piece_code = move['promotion']
    elif move['en_passant_capture'] != '':
        en_passant_square = move['en_passant_capture']
        board[en_passant_square] = opposite_color(color_code) + 'i' + opposite_color(color_code)    #restores pawn captured en_passant
        restored_pieces[en_passant_square] = {'color_code': opposite_color(color_code), 'piece_code': 'i'}
    redo_move_log.append(move)          # only undone moves can be redone
    withdrawn_pieces[move['move_square']] = {'color_code': color_code, 'piece_code': piece_code}
    restored_position = copy.deepcopy(current_position)
    update_position(board, color_code, move, restored_pieces, withdrawn_pieces, current_position, restored_position)
    for color in current_position:
        current_position[color] = restored_position[color]
    return game_state

def end_of_game(board, color_code, move_log, redo_move_log, current_position):    # handles end-of-game options; calls: display_move_log, undo_move, opposite_color
    game_state = -1
    option = ''
    while option != 'q':
        print('\nTo undo last move, type <. To display move log, type m. To save game, type s. To finish, type q.')
        option = input()
        if option == 'm': print(display_move_log(move_log))
        if option == 's': save_game(move_log)
        if option == '<':
            game_state = undo_move(board, opposite_color(color_code), move_log, redo_move_log, current_position)
            break
    return game_state

# executes single-character option requests by player during turn; calls: display_move_log, opposite_color, save_game undo_move, move_piece
def game_options(board, color_code, chosen_move, move_log, redo_move_log, current_position):
    game_state = 0
    if chosen_move == 'i': print(instructions)
    elif chosen_move == 'q':        # quit game
        game_state = -1
    elif chosen_move == '/':        # resign game
        print(color_dict[color_code]['color'].capitalize() + ' resigns. ' +
              color_dict[opposite_color(color_code)]['color'].capitalize() + ' wins!')
        game_state = -1
    elif chosen_move == '=':        # offer draw
        print(color_dict[color_code]['color'].capitalize() + ' is offering a draw. Would you like to accept? (To accept, enter y. To refuse, enter nothing.)')
        choice = input()
        if choice == 'y':
            print('The players have agreed to a draw.')
            game_state = -1
        else:
            print(color_dict[opposite_color(color_code)]['color'].capitalize() + ' has refused the draw.\n')
    elif chosen_move == 'm': print(display_move_log(move_log))
    elif chosen_move == 's': save_game(move_log)
    elif chosen_move == '<':        # undo last move
        game_state = undo_move(board, opposite_color(color_code), move_log, redo_move_log, current_position)
    elif chosen_move == '>':        # redo redo last undone move
        if redo_move_log == []:
            print('There are no moves to redo.')
            return None
        move_piece(board, color_code, redo_move_log.pop(), move_log, current_position)
        game_state = 1    
    else: print('That is not a valid move. Please try again.')  # invalid entry

    if game_state == -1:
        game_state = end_of_game(board, color_code, move_log, redo_move_log, current_position)
    return game_state

# checks for conditions of check, checkmate, stalemate, and insufficient material at beginning of turn; calls end_of_game in case of checkmate or draw
# calls: check, end_of_game
def mate_check_draw(board, color_code, silent_mode, current_position, legal_moves, move_log, redo_move_log):
    game_state = 0
    king_position = list(current_position[color_code]['K'].keys())[0]
    if check(color_code, current_position, king_position) == True:      # detects check
        if legal_moves == {}:                                           # checkmate
            print('Checkmate! ' + color_dict[opposite_color(color_code)]['color'].capitalize() + ' wins!')
            game_state = -1
        elif silent_mode == False:                                        # simple check
           print('The ' + color_dict[color_code]['color'] + ' king is in check.')
    elif legal_moves == {}:         # stalemate
        print('Stalemate! The game is drawn.')
        game_state = -1
    if game_state == 0:       # no checkmate or stalemate
        if len(current_position[color_code]) < 3 and len(current_position[opposite_color(color_code)]) == 1:    # possibility of insufficient material
            sufficient_material = None
            if      (len(current_position[color_code]) == 2 and           # knight/bishop + king vs. lone king = insufficient material
                    'B' not in current_position[color_code] and
                    'N' not in current_position[color_code]):
                sufficient_material = True
            if sufficient_material != True:
                print('The game is drawn due to insufficient material.')
                game_state = -1
    if game_state == -1:
        game_state = end_of_game(board, color_code, move_log, redo_move_log, current_position)
    return game_state


# -------------------- primary game-play function

def play_game(file_path, silent_mode):    # calls: arrange_board, display_board, legal_moves_func, mate_check_draw
    game_board, current_position = arrange_board()
    color_code = '*'                    # sets first turn to white
    move_log = {'*': [], '-': []}       # {'color_code': ['piece_code', 'piece_square', 'move_square', 'captured_piece', 'capture_square']}
    redo_move_log = []
    chosen_move = ''
    game_state = 0                # 0 = turn not complete, do not proceed to next turn; 1 = finish turn and go to next turn; -1 = game over
    if file_path == '': move_seq = []   # no game to restore, continue with normal gameplay
    else:                               # game is being restored
        game_file = open(file_path)
        log_file = [i.split()[1:] for i in list(game_file)] # captures each pair of moves in the log file as a second-dimension list of 2, removing the move number 
        game_file.close()
        move_seq = list(itertools.chain.from_iterable(log_file)) # combines all moves into one continuous sequence
    while game_state > -1:       # loop until game is over
        if silent_mode == False:    # keep updating display
            display_board(game_board, color_code, move_log)
            if len(move_log['*']) > 0:  # if previous moves exist
                last_move = display_move_log(move_log).split()[-1]
                print(last_move, '\n')
        legal_moves = legal_moves_func(game_board, color_code, current_position, move_log)         #legal_moves: {'piece_code': {'location': ['moves', 'for', 'this', 'piece']}
        game_state = mate_check_draw(game_board, color_code, silent_mode, current_position,
                                        legal_moves, move_log, redo_move_log)
        auto_move_attempt = 0
        while game_state == 0:                                 # begins turn execution
            if move_seq != []:   # there are moves to restore
                auto_move_attempt += 1
                if auto_move_attempt == 1:      # detects unsuccessful auto move attempt in order to stop auto moving
                    chosen_move = move_seq.pop(0)
                    if silent_mode == False:
                        print('Press enter for next move. To stop and play game from this point, type x.')
                        response = input()
                        if response == 'x':     # exit restore mode and continue play normally
                            del move_seq[:]
                            continue
                    elif move_seq == []:        # restarts board refresh when auto moves complete
                        silent_mode = False
                else:                           # stops restore when unsuccessful move attempted
                    del move_seq[:]
                    slient_mode = False
                    display_board(game_board, color_code, move_log)
                    continue
            else:
                print("It's " + color_dict[color_code]['color'] + "'s turn to move. Please enter your move. For more instructions type i.")     #initial move instructions in normal play
                chosen_move = input()
            if len(chosen_move) < 2:
                game_state = game_options(game_board, color_code, chosen_move, move_log, redo_move_log, current_position)      # option entered instead of move
            else:
                game_state = execute_move(game_board, color_code, chosen_move, legal_moves, move_log, redo_move_log, current_position)
        color_code = opposite_color(color_code)                     #sets next turn to opposite color


mode = ''
while mode != 'x':  # x = terminate the program
    print('''
To start a new game, type n. To restore a game, type r.
For game instructions, type i. To exit, type x.''')
    mode = input()
    if mode == 'i':     # show instructions
        print(instructions)
    elif mode == 'r':   # restore game
        print('''
Enter the name of the log file you would like to load.
(Enter filename only, not path.)''')
        filename = input()
        if not filename.endswith('.txt'): filename += '.txt'
        file_path = os.path.join('.', 'chess_log_files', filename)
        if os.path.isfile(file_path):
            print('Type m to manually review each move. Press enter to load final position.')   # choose restoration mode
            if input() == 'm': silent_mode = False  # continue updating display
            else: silent_mode = True                # do not update display until final position is reached
            play_game(file_path, silent_mode)
        else:
            print('That is not a valid filename.')
    elif mode == 'n':   # start new game
        silent_mode = False
        play_game('', silent_mode)
    elif mode != 'x':   # x = terminate the program
        print('That is not a valid choice.')
