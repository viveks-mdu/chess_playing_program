__author__ = 'vivek'

import math, random, sys, time, bisect, string, functools, collections
import unicodedata
from termcolor import colored, cprint

board = [0 for i in range(64)]
stm = 0
max_depth = 4
k_wt = 200
q_wt = 9
r_wt = 5
b_wt = 3
n_wt = 3
p_wt = 1
capture_aggression_factor = 1
prune_nx_moves = 0

def user_readable_format(square_code):

    if square_code == 0:
        return str(".")
    color = "black" if square_code >> 6 == 1 else "white"

    pieces = {6: 'K', 5: 'Q', 3: 'B', 2: 'N', 4: 'R', 1: 'P'}

    str_value = (pieces[square_code & 7])
    if color == "black":
        return str_value.lower()
    else:
        return str_value

def print_chess_board(state):
    files = [' ', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', ' ']

    unicode_pieces = {
                        'K': "\u2654",
                        'Q': "\u2655",
                        'R': "\u2656",
                        'B': "\u2657",
                        'N': "\u2658",
                        'P': "\u2659",
                        'k': "\u265A",
                        'q': "\u265B",
                        'r': "\u265C",
                        'b': "\u265D",
                        'n': "\u265E",
                        'p': "\u265F",
                        '.': " "
                     }

    attributes = []

    for chr in files:
        print("  %s " % chr, end="")
    # print()
    dash = '-'
    # for i in range(10):
    #     print("  %s " % dash, end="")
    print()
    flip = 0
    for i in range(8, 0, -1):
        print("  %s " % i, end="")
        for j in range(0, 8, 1):
            if flip:
                cprint(colored("  %s " % unicode_pieces[user_readable_format(state[(i-1)*8 + j])],
                               'green', 'on_grey', attrs=attributes), end="")
                flip = 0
            else:
                cprint(colored("  %s " % unicode_pieces[user_readable_format(state[(i-1)*8 + j])],
                               'green', 'on_white', attrs=attributes), end="")
                flip = 1
        print("  %s" % i, end="")
        print()
        if flip == 0:
            flip = 1
        else:
            flip = 0
    # for i in range(10):
    #     print("  %s " % dash, end="")
    # print()
    for chr in files:
        print("  %s " % chr, end="")
    print()

def get_piece_in_square(inp_state, rank, file, return_code = 0):
    state = list(inp_state)
    # print("rank: %d, file: %s" % (int(rank), file))
    rank = int(rank)-1
    files = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
    file_num = files[file]

    # print("board index: %d" % (8*int(rank) + file_num))
    square_code = state[8*int(rank) + file_num]
    if return_code:
        return square_code
    else:
        piece = user_readable_format(square_code)
    return piece


def place_piece(piece, color, rank=0, file=0):
    allowed_pieces = {'k': 6, 'q': 5, 'b': 3, 'n': 2, 'r': 4, 'p': 1}
    allowed_colors = {'w': 0, 'b': 1}
    allowed_files = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}


    if piece not in allowed_pieces.keys():
        print("Invalid piece: %s" % piece)
        return

    if color not in allowed_colors:
        print("Invalid color: %s" % color)
        return

    if file not in allowed_files:
        print("Invalid file passed: %s" % file)
        file_num = 0
        return
    else:
        file_num = allowed_files[file]

    value = allowed_colors[color] << 6 | allowed_pieces[piece]

    board[8*(rank - 1) + file_num] = value

def validate_move(inp_state, move):
    state = list(inp_state)
    piece_type = 'P'
    move_type = 'move'
    color = 1

    result = move.split("-")
    if len(result) <= 1:
        result = move.split("x")
        move_type = 'capture'
        if len(result) <= 1:
            print("Invalid move input")
            return 0

    if len(result[0]) == 3:
        piece_type = result[0][0]

    from_location = result[0][-2:]
    to_location = result[1][-2:]

    # check if the piece type is in that position
    piece = get_piece_in_square(state, from_location[1], from_location[0])
    color_result = get_color(piece)
    if piece.lower() == piece_type.lower() and color_result == color:
        # print('piece mentioned present in the from location')
        print("", end="")
    else:
        print('piece mentioned NOT present in the from location')
        return 0

    possible_moves, score = generate_moves(state, piece_type, from_location, color)
    # print(possible_moves)

    if move_type == 'capture':
        check_move = "x"+result[1]
    else:
        check_move = result[1]

    if check_move in possible_moves:
        # print("valid move")
        return 1
    else:
        print("invalid move")
        print("Possible moves: ", possible_moves)
        return 0

