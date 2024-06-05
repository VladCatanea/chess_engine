from move_gen_10x12 import initial_board, matrix, white, black, rook, bishop, knight, queen, king, pawn
from chessAI import material_score

class Board:
    """class to hold the board"""
    def __init__(self):
        self.state = initial_board
        # print(self.state)
        self.color_to_move = white
        self.right_to_castle_short = [True, True, True]
        self.right_to_castle_long = [True, True, True]
        self.en_passant_square = -1
        self.king_pos = [0, 25, 95]
        # self.score = 0
        
    def __str__(self):
        s = ''
        for line in matrix(self.state):
            for piece in line:
                if piece:
                    s += 'X'
                else:
                    s += 'O'
            s += '\n'
        return s
    
    def __eq__(self, other):
        if not isinstance(other, Board):
            return False
        for i in range(8):
            for j in range(8):
                piece1 = self.state[i][j]
                piece2 = other.state[i][j]
                if piece1 != piece2:
                    return
        if self.color_to_move != other.color_to_move:
            return False
        return True
    
    def move(self, old_coord, new_coord, promotion=0):
        #check that the move is not redundant
        if old_coord == new_coord:
            return False
        #check that piece exists
        if self.state[old_coord] == 0:
            return False
        #keep the piece in a local variable
        piece = self.state[old_coord]
        piece_type = piece // 4
        piece_color = piece % 4
        
        #reset the en passant square
        self.en_passant_square = -1
        #update castling rights and king position
        if piece_type == king:
            self.king_pos[piece_color] = new_coord
            self.right_to_castle_long[piece_color] = False
            self.right_to_castle_short[piece_color] = False
        if piece_type == rook:
            if old_coord % 10 == 1:
                self.right_to_castle_long[piece_color] = False
            if old_coord % 10 == 8:
                self.right_to_castle_short[piece_color] = False

        #check if the move is castling
        if piece_type == king and abs(new_coord % 10 - old_coord % 10) > 1:
            if new_coord % 10 > old_coord % 10:
                return self.castling(old_coord, old_coord // 10 * 10 + 8)
            if new_coord % 10 < old_coord % 10:
                return self.castling(old_coord, old_coord // 10 * 10 + 1)

        #check if the move is en passant
        if piece_type == pawn and old_coord % 10 != new_coord % 10 and self.state[new_coord] == 0:
            # self.score += material_score[pawn] * (-1) ** piece_color
            return self.en_passant(old_coord, new_coord)

        #change the en passant flag if pawn moved 2 squares
        if piece_type == pawn and abs(old_coord // 10 - new_coord // 10) == 2:
            #the en passant square is the piece where a pawn might capture en passant
            self.en_passant_square = (old_coord + new_coord) // 2

        #make the actual move and change the position score
        # self.score += material_score[self.state[new_coord] // 4] * (-1) ** piece_color
        self.state[old_coord] = 0
        self.state[new_coord] = piece
        
        #now we have to handle pawn promotion
        #the row of the 10x12 board on which we promote
        last_row = 2 if piece % 4 == white else 9
        if piece // 4 == pawn and new_coord // 10 == last_row:
            if promotion:
                new_piece = promotion * 4 + piece % 4
            else:
                new_piece = 0
            self.state[new_coord] = new_piece
        
        #toggle the color to move
        self.color_to_move = black if self.color_to_move == white else white
        return True #return success

    def en_passant(self, old_coord, new_coord):
        """
        handles the en passant move (moves pawn, deletes captured pawn)
        doesn't check that the move is in any way valid
        """
        self.state[old_coord // 10 * 10 + new_coord % 10] = 0
        self.state[new_coord] = self.state[old_coord]
        self.state[old_coord] = 0

        #toggle the color to move
        self.color_to_move = black if self.color_to_move == white else white
        return True #return success 
    
    def castling(self, king_coord, rook_coord):
        """
        moves the king and rook according to rules of castling
        (assumes that it was checked previously that the relevant
        squares are empty and not in check)
        """
        king_color = self.state[king_coord] % 4
        #move the king 2 squares in the direction of the rook,
        #and the rook near him, update king position
        if rook_coord < king_coord:
            self.state[king_coord - 2] = self.state[king_coord]
            self.state[king_coord - 1] = self.state[rook_coord]
            self.king_pos[king_color] = king_coord - 2
        else:
            self.state[king_coord + 2] = self.state[king_coord]
            self.state[king_coord + 1] = self.state[rook_coord]
            self.king_pos[king_color] = king_coord + 2
        #deletes the old instances of the king and rook
        self.state[king_coord] = 0
        self.state[rook_coord] = 0
        #toggle the color to move
        self.color_to_move = black if self.color_to_move == white else white 
        return True
