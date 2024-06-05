from copy import deepcopy
import numpy as np
import time


#pieces: piece number = type * 4 + color
white = 2
black = 1
pawn = 1
bishop = 2
knight = 3
rook = 4
queen = 5
king = 6

# to access a square to the right we add +1, to the left -1, upwards -10, downwards +10
# -1 values represent out of bounds squares, 0 empty squares, positive numbers are pieces
initial_board = [ -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
                  -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
                  -1, 17, 13,  9, 21, 25,  9, 13, 17, -1,
                  -1,  5,  5,  5,  5,  5,  5,  5,  5, -1,
                  -1,  0,  0,  0,  0,  0,  0,  0,  0, -1,
                  -1,  0,  0,  0,  0,  0,  0,  0,  0, -1,
                  -1,  0,  0,  0,  0,  0,  0,  0,  0, -1,
                  -1,  0,  0,  0,  0,  0,  0,  0,  0, -1,
                  -1,  6,  6,  6,  6,  6,  6,  6,  6, -1,
                  -1, 18, 14, 10, 22, 26, 10, 14, 18, -1,
                  -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
                  -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
                  ]

#the directions in which the pieces move in the above array
directions = {
    bishop: [+11, -11, +9, -9],  
    knight: [+21, +19, -21, -19, 12, 8, -12, -8], 
    rook: [-1, +1, -10, +10],
    queen: [-1, +1, -10, +10, +11, -11, +9, -9], 
    king: [-1, +1, -10, +10, +11, -11, +9, -9] 
}