def execute_move(inp_state, from_location, to_location):
    state = list(inp_state)
    files = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}

    # print("from location: %s, to location: %s" % (from_location, to_location))
    square_code = get_piece_in_square(state, from_location[1], from_location[0], 1)
    state[8*(int(to_location[1])-1) + files[to_location[0]]] = int(square_code)
    state[8*(int(from_location[1])-1) + files[from_location[0]]] = 0

    # print_chess_board(state)
    return state

def check_within_board(rank, file):
    if rank >= 1 and rank <= 8 and ord(file) >= 97 and ord(file) <= 104:
        return 1
    else:
        return 0

def get_strike_value_for_piece(piece):
    piece = piece.lower()
    if piece == 'k':
        score = 9
    elif piece == 'q':
        score = 5
    elif piece == 'r':
        score = 4
    elif piece == 'b':
        score = 3
    elif piece == 'n':
        score = 3
    elif piece == 'p':
        score = 2

    return (score * capture_aggression_factor)

def check_move(inp_state, rank, file, color):
    state = list(inp_state)
    score = 0
    # print("rank: %d; file: %s" % (rank, file))
    if check_within_board(rank, file):
        piece = get_piece_in_square(state, rank, file)
        color_result = get_color(piece)
        if color_result != -1:
            if color_result != color:
                # print("x%s%d" % (file, rank))
                score = get_strike_value_for_piece(piece)
                return 0, ("x%s%d" % (file, rank)), score
            else:
                return 0, "", score
        else:
            # print("%s%d" % (file, rank))
            return 1, ("%s%d" % (file, rank)), 1
    else:
        return 0, "", score

