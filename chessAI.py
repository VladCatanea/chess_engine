import numpy as np 
import random

from move_gen_10x12 import * 
from Move import nicer_print


#king doesn't matter since both players are going to have exactly 1
material_score = {'checkmate': 100000, 
                  'stalemate': 0,
                  0: 0,   #no piece score
                  pawn: 100,
                  bishop: 330,
                  knight: 320,
                  rook: 500,
                  queen: 900,
                  king: 200000} 

#piece-square tables - simplified evaluation function
#from https://www.chessprogramming.org/Simplified_Evaluation_Function, 
#originally by Tomasz Michniewski
pst = {
     pawn: [  0,  0,  0,  0,  0,  0,  0,  0,
             50, 50, 50, 50, 50, 50, 50, 50,
             10, 10, 20, 30, 30, 20, 10, 10,
              5,  5, 10, 25, 25, 10,  5,  5,
              0,  0,  0, 20, 20,  0,  0,  0,
              5, -5,-10,  0,  0,-10, -5,  5,
              5, 10, 10,-20,-20, 10, 10,  5,
              0,  0,  0,  0,  0,  0,  0,  0
            ],
    knight: [-50,-40,-30,-30,-30,-30,-40,-50,
             -40,-20,  0,  0,  0,  0,-20,-40,
             -30,  0, 10, 15, 15, 10,  0,-30,
             -30,  5, 15, 20, 20, 15,  5,-30,
             -30,  0, 15, 20, 20, 15,  0,-30,
             -30,  5, 10, 15, 15, 10,  5,-30,
             -40,-20,  0,  5,  5,  0,-20,-40,
             -50,-40,-30,-30,-30,-30,-40,-50
            ],
    bishop: [-20,-10,-10,-10,-10,-10,-10,-20,
             -10,  0,  0,  0,  0,  0,  0,-10,
             -10,  0,  5, 10, 10,  5,  0,-10,
             -10,  5,  5, 10, 10,  5,  5,-10,
             -10,  0, 10, 10, 10, 10,  0,-10,
             -10, 10, 10, 10, 10, 10, 10,-10,
             -10,  5,  0,  0,  0,  0,  5,-10,
             -20,-10,-10,-10,-10,-10,-10,-20
            ],
    rook:   [  0,  0,  0,  0,  0,  0,  0,  0,
               5, 10, 10, 10, 10, 10, 10,  5,
              -5,  0,  0,  0,  0,  0,  0, -5,
              -5,  0,  0,  0,  0,  0,  0, -5,
              -5,  0,  0,  0,  0,  0,  0, -5,
              -5,  0,  0,  0,  0,  0,  0, -5,
              -5,  0,  0,  0,  0,  0,  0, -5,
               0,  0,  0,  5,  5,  0,  0,  0
            ],
    queen:  [-20,-10,-10, -5, -5,-10,-10,-20,
             -10,  0,  0,  0,  0,  0,  0,-10,
             -10,  0,  5,  5,  5,  5,  0,-10,
              -5,  0,  5,  5,  5,  5,  0, -5,
               0,  0,  5,  5,  5,  5,  0, -5,
             -10,  5,  5,  5,  5,  5,  0,-10,
             -10,  0,  5,  0,  0,  0,  0,-10,
             -20,-10,-10, -5, -5,-10,-10,-20
            ],
    king:   [-30,-40,-40,-50,-50,-40,-40,-30,
             -30,-40,-40,-50,-50,-40,-40,-30,
             -30,-40,-40,-50,-50,-40,-40,-30,
             -30,-40,-40,-50,-50,-40,-40,-30,
             -20,-30,-30,-40,-40,-30,-30,-20,
             -10,-20,-20,-20,-20,-20,-20,-10,
              20, 20,  0,  0,  0,  0, 20, 20,
              20, 30, 10,  0,  0, 10, 30, 20
            ],  #king in the middlegame
    # king:   [-50,-40,-30,-20,-20,-30,-40,-50,
    #          -30,-20,-10,  0,  0,-10,-20,-30,
    #          -30,-10, 20, 30, 30, 20,-10,-30,
    #          -30,-10, 30, 40, 40, 30,-10,-30,
    #          -30,-10, 30, 40, 40, 30,-10,-30,
    #          -30,-10, 20, 30, 30, 20,-10,-30,
    #          -30,-30,  0,  0,  0,  0,-30,-30,
    #          -50,-30,-30,-30,-30,-30,-30,-50
    #         ]  #king in the endgame

}