def matrix(board):
    """
    takes a 120 size array (representing a 10x12 board), and
    returns a 8x8 matrix representation of the board
    """
    board_matrix = [[ 0 for _ in range(8)] for _ in range(8)]
    for i in range(len(board)):
        if board[i] == -1:
            continue
        board_matrix[i // 10 - 2][i % 10 - 1] = board[i]
    return board_matrix

def array(board_matrix):
    """
    takes a 8x8 matrix representation of the board, and
    returns a 120 size array (representing a 10x12 board)
    """
    array = []
    for _ in range(20):
        array.append(-1)
    for i in range(8):
        array.append(-1)
        for j in range(8):
            array.append(board_matrix[i][j])
        array.append(-1)
    for _ in range(20):
        array.append(-1)
    return array

def array_to_matrix_coord(i):
    """
    changes from coordinates in a 120 nr array representation
    of a board to a more normal 8x8 matrix representation
    """
    return (i // 10 - 2, i % 10 - 1)


def gen_pawn_moves(color, board, pos, en_passant_square):
    #in which direction the pawn usually moves depends on color
    direction = -10 if color == white else 10
    piece = pawn * 4 + color #piece code
    #the row of the 10x12 board on which we promote
    last_row = 2 if color == white else 9
    #if the square is empty, the pawn can advance
    if board[pos + direction] == 0:
        if (pos + direction) // 10 == last_row:
            for promotion in [queen, rook, knight, bishop]:
                yield pos, pos + direction, promotion
        yield pos, pos + direction
        #2 square advance now
        if (color == white and pos // 10 == 8) or (color == black and pos // 10 == 3):
            if board[pos + 2*direction] == 0:
                yield pos, pos + 2 * direction
    #now check for captures
    capture_directions = [direction + 1, direction - 1]
    enemy_color = black if color == white else white
    for d in capture_directions:
        if board[pos + d] % 4 == enemy_color or pos + d == en_passant_square:
            if (pos + direction) // 10 == last_row:
                for promotion in [queen, rook, knight, bishop]:
                    yield pos, pos + d, promotion
            yield pos, pos + d

def gen_possible_moves(color, board, en_passant_square, right_to_castle_short, right_to_castle_long):
    """
    Generates all the possible moves that can be made by
    color and returns the boards after the moves are made
    board parameter is just an array, not the object
    """
    for (pos, piece) in enumerate(board):
        if piece % 4 != color:
            continue
        if piece // 4 == pawn:
            #pawns are special
            for move in gen_pawn_moves(color, board, pos, en_passant_square):
                yield move
            continue
        #other pieces have more predictable patterns of movement
        for direction in directions[piece // 4]:
            for adv in range(1, 8): #how much the piece advances along given direction
                destination = board[pos + direction * adv]
                #check for castling
                if piece // 4 == rook and destination == king * 4 + piece % 4: #same color king
                    if direction * adv > 0 and right_to_castle_long[piece % 4]:
                        #check first if the king or any square that the king has to go through is in check
                        enemy_color = black if color == white else white
                        for i in range(pos + 2, pos + direction * adv + 1):
                            if check(enemy_color, board, i):
                                break
                        else:
                            yield (pos + direction * adv, pos) #king pos is first, then the rook
                    elif direction * adv < 0 and right_to_castle_short[piece % 4]:
                        #check first if the king or any square that the king has to go through is in check
                        enemy_color = black if color == white else white
                        for i in range(pos + direction * adv, pos + direction * adv + 3):
                            if check(enemy_color, board, i):
                                break
                        else:
                            yield (pos + direction * adv, pos) #king pos is first, then the rook
                #break if there is a same color piece blocking or out of bounds
                if destination == -1 or destination % 4 == color:
                    break
                #make move
                yield pos, pos + direction * adv
                if destination != 0:
                    break # if this wasn't an empty square, it was a capture
                if piece // 4 == pawn or piece // 4 == knight or piece // 4 == king:
                    break #piece can only advance one square in this direction

def gen_legal_moves(board):
    """
    Generates all legal moves from a board object
    The input parameter is a board object
    Yields tuples of the form (starting_coordinate, end_coordinate)
    """
    color = board.color_to_move
    enemy_color = black if color == white else white
    board_array = board.state
    for move in gen_possible_moves(color, board_array, board.en_passant_square, board.right_to_castle_short, board.right_to_castle_long):
        next_board = deepcopy(board)
        next_board.move(move[0], move[1])
        if not check(enemy_color, next_board.state, next_board.king_pos[color]):
            yield move

def legal_move_list(board):
    move_list = []
    for move in gen_legal_moves(board):
        move_list.append(move)
    return move_list


def check(color, board, king_pos):
    """
    returns True if *color* holds the opponent in check,
    False otherwise
    """
    king_color = black if color == white else white
    #first pawn attacks
    pawn_direction = 10 if color == white else -10
    if board[king_pos + pawn_direction + 1] == pawn * 4 + color:
        return True
    if board[king_pos + pawn_direction - 1] == pawn * 4 + color:
        return True 
    #now other attacks
    #remember the piece codes so we don't have to calculate them every time 
    enemy_knight = knight * 4 + color
    enemy_bishop = bishop * 4 + color
    enemy_queen = queen * 4 + color
    enemy_rook = rook * 4 + color
    enemy_king = king * 4 + color
    for d in directions[knight]:
        if board[king_pos + d] == enemy_knight:
            return True
    #diagonal sliders
    for d in directions[bishop]:
        for adv in range(1, 8):
            piece = board[king_pos + adv * d]
            if piece == enemy_bishop or piece == enemy_queen:
                return True
            if piece != 0:
                break # if it isn't an empty square
    #line sliders
    for d in directions[rook]:
        for adv in range(1, 8):
            piece = board[king_pos + adv * d]
            if piece == enemy_rook or piece == enemy_queen:
                return True
            if piece != 0:
                break # if it isn't an empty square
    #now the king
    for d in directions[king]:
        if board[king_pos + d] == enemy_king:
            return True
    return False






if __name__ == '__main__':
    start_time = time.process_time()

    board = initial_board
    king_color = white

    # 0.2s
    # for _ in range(10000):
    #     for i in range(20, 120): 
    #         if board[i] // 4 == king and board[i] % 4 == king_color:
    #             king_pos = i
    #             break
    # print(king_pos)

    # 0.15s
    for _ in range(1000 * 100):
        check(black, initial_board, 95)
        

    end_time = time.process_time()
    print('time:', end_time - start_time)


    input('press <Enter> to exit')