def generate_moves(inp_state, piece_type, from_location, color):
    state = list(inp_state)
    total_score = 0
    possible_moves = []

    if piece_type.lower() == 'k':
        direction = range(1, 9, 1)
        distance = 1
    elif piece_type.lower() == 'q':
        direction = range(1, 9, 1)
        distance = 8
    elif piece_type.lower() == 'b':
        direction = [2, 4, 6, 8]
        distance = 8
    elif piece_type.lower() == 'n':
        direction = range(9, 17, 1)
        distance = 1
    elif piece_type.lower() == 'r':
        direction = [1, 3, 5, 7]
        distance = 8
    elif piece_type.lower() == 'p':
        if color == 0:
            direction = [17, 18, 21, 22]
        elif color == 1:
            direction = [19, 20, 23, 24]
        distance = 1

    # if piece_type == 'R' and color == 0:
    #     print(piece_type, from_location, direction)

    original_file = from_location[0]
    original_rank = int(from_location[1])
    for direction_i in direction:
        file = original_file
        rank = original_rank
        if direction_i == 1:
            for d in range(distance):
                file = chr(ord(file)+1)
                status, move, score = check_move(state, rank, file, color)
                if move:
                    possible_moves.append(move)
                    total_score = total_score + score
                if not status:
                    break
        if direction_i == 2:
            for d in range(distance):
                file = chr(ord(file)+1)
                rank = rank+1
                status, move, score = check_move(state, rank, file, color)
                if move:
                    possible_moves.append(move)
                    total_score = total_score + score
                if not status:
                    break
        if direction_i == 3:
            for d in range(distance):
                rank = rank+1
                status, move, score = check_move(state, rank, file, color)
                if move:
                    possible_moves.append(move)
                    total_score = total_score + score
                if not status:
                    break
        if direction_i == 4:
            for d in range(distance):
                file = chr(ord(file)-1)
                rank = rank+1
                status, move, score = check_move(state, rank, file, color)
                if move:
                    possible_moves.append(move)
                    total_score = total_score + score
                if not status:
                    break
        if direction_i == 5:
            for d in range(distance):
                file = chr(ord(file)-1)
                status, move, score = check_move(state, rank, file, color)
                if move:
                    possible_moves.append(move)
                    total_score = total_score + score
                if not status:
                    break
        if direction_i == 6:
            for d in range(distance):
                file = chr(ord(file)-1)
                rank = rank-1
                status, move, score = check_move(state, rank, file, color)
                if move:
                    possible_moves.append(move)
                    total_score = total_score + score
                if not status:
                    break
        if direction_i == 7:
            for d in range(distance):
                rank = rank-1
                status, move, score = check_move(state, rank, file, color)
                if move:
                    possible_moves.append(move)
                    total_score = total_score + score
                if not status:
                    break
        if direction_i == 8:
            for d in range(distance):
                file = chr(ord(file)+1)
                rank = rank-1
                status, move, score = check_move(state, rank, file, color)
                if move:
                    possible_moves.append(move)
                    total_score = total_score + score
                if not status:
                    break
        if direction_i == 9:
            file = chr(ord(file) + 2)
            rank = rank+1
            status, move, score = check_move(state, rank, file, color)
            if move:
                possible_moves.append(move)
                total_score = total_score + score
        if direction_i == 10:
            file = chr(ord(file) + 1)
            rank = rank+2
            status, move, score = check_move(state, rank, file, color)
            if move:
                possible_moves.append(move)
                total_score = total_score + score
        if direction_i == 11:
            file = chr(ord(file) - 1)
            rank = rank+2
            status, move, score = check_move(state, rank, file, color)
            if move:
                possible_moves.append(move)
                total_score = total_score + score
        if direction_i == 12:
            file = chr(ord(file) - 2)
            rank = rank+1
            status, move, score = check_move(state, rank, file, color)
            if move:
                possible_moves.append(move)
                total_score = total_score + score
        if direction_i == 13:
            file = chr(ord(file) - 2)
            rank = rank-1
            status, move, score = check_move(state, rank, file, color)
            if move:
                possible_moves.append(move)
                total_score = total_score + score
        if direction_i == 14:
            file = chr(ord(file) - 1)
            rank = rank-2
            status, move, score = check_move(state, rank, file, color)
            if move:
                possible_moves.append(move)
                total_score = total_score + score
        if direction_i == 15:
            file = chr(ord(file) + 1)
            rank = rank-2
            status, move, score = check_move(state, rank, file, color)
            if move:
                possible_moves.append(move)
                total_score = total_score + score
        if direction_i == 16:
            file = chr(ord(file) + 2)
            rank = rank-1
            status, move, score = check_move(state, rank, file, color)
            if move:
                possible_moves.append(move)
                total_score = total_score + score
        if direction_i == 17:
            pawn_file = file
            pawn_rank = rank

            file = chr(ord(file)+1)
            rank = rank+1

            if check_within_board(rank, file):
                piece = get_piece_in_square(state, rank, file)
                color_result = get_color(piece)
                if color_result != -1:
                    if color_result != color:
                        # print("x%s%d" % (file, rank))
                        possible_moves.append("x%s%d" % (file, rank))
                        total_score = total_score + get_strike_value_for_piece(piece)
        if direction_i == 18:
            pawn_file = file
            pawn_rank = rank

            file = chr(ord(file)-1)
            rank = rank+1

            if check_within_board(rank, file):
                piece = get_piece_in_square(state, rank, file)
                color_result = get_color(piece)
                if color_result != -1:
                    if color_result != color:
                        # print("x%s%d" % (file, rank))
                        possible_moves.append("x%s%d" % (file, rank))
                        total_score = total_score + get_strike_value_for_piece(piece)
        if direction_i == 19:
            pawn_file = file
            pawn_rank = rank

            file = chr(ord(file)-1)
            rank = rank-1

            if check_within_board(rank, file):
                piece = get_piece_in_square(state, rank, file)
                color_result = get_color(piece)
                if color_result != -1:
                    if color_result != color:
                        # print("x%s%d" % (file, rank))
                        possible_moves.append("x%s%d" % (file, rank))
                        total_score = total_score + get_strike_value_for_piece(piece)
        if direction_i == 20:
            pawn_file = file
            pawn_rank = rank

            file = chr(ord(file)+1)
            rank = rank-1

            if check_within_board(rank, file):
                piece = get_piece_in_square(state, rank, file)
                color_result = get_color(piece)
                if color_result != -1:
                    if color_result != color:
                        # print("x%s%d" % (file, rank))
                        possible_moves.append("x%s%d" % (file, rank))
                        total_score = total_score + get_strike_value_for_piece(piece)
        if direction_i == 21:
            pawn_file = file
            pawn_rank = rank

            rank = rank+1

            # status, move = check_move(state, rank, file, color)
            # if move:
            #     possible_moves.append(move)
            if check_within_board(rank, file):
                piece = get_piece_in_square(state, rank, file)
                if piece == ".":
                    # print("%s%d" % (file, rank))
                    possible_moves.append("%s%d" % (file, rank))
                    total_score = total_score + 1
        if direction_i == 22:
            if rank != 2:
                continue
            pawn_file = file
            pawn_rank = rank

            rank = rank+2

            # status, move = check_move(state, rank, file, color)
            # if move:
            #     possible_moves.append(move)

            if check_within_board(rank, file):
                piece = get_piece_in_square(state, rank, file)
                if piece == ".":
                    # print("%s%d" % (file, rank))
                    possible_moves.append("%s%d" % (file, rank))
                    total_score = total_score + 1
        if direction_i == 23:
            pawn_file = file
            pawn_rank = rank

            rank = rank-1

            # status, move = check_move(state, rank, file, color)
            # if move:
            #     possible_moves.append(move)

            if check_within_board(rank, file):
                piece = get_piece_in_square(state, rank, file)
                if piece == ".":
                    possible_moves.append("%s%d" % (file, rank))
                    total_score = total_score + 1
        if direction_i == 24:
            if rank != 7:
                continue
            pawn_file = file
            pawn_rank = rank

            rank = rank-2

            # status, move = check_move(state, rank, file, color)
            # if move:
            #     possible_moves.append(move)
            if check_within_board(rank, file):
                piece = get_piece_in_square(state, rank, file)
                if piece == ".":
                    # print("%s%d" % (file, rank))
                    possible_moves.append("%s%d" % (file, rank))
                    total_score = total_score + 1

    return possible_moves, total_score

