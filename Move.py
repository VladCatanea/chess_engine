#pieces: piece number = type * 4 + color
white = 2
black = 1
pawn = 1
bishop = 2
knight = 3
rook = 4
queen = 5
king = 6

class Move:
    """class to represent a move"""
    def __init__(self, piece, start_coord, end_coord, capture=False, promotion=0, check=False, mate=False):
        self.piece = piece
        self.start_coord = start_coord
        self.end_coord = end_coord
        self.capture = capture
        self.promotion = promotion
        self.check = check
        self.mate = mate

    def __str__(self):
        s = ''
        if self.piece//4 == king and abs(self.start_coord[1] - self.end_coord[1]) > 1:
            #this means it is a castling move
            if self.start_coord[1] < self.end_coord[1]:
                s += 'O-O' #short castle
            else:
                s += 'O-O-O' #long castle
        else:    
            s += piece_name_to_notation(self.piece // 4)
            if self.capture:
                if self.piece // 2 == pawn:
                    s += coord_to_chess_notation(self.start_coord)[0]
                s += 'x'
            s += coord_to_chess_notation(self.end_coord)
            if self.promotion:
                s += '=' + piece_name_to_notation(self.promotion)
        if self.mate:
            s += '#'
        elif self.check:
            s += '+'
        return s

    def __eq__(self, other):
        if not isinstance(other, Move):
            return False
        if self.piece != other.piece:
            return False
        if self.start_coord != other.start_coord:
            return False
        if self.end_coord != other.end_coord:
            return False
        return True


def coord_to_chess_notation(coord):
    """
    transforms coordinates where (0,0) is the black queenside rook 
    to normal chess notation where that square is a8
    """
    s = ''
    #column
    s += chr(ord('a') + coord[1])
    #row
    s += str(8 - coord[0])
    return s

def piece_name_to_notation(piece_name):
    if piece_name == king:
        return 'K'
    elif piece_name == queen:
        return 'Q'
    elif piece_name == rook:
        return'R'
    elif piece_name == bishop:
        return 'B'
    elif piece_name == knight:
        return 'N'
    elif piece_name == pawn:
        return ''
    else:
        return 'X'

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


def nicer_print(move, board_array):
    """
    converts the move on the 10x12 board array in chess notation 
    string for better readability when printed on screen
    """
    piece = board_array[move[0]]
    capture = board_array[move[1]]
    mate = False
    check = False
    promotion = 0
    s = ''
    if piece // 4 == king and abs(move[0] % 10 - move[1] % 10) > 1:
        #this means it is a castling move
        if move[0] < move[1]:
            s += 'O-O' #short castle
        else:
            s += 'O-O-O' #long castle
    else:    
        s += piece_name_to_notation(piece // 4)
        if capture:
            if piece // 4 == pawn:
                s += index_to_chess_notation(move[0])[0]
            s += 'x'
        s += index_to_chess_notation(move[1])
        if promotion:
            s += '=' + piece_name_to_notation(promotion)
    if mate:
        s += '#'
    elif check:
        s += '+'
    return s