# from sunfish - https://github.com/thomasahle/sunfish
# pst = {
#     pawn: (   0,   0,   0,   0,   0,   0,   0,   0,
#             78,  83,  86,  73, 102,  82,  85,  90,
#              7,  29,  21,  44,  40,  31,  44,   7,
#            -17,  16,  -2,  15,  14,   0,  15, -13,
#            -26,   3,  10,   9,   6,   1,   0, -23,
#            -22,   9,   5, -11, -10,  -2,   3, -19,
#            -31,   8,  -7, -37, -36, -14,   3, -31,
#              0,   0,   0,   0,   0,   0,   0,   0),
#     knight: ( -66, -53, -75, -75, -10, -55, -58, -70,
#             -3,  -6, 100, -36,   4,  62,  -4, -14,
#             10,  67,   1,  74,  73,  27,  62,  -2,
#             24,  24,  45,  37,  33,  41,  25,  17,
#             -1,   5,  31,  21,  22,  35,   2,   0,
#            -18,  10,  13,  22,  18,  15,  11, -14,
#            -23, -15,   2,   0,   2,   0, -23, -20,
#            -74, -23, -26, -24, -19, -35, -22, -69),
#     bishop: ( -59, -78, -82, -76, -23,-107, -37, -50,
#            -11,  20,  35, -42, -39,  31,   2, -22,
#             -9,  39, -32,  41,  52, -10,  28, -14,
#             25,  17,  20,  34,  26,  25,  15,  10,
#             13,  10,  17,  23,  17,  16,   0,   7,
#             14,  25,  24,  15,   8,  25,  20,  15,
#             19,  20,  11,   6,   7,   6,  20,  16,
#             -7,   2, -15, -12, -14, -15, -10, -10),
#     rook: (  35,  29,  33,   4,  37,  33,  56,  50,
#             55,  29,  56,  67,  55,  62,  34,  60,
#             19,  35,  28,  33,  45,  27,  25,  15,
#              0,   5,  16,  13,  18,  -4,  -9,  -6,
#            -28, -35, -16, -21, -13, -29, -46, -30,
#            -42, -28, -42, -25, -25, -35, -26, -46,
#            -53, -38, -31, -26, -29, -43, -44, -53,
#            -30, -24, -18,   5,  -2, -18, -31, -32),
#     queen: (   6,   1,  -8,-104,  69,  24,  88,  26,
#             14,  32,  60, -10,  20,  76,  57,  24,
#             -2,  43,  32,  60,  72,  63,  43,   2,
#              1, -16,  22,  17,  25,  20, -13,  -6,
#            -14, -15,  -2,  -5,  -1, -10, -20, -22,
#            -30,  -6, -13, -11, -16, -11, -16, -27,
#            -36, -18,   0, -19, -15, -15, -21, -38,
#            -39, -30, -31, -13, -31, -36, -34, -42),
#     king: (   4,  54,  47, -99, -99,  60,  83, -62,
#            -32,  10,  55,  56,  56,  55,  10,   3,
#            -62,  12, -57,  44, -67,  28,  37, -31,
#            -55,  50,  11,  -4, -19,  13,   0, -49,
#            -55, -43, -52, -28, -51, -47,  -8, -50,
#            -47, -42, -43, -79, -64, -32, -29, -32,
#             -4,   3, -14, -50, -57, -18,  13,   4,
#             17,  30,  -3, -14,   6,  -1,  40,  18),
# }

DEPTH = 1