def get_color(piece):
    if piece in ['k', 'q', 'b', 'n', 'r', 'p']:
        return 1
    elif piece in ['K', 'Q', 'B', 'N', 'R', 'P']:
        return 0
    else:
        return -1

def get_user_move():
    print()
    user_move = input("Enter your move (* for changing parameters):\n")
    return user_move

def get_moves_for_player(inp_state, player=0):
    state = list(inp_state)
    possible_moves = []
    capture_moves = []
    total_score = 0

    possible_moves_for_piece = {}
    for i in range(64):
        if (state[i] >> 6 == player) and (state[i]):
            rank = int(i/8) + 1
            file = chr((i%8) + 97)
            piece = get_piece_in_square(state, rank, file)
            # if piece == 'R' and player == 0:
            #     print("player %d, piece %s, rank %d, file %s" % (player, piece, rank, file))
            possible_moves_for_piece, score = generate_moves(state, piece, str(file)+str(rank), player)
            total_score = total_score + score
            # print(possible_moves_for_piece)
            if piece.lower() == 'p':
                piece = ""
            if len(possible_moves_for_piece) > 0:
                for move in possible_moves_for_piece:
                    if len(move) == 3:
                        capture_moves.append(piece+str(file)+str(rank)+move)
                    else:
                        possible_moves.append(piece+str(file)+str(rank)+"-"+move)
    return (capture_moves + possible_moves), total_score

def calc_material_score(inp_state):
    state = list(inp_state)

    wp, wn, wb, wr, wq, wk, bp, bn, bb, br, bq, bk = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    for i in range(64):
        rank = int(i/8) + 1
        file = chr((i%8) + 97)
        piece = get_piece_in_square(state, rank, file)
        # print(state[i], piece, rank, file)

        if state[i] == 1:
            wp = wp+1
        elif state[i] == 2:
            wn = wn+1
        elif state[i] == 3:
            wb = wb+1
        elif state[i] == 4:
            wr = wr+1
        elif state[i] == 5:
            wq = wq+1
        elif state[i] == 6:
            wk = wk+1
        elif state[i] == 65:
            bp = bp+1
        elif state[i] == 66:
            bn = bn+1
        elif state[i] == 67:
            bb = bb+1
        elif state[i] == 68:
            br = br+1
        elif state[i] == 69:
            bq = bq+1
        elif state[i] == 70:
            bk = bk+1

    material_score = k_wt * (wk - bk) \
                        + q_wt * (wq - bq) \
                        + r_wt * (wr - br) \
                        + b_wt * (wb - bb) \
                        + n_wt * (wn - bn) \
                        + p_wt * (wp - bp)

    return material_score

def calc_mobility_score(inp_state, player):
    state = list(inp_state)

    my_score = 0
    opponent_score = 0

    if player == 0:
        opponent = 1
        mfactor = 1
    else:
        opponent = 0
        mfactor = -1

    my_possible_moves, my_score = get_moves_for_player(state, player)
    # for move in my_possible_moves:
    #     my_score = my_score + analyze_move(move)
    # my_score = len(my_possible_moves)


    opponent_possible_moves, opponent_score = get_moves_for_player(state, opponent)
    # for move in opponent_possible_moves:
    #     opponent_score = opponent_score + analyze_move(move)
    # opponent_score = len(opponent_possible_moves)

    score = (my_score - opponent_score) * mfactor

    # print(score)
    return score * (0.25)

def analyze_move(move):
    score = 0
    piece_type = 'P'
    move_type = 'move'
    color = 1

    result = move.split("-")
    if len(result) <= 1:
        result = move.split("x")
        move_type = 'capture'

    if len(result[0]) == 3:
        piece_type = result[0][0]
    else:
        piece_type = 'P'

    from_location = result[0][-2:]
    to_location = result[1][-2:]

    if move.find('x') != -1:
        # capture
        score = score + 5

    from_location_x = ord(from_location[0])
    from_location_y = int(from_location[1])

    to_location_x = ord(to_location[0])
    to_location_y = int(to_location[1])

    if (from_location_x == to_location_x) or (from_location_y == to_location_y):
        dist = abs(to_location_y - from_location_y) + abs(to_location_x - from_location_x)
    else:
        dist = ((to_location_y - from_location_y) ** 2 + (to_location_x - from_location_x) ** 2) ** 0.5

    piece_type = piece_type.lower()

    score = score + (dist)

    return score

def alphabeta_search(inp_state, game, d=4, player=0, cutoff_test=None, eval_fn=None):
    """Search game to determine best action; use alpha-beta pruning.
    This version cuts off search and uses an evaluation function."""
    state = list(inp_state)

    # player = game.to_move(state)

    def max_value(inp_state, player, alpha, beta, depth):
        state = list(inp_state)
        # print("max_value -> alpha: %d; beta: %d; depth:%d" % (alpha, beta, depth))
        # print_chess_board(state)
        if cutoff_test(state, depth, player):
            return eval_fn(state, player)
        v = -5000
        opponent = 1 if player == 0 else 0
        for a in game.actions(state, player):
            # print("action by %s: %s" % (player, a))
            # print_chess_board(state)
            if prune_nx_moves and depth >= 3 and a.find("x") == -1:
                continue

            v = max(v, min_value(game.result(state, a), opponent,
                                 alpha, beta, depth+1))
            if v >= beta:
                return v
            alpha = max(alpha, v)
        return v

    def min_value(inp_state, player, alpha, beta, depth):
        state = list(inp_state)
        # print("min_value -> alpha: %d; beta: %d; depth:%d" % (alpha, beta, depth))
        # print_chess_board(state)
        if cutoff_test(state, depth, player):
            return eval_fn(state, player)
        v = 5000
        opponent = 1 if player == 0 else 0
        for a in game.actions(state, player):
            # print("action by %s: %s" % (player, a))
            # if depth >= 3 and a.find("x") == -1:
            #     continue
            v = min(v, max_value(game.result(state, a), opponent,
                                 alpha, beta, depth+1))
            if v <= alpha:
                return v
            beta = min(beta, v)
        return v

    # Body of alphabeta_search starts here:
    # The default test cuts off at depth d or at a terminal state
    cutoff_test = (cutoff_test or
                   (lambda state, depth, player: depth>=d or game.terminal_test(state, player)))
    eval_fn = eval_fn or (lambda state, player: game.utility(state, player))

    current_max= -5000
    best_action = ""
    opponent = 1 if player == 0 else 0
    for action in game.actions(state, player):
        # print(action)
        resultant_state = game.result(state, action)
        # print("action by %s: %s" % (player, action))
        value = min_value(resultant_state, opponent, -5000, 5000, 1)
        if value > current_max:
            # print(value)
            current_max = value
            best_action = action

    return best_action

    # return argmax(game.actions(state, player),
    #               lambda a: min_value(game.result(state, a), opponent,
    #                                   -5000, 5000, 0))