def coord_10x12_to_8x8_array(i):
    """
    changes index of the same chess board square from a 1D array
    in a 10x12 representation to a 1D array in a 8x8 representation
    """
    return (i // 10 - 2) * 8 + i % 10 - 1

def index_to_chess_notation(index):
    """
    transforms an array index from a 10x12 array representation
    of a chess board into chess notation
    """
    i, j = index // 10 - 2, index % 10 - 1
    s = ''
    #column
    s += chr(ord('a') + j)
    #row
    s += str(8 - i)
    return s

def score_position(board):
    color = black if board.color_to_move == white else white #color of the player that just moved
    #first check for checkmate/stalemate (TODO: stalemate -> need function to check wether legal moves exist without generating all of them otherwise performance is bad)
    if check(color, board.state, board.king_pos[board.color_to_move]) and len(legal_move_list(board)) == 0:
        if color == white:
            return material_score['checkmate']
        if color == black:
            return -material_score['checkmate']
    #now we calculate the material score
    score = 0
    board_array = board.state
    for i in range(120): #iterate through the board
            if board_array[i] > 0:
                piece = board_array[i]
                if piece % 4 == white: #add the piece score if white piece
                    score += material_score[piece // 4]
                    score += pst[piece // 4][coord_10x12_to_8x8_array(i)] 
                else: #if black piece, substract the piece score
                    score -= material_score[piece // 4]
                    score -= pst[piece // 4][63 - coord_10x12_to_8x8_array(i)] 
    return score

def least_important_attacker(board, square):
    """
    Returns the attacker with the smallest material score or 
    None if no enemy pieces attack that square
    board parameter is just an array, not the object
    """
    #enemy color = opposite color of the piece on the square
    color = white if board[square] % 4 == black else black
    #first pawn attacks
    pawn_direction = 10 if color == white else -10
    if board[square + pawn_direction + 1] == pawn * 4 + color:
        return square + pawn_direction + 1
    if board[square + pawn_direction - 1] == pawn * 4 + color:
        return square + pawn_direction - 1
    #now other attacks
    #remember the piece codes so we don't have to calculate them every time 
    enemy_knight = knight * 4 + color
    enemy_bishop = bishop * 4 + color
    enemy_queen = queen * 4 + color
    enemy_rook = rook * 4 + color
    enemy_king = king * 4 + color
    #knight
    for d in directions[knight]:
        if board[square + d] == enemy_knight:
            return square + d
    #bishop
    for d in directions[bishop]:
        for adv in range(1, 8): #how many squares to advance
            piece = board[square + adv * d]
            if piece == enemy_bishop:
                return square + adv * d
            if piece != 0:
                break # if it isn't an empty square
    #rook
    for d in directions[rook]:
        for adv in range(1, 8):
            piece = board[square + adv * d]
            if piece == enemy_rook:
                return square + adv * d
            if piece != 0:
                break # if it isn't an empty square
    #queen
    for d in directions[queen]:
        for adv in range(1, 8):
            piece = board[square + adv * d]
            if piece == enemy_queen:
                return square + adv * d
            if piece != 0:
                break # if it isn't an empty square
    #now the king
    for d in directions[king]:
        if board[square + d] == enemy_king:
            return square + d
    return None


def static_exchange_evaluation(board_array, move):
    """
    It calculates whether a capture is 'good' or 'bad' based on 
    the material count after several exchanges on the same square
    """
    #square where the captures take place
    target_square = move[1]
    #initialise score with our first capture
    score = material_score[board_array[move[1]] // 4]
    #make the move
    board_array[move[1]] = board_array[move[0]]
    board_array[move[0]] = 0
    
    while True:
        #if the score is less than 0 after our capture then the
        #opponent can stop here and the exchange is bad2
        if score < 0:
            return False
        LIA = least_important_attacker(board_array, target_square)
        #if opponent has no more attackers
        if not LIA:
            return True
        score -= material_score[board_array[target_square] // 4]
        #make the move
        board_array[target_square] = board_array[LIA]
        board_array[LIA] = 0
        #now let's look at our attacker
        LIA = least_important_attacker(board_array, target_square)
        #if we have no more attackers
        if not LIA:
            if score < 0:
                return False
            else:
                return True 
        score += material_score[board_array[target_square] // 4]
        #make the move
        board_array[target_square] = board_array[LIA]
        board_array[LIA] = 0
    

def find_best_move(board, move_list, depth=DEPTH):
    global negamax_best_move
    global negamax_alphabeta_best_move
    global minmax_best_move
    global max_depth
    global counter
    #color multiplier
    color_mx = 1 if board.color_to_move == white else -1
    maximizing_player = True if board.color_to_move == white else False
    max_depth = depth
    counter = 0
    # random.shuffle(move_list)
    # best_score = nega_max(board, move_list, color_mx, depth)
    best_score = negamax_alphabeta(board, -10**6, 10**6, color_mx, depth)
    # best_score = minmax_alphabeta(board, -10**6, 10**6, maximizing_player, depth, False)
    print('position evaluation:', -best_score) # the score is maximized from the black player perspective
    print('counter:', counter)
    return negamax_alphabeta_best_move

def negamax_alphabeta(board, alpha, beta, color_mx, depth):
    """
    using a nega max min max algorithm we iterate (recursively) 
    through all the possible moves up to a depth of *depth*, 
    chosing the best one, which is returned through the 
    global variable "negamax_alphabeta_best_move"
    """
    global negamax_alphabeta_best_move
    global max_depth
    global counter
    counter += 1
    if depth == 0:
        return score_position(board) * color_mx
    best_score = -10**6
    move_list = legal_move_list(board)
    no_moves_flag, move_list = order_moves(move_list, board.state)
    for move in move_list:
        next_board = deepcopy(board)
        next_board.move(move[0], move[1])
        score = -negamax_alphabeta(next_board, -beta, -alpha, -color_mx, depth-1)
        if score > best_score:
            best_score = score
            if depth == max_depth:
                negamax_alphabeta_best_move = move
        if best_score > alpha:
            alpha = best_score
        if alpha >= beta:
            return best_score
    if no_moves_flag:
        return score_position(board) * color_mx
    return best_score

def hash_board(board_array):
    board_hash = 0
    for i in range(8):
        for j in range(8):
            index = 20 + i * 10 + j + 1
            board_hash += (i * 8 + j) * 30 + board_array[index]
    return board_hash


def quiescence_search(board, alpha, beta, maximizing_player):
    return score_position(board)

def minmax_alphabeta(board, alpha, beta, maximizing_player, depth, capture_move=False):
    global minmax_best_move
    global max_depth
    global counter
    counter += 1
    # print(depth)
    if depth <= 0: 
        if capture_move == False: #last move has to not be a capture in order to stop
            return score_position(board)
        else:
            return quiescence_search(board, alpha, beta, maximizing_player)
    # if depth < -20:  
    #     print(depth)
    #     print(board)
    move_list = legal_move_list(board)
    no_moves, move_list = order_moves(move_list, board.state, depth)
    if maximizing_player:
        best_score = -10**6
        for move in move_list:
            next_board = deepcopy(board)
            next_board.move(move[0], move[1])
            # print(nicer_print(move, board.state), score_position(next_board))
            capture_move = True if board.state[move[1]] != 0 else False
            score = minmax_alphabeta(next_board, alpha, beta, not maximizing_player, depth-1, capture_move=capture_move)
            if score > best_score:
                best_score = score
                if depth == max_depth:
                    minmax_best_move = move
            if best_score > alpha:
                alpha = best_score
            if alpha >= beta:
                return best_score
        if no_moves:
            best_score = score_position(board)
        return best_score
    else:
        #minimizing player
        best_score = 10**6
        for move in move_list:
            next_board = deepcopy(board)
            next_board.move(move[0], move[1])
            # print(nicer_print(move, board.state), score_position(next_board))
            # if depth == 2:
                # print(nicer_print(move, board.state))
            capture_move = False #True if board.state[move[1]] != 0 else False
            score = minmax_alphabeta(next_board, alpha, beta, not maximizing_player, depth-1, capture_move=capture_move)
            if score < best_score:
                best_score = score
                if depth == max_depth:
                    minmax_best_move = move
            if best_score < beta:
                beta = best_score
            if beta <= alpha:
                return best_score
        if no_moves:
            best_score = score_position(board)
        return best_score

def negamax(board, color_mx, depth):
    """
    using a nega max min max algorithm we iterate (recursively) 
    through all the possible moves up to a depth of *depth*, 
    chosing the best one, which is returned through the 
    global variable *negamax_best_move*
    """
    global negamax_best_move
    global max_depth
    global counter
    counter += 1
    if depth == 0:
        return color_mx * score_position(board)
    move_list = legal_move_list(board)
    best_score = -10**6
    for move in move_list:
        next_board = deepcopy(board)
        next_board.move(move[0], move[1])
        score = -negamax(next_board, -color_mx, depth-1)
        if score > best_score:
            best_score = score
            if depth == max_depth:
                nega_max_best_move = move
    return color_mx * best_score

def order_moves(move_list, board_array, quiet=True):
    no_moves_flag = False
    good_capture_moves = []
    quiet_moves = []
    bad_capture_moves = []
    for move in move_list:
        if board_array[move[1]]:
            good_capture_moves.append(move)
            # if static_exchange_evaluation(deepcopy(board_array), move):
            #     good_capture_moves.append(move)
            # else:
            #     bad_capture_moves.append(move)
        elif quiet:
            quiet_moves.append(move)
    all_moves = good_capture_moves + quiet_moves + bad_capture_moves
    if len(all_moves) == 0:
        no_moves_flag = True
    return no_moves_flag, all_moves