def argmax(keys, f):
    return max(keys, key=f)

class Game:
    """A game is similar to a problem, but it has a utility for each
    state and a terminal test instead of a path cost and a goal
    test. To create a game, subclass this class and implement actions,
    result, utility, and terminal_test. You may override display and
    successors or you can inherit their default methods. You will also
    need to set the .initial attribute to the initial state; this can
    be done in the constructor."""

    initial = {}

    def __init__(self):
        print("Place pieces at initial positions")
        place_piece("k", "w", 1, "e")
        place_piece("q", "w", 1, "d")
        place_piece("r", "w", 1, "a")
        place_piece("n", "w", 1, "b")
        place_piece("b", "w", 1, "c")
        place_piece("b", "w", 1, "f")
        place_piece("n", "w", 1, "g")
        place_piece("r", "w", 1, "h")

        place_piece("k", "b", 8, "e")
        place_piece("q", "b", 8, "d")
        place_piece("r", "b", 8, "a")
        place_piece("n", "b", 8, "b")
        place_piece("b", "b", 8, "c")
        place_piece("b", "b", 8, "f")
        place_piece("n", "b", 8, "g")
        place_piece("r", "b", 8, "h")

        for j in range(97, 105, 1):
            place_piece("p", "w", 2, chr(j))
            place_piece("p", "b", 7, chr(j))

        # place_piece("q", "b", 2, "e")
        print("Initial alignment done")

        self.initial = board
        print_chess_board(board)

    def actions(self, inp_state, player):
        # "Return a list of the allowable moves at this point."
        # find all the pieces of corresponding player
        state = list(inp_state)
        # print_chess_board(state)
        possible_moves, score = get_moves_for_player(state, player)
        return possible_moves

    def result(self, inp_state, move):
        "Return the state that results from making a move from a state."
        state = list(inp_state)

        # print(move)

        result = move.split("-")
        if len(result) == 1:
            result = move.split("x")
            move_type = 'capture'
            if len(result) == 1:
                print("Invalid move input")

        from_location = result[0][-2:]
        to_location = result[1][-2:]

        # print(from_location, to_location)

        return execute_move(state, from_location, to_location)

    def utility(self, inp_state, player):
        "Return the value of this final state to player."
        state = list(inp_state)

        material_score = 0
        mobility_score = 0

        # calculate material score
        material_score = calc_material_score(state)

        mobility_score = calc_mobility_score(state, player)

        # if player == 1:
        #     material_score = material_score * (-1)

        # print("material score:", material_score)

        return (material_score + mobility_score)

    def terminal_test(self, inp_state, player, actual_play = 0):
        "Return True if this is a final state for the game."
        state = list(inp_state)
        opponent = 1 if player == 0 else 0
        king_under_attack = 0
        check_mate = 0

        possible_moves, score = get_moves_for_player(state, opponent)
        for move in possible_moves:
            state_after_move = self.result(state, move)
            # self.utility(state, player)
            if not check_king_present(state_after_move, player):
                king_under_attack = 1
                break

        if king_under_attack and actual_play:
            cprint(colored("king under attack", "red"))

        if king_under_attack:
            check_mate = 1
            my_moves, score = get_moves_for_player(state, player)
            for my_move in my_moves:
                one_ply_state = self.result(state, my_move)
                # print("my_move : %s" % my_move, end=" ")
                # print_chess_board(one_ply_state)
                opponent_moves, score = get_moves_for_player(one_ply_state, opponent)
                # print(opponent_moves)
                safe_move = 1
                for opponent_move in opponent_moves:
                    # print_chess_board(one_ply_state)
                    # print("opponent move", opponent_move)
                    two_ply_state = self.result(one_ply_state, opponent_move)
                    # print_chess_board(two_ply_state)
                    if not check_king_present(two_ply_state, player):
                        safe_move = 0
                        break
                if safe_move:
                    check_mate = 0
                # print("safe move", safe_move)
        else:
            check_mate = 0

        # print(check_mate)
        if check_mate and actual_play:
            cprint(colored("CHECKMATE", 'red'))
        return check_mate

    def __repr__(self):
        return '<%s>' % self.__class__.__name__

def check_king_present(state, player):
    king_piece = 6 if player == 0 else 70
    try:
        king_present = state.index(king_piece)
    except:
        king_present = 0

    return king_present

def change_parameters():
    global max_depth, k_wt, q_wt, r_wt, b_wt, n_wt, p_wt, capture_aggression_factor, prune_nx_moves

    while 1:
        print()
        print("Choose from below options:")
        print("1 -> depth: %d" % max_depth)
        print("2 -> king weightage: %d" % k_wt)
        print("3 -> queen weightage: %d" % q_wt)
        print("4 -> rook weightage: %d" % r_wt)
        print("5 -> bishop weightage: %d" % b_wt)
        print("6 -> knight weightage: %d" % n_wt)
        print("7 -> pawn weightage: %d" % p_wt)
        print("8 -> aggression factor(1-5): %d" % capture_aggression_factor)
        print("9 -> Only capture moves after depth 3(0|1): %d" % prune_nx_moves)
        print("0 -> EXIT")

        option_entered = int(input("Enter your option to change:"))

        if option_entered == 1:
            max_depth = get_user_input("Enter search depth:")
        elif option_entered == 2:
            k_wt = get_user_input("Enter king weightage:")
        elif option_entered == 3:
            q_wt = get_user_input("Enter queen weightage:")
        elif option_entered == 4:
            r_wt = get_user_input("Enter rook weightage:")
        elif option_entered == 5:
            b_wt = get_user_input("Enter bishop weightage:")
        elif option_entered == 6:
            n_wt = get_user_input("Enter knight weightage:")
        elif option_entered == 7:
            p_wt = get_user_input("Enter pawn weightage:")
        elif option_entered == 8:
            capture_aggression_factor = get_user_input("Enter capture aggression factor:")
            if capture_aggression_factor > 5:
                capture_aggression_factor = 5
            if capture_aggression_factor < 1:
                capture_aggression_factor = 1
        elif option_entered == 9:
            prune_nx_moves = get_user_input("Only capture moves after depth 3(0|1):")
            if prune_nx_moves > 1:
                prune_nx_moves = 1
            if prune_nx_moves < 1:
                prune_nx_moves = 0
        elif option_entered == 0:
            break

def get_user_input(input_instr):
    while 1:
        try:
            input_entered = int(input(input_instr))
            return  input_entered
        except ValueError:
            print("Error: not an integer")


print("Starting ... ")

chess = Game()

state = chess.initial
player = 0
ply_count = 1
while not chess.terminal_test(state, player, 1):
    if player == 0:
        move = alphabeta_search(state, chess, max_depth, player)
        player_color = "WHITE"
    else:
        is_valid_move = 0
        while not is_valid_move:
            move = get_user_move()
            if move == "*":
                change_parameters()
                print_chess_board(state)
            else:
                is_valid_move = validate_move(state, move)
        player_color = "BLACK"

    state = chess.result(state, move)
    cprint(colored("%d) %s made move: %s" % (ply_count, player_color, move)), "blue", "on_yellow")
    print_chess_board(state)
    if player == 0:
        player = 1
    else:
        player = 0
    ply_count = ply_count + 1


print("Program execution completed")