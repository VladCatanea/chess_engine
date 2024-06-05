#TODO:
# - change the board to a more efficient way of storing the state - bitboard
# - improve the generating of next legal moves
# - improve the game over thing
# - implement FEN notation - add a feature where you can add a custom FEN to start from the position you want
# - draws by insufficient material, repetition or 50 move rule
# - look at importance of stalemate in the position evaluation of the AI
# - improve move notation so that check and checkmate are included
# - improve move notation when it is unclear (2 pieces can make that move)
# - implement quiescence search
#      -> (maybe) try to investigate a movelog to how on black's 1st move quiescence search can get to depth -20 
#      -> quiescence search with no other conditions seem to only converge because of the finite number of pieces, 
#         which might be a bit too slow (32 pieces to start with)
# - implement alpha beta pruning nega max
# - fix issue where computer generates an invalid move when being very close (1 move) to checkmate - only on depth 3 
# - *** a technique applied outside of the search for this is iterative deepening boosted by a transposition table, and possibly aspiration windows


import os
import sys
import random
import time
# from copy import deepcopy

import pygame
# import numpy as np
import chessAI
import Board
from move_gen_10x12 import *
from Move import nicer_print


os.environ['SDL_VIDEO_CENTERED'] = '1'
pygame.init()
random.seed()

#global constants:

#general:
WAITING_TIME = 50 #time to wait between loops in ms
MAX_FPS = 16 #maximum frames per second

#writings
WARNING_FONT_SIZE = 70
MOVELIST_FONT_SIZE = 25
MOVELIST_HORIZONTAL_SPACING = 100
MOVELIST_VERTICAL_SPACING = 30

#board:
MARGIN = 60
MOVELIST_WIDTH = 200
BOARD_SIZE = 480
square_size = BOARD_SIZE // 8
PIECE_MARGIN = 0
HIGHLIGHT_SIZE = 3

#colors:
background_brown = 139, 69, 19
background_grey = 36, 36, 36
shadow_black = 50, 30, 30
shadow_grey = 80, 80, 80
shadow_alpha = 150
background_color = 210, 105, 30
wood_black = 205, 133, 63
wood_white = 222, 184, 135
warning_red = 255, 0, 0
movelist_white = 255, 255, 255
selected_blue = 93, 221, 213
selected_alpha = 255
highlight_white = 255, 255, 255


#make a screen:
SCREEN_WIDTH = BOARD_SIZE + MOVELIST_WIDTH + 2 * MARGIN
SCREEN_HEIGHT = BOARD_SIZE + 2 * MARGIN
screen = pygame.display.set_mode([SCREEN_WIDTH, SCREEN_HEIGHT])
pygame.display.set_caption("Best Chess Ever")


class Writing:
    """Class to represent writings on screen"""
    def __init__(self, x, y, msg, color, font_size, centered=True):
        self.font = pygame.font.Font(None, font_size)
        self.image = self.font.render(msg, 1, color)
        self.rect = self.image.get_rect()
        if centered:
            self.rect.centerx = x
            self.rect.centery = y
        else:
            self.rect.x = x
            self.rect.y = y


class GameState:
    """class to hold the game state"""
    def __init__(self):
        self.board = Board.Board()
        self.board_matrix = matrix(self.board.state)
        self.log = [] #holds tupples of boards and the move played on that board
        self.update_legal_move_list()
        self.swapped = False

    def undo(self):
        """"undos the last move"""
        if len(self.log) > 0:
            self.board = self.log.pop()[0]
            self.board_matrix = matrix(self.board.state)
            self.update_legal_move_list()
            return True #success
        return False #failure

    def move(self, move):
        """
         Checks if a move is legal and then call the board move() method
        to make the move.
         If all is good, append the move and previous board to the log.
        """
        if move not in self.next_legal_moves:
            return False
        self.log.append((deepcopy(self.board), deepcopy(move)))
        promotion = 0 if len(move) < 3 else move[2]
        if self.board.move(move[0], move[1], promotion):
            #update next legal moves and the matrix
            self.board_matrix = matrix(self.board.state)
            self.update_legal_move_list()
            return True #success
        else:
            #eliminate the board from the log and return failure
            self.log.pop()
            return False

    def update_legal_move_list(self):
        """updates the list of legal moves. Called after the board state changes"""
        self.next_legal_moves = []
        # print('next legal moves')
        for move in gen_legal_moves(self.board):
            self.next_legal_moves.append(move)
            # print(nicer_print(move, self.board.state))

    def swap(self):
        """Toggles a flag which says if the board is seen from white or black perspective"""
        self.swapped = not self.swapped


class In_hand:
    """
    Class to hold the piece the player has taken to move
    and the place it was taken from.
    """
    def __init__(self):
        self.piece = 0
        self.taken_from = (-1, -1)

    def reset(self):
        """resets to no piece being in hand"""
        self.piece = 0
        self.taken_from  = (-1, -1)


def board_coord_to_window_coord(coord, swapped):
    """
    board coordinate (0, 0) is always the a8 square, but on the screen
    this can be top left or bottom left depending on whether you look 
    from white or black perspective.
    This function changes from coordinates in the board state to coordinates
    on the screen (window)
    """
    i, j = coord
    if swapped:
        y = MARGIN + PIECE_MARGIN + (7 - i) * square_size
        x = MARGIN + PIECE_MARGIN + (7 - j) * square_size
    else:
        y = MARGIN + PIECE_MARGIN + i * square_size
        x = MARGIN + PIECE_MARGIN + j * square_size
    return x, y

def window_coord_to_board_coord(pos, swapped):
    """
    board coordinate (0, 0) is always the a8 square, but on the screen
    this can be top left or bottom left depending on whether you look 
    from white or black perspective.
    This function changes from coordinates on the screen (window) to 
    coordinates in the board state
    """
    x, y = pos
    if swapped:
        i = 7 - (y - MARGIN)//square_size
        j = 7 - (x - MARGIN)//square_size
    else:
        i = (y - MARGIN)//square_size
        j = (x - MARGIN)//square_size
    return i, j

def array_to_matrix_coord(i):
    """
    changes from coordinates in a 120 nr array representation
    of a board to a more normal 8x8 matrix representation
    """
    return (i // 10 - 2, i % 10 - 1)

def matrix_to_array_coord(coord):
    i, j = coord
    return (i + 2) * 10 + j + 1


def draw_board():
    """Draws the chess board, including highlighting squares"""
    screen.fill(background_grey)
    
    #a black line that surrounds the board (for contrast)
    line = pygame.Rect(MARGIN - 2, MARGIN - 2, BOARD_SIZE + 3, BOARD_SIZE + 3)
    pygame.draw.rect(screen, black, line, 2)
    
    #fill the board black
    board_rect = pygame.Rect(MARGIN, MARGIN, BOARD_SIZE, BOARD_SIZE)
    pygame.draw.rect(screen, wood_black, board_rect)
    
    #draw the white squares
    for i in range(8):
        for j in range(8):
            if (i + j) % 2 == 0:
                x = MARGIN + square_size * i
                y = MARGIN + square_size * j
                square = pygame.Rect(x, y, square_size, square_size)
                pygame.draw.rect(screen, wood_white, square)

    #draw the selected square if any
    if in_hand.piece:
        i, j = in_hand.taken_from
        x, y = board_coord_to_window_coord((i, j), gs.swapped)
        square_surface = pygame.Surface((square_size, square_size))
        square_surface.set_alpha(selected_alpha)
        square_surface.fill(selected_blue)
        screen.blit(square_surface, (x, y))

    if in_hand.piece:
        #highlight the squares where it is possible to move our piece
        #ugly solution of using *end_coord_list* to not highlight a
        #pawn promotion move for every promotion choice which
        #would make the highlight opaque and ugly
        end_coord_list = []
        for move in gs.next_legal_moves:
            if array_to_matrix_coord(move[0]) == in_hand.taken_from:
                if array_to_matrix_coord(move[1]) in end_coord_list:
                    continue
                x, y = board_coord_to_window_coord(array_to_matrix_coord(move[1]), gs.swapped)
                square_surface = pygame.Surface((square_size, square_size))
                square_surface.set_alpha(shadow_alpha)
                square_surface.fill(shadow_grey)
                screen.blit(square_surface, (x, y))
                end_coord_list.append(array_to_matrix_coord(move[1]))

        #highlight the square where we might move our piece
        x, y = pygame.mouse.get_pos()
        x = x - MARGIN
        y = y - MARGIN
        #check that the mouse is on the board
        if (x in range(BOARD_SIZE) and y in range(BOARD_SIZE)):
            i = y // square_size
            j = x // square_size
            board_i = i #board coord, where (0, 0) is a8
            board_j = j
            if gs.swapped:
                board_i = 7 - i
                board_j = 7 - j
            highlighted_square = (board_i, board_j)
            if highlighted_square != in_hand.taken_from:
                y = MARGIN + square_size * i
                x = MARGIN + square_size * j
                square = pygame.Rect(x, y, square_size, square_size)
                pygame.draw.rect(screen, highlight_white, square, HIGHLIGHT_SIZE)

def load_piece(filename):
    """Makes a pygame image from the 'filename' PNG image"""
    piece_size = square_size - 2 * PIECE_MARGIN
    piece = pygame.image.load(os.path.join("pieces", filename))
    piece = pygame.transform.scale(piece, (piece_size, piece_size))
    return piece
    
def init_pieces():
    """
    Creates a piece_matrix which stores the images of the pieces,
    to be easier to get when they will be drawn on the screen.
    Also, creates the GameState and In_hand objects
    """
    global board
    global gs
    global in_hand
    global piece_matrix
    
    piece_matrix = [ [ None for _ in range(7) ] for _ in range(4) ]
    
    piece_matrix[black][pawn] = load_piece("black_pawn.png")
    piece_matrix[black][bishop] = load_piece("black_bishop.png")
    piece_matrix[black][knight] = load_piece("black_knight.png")
    piece_matrix[black][rook] = load_piece("black_rook.png")
    piece_matrix[black][queen] = load_piece("black_queen.png")
    piece_matrix[black][king] = load_piece("black_king.png")
    
    piece_matrix[white][pawn] = load_piece("white_pawn.png")
    piece_matrix[white][bishop] = load_piece("white_bishop.png")
    piece_matrix[white][knight] = load_piece("white_knight.png")
    piece_matrix[white][rook] = load_piece("white_rook.png")
    piece_matrix[white][queen] = load_piece("white_queen.png")
    piece_matrix[white][king] = load_piece("white_king.png")
    
    gs = GameState()
    in_hand = In_hand()

def draw_pieces():
    """Draws all the pieces on the screen"""

    board_matrix = gs.board_matrix
    #normal pieces on their squares first
    for i in range(8):
        for j in range(8):
            if board_matrix[i][j]:
                if not (i, j) == in_hand.taken_from:
                    name = board_matrix[i][j] // 4
                    color = board_matrix[i][j] % 4
                    x, y = board_coord_to_window_coord((i, j), gs.swapped)
                    piece = piece_matrix[color][name]
                    piece_rect = piece.get_rect()
                    piece_rect.move_ip(x, y)
                    screen.blit(piece, piece_rect)
    
    #the piece in out hand
    if in_hand.piece:
        name = in_hand.piece // 4
        color = in_hand.piece % 4
        x, y = pygame.mouse.get_pos()
        piece = piece_matrix[color][name]
        piece_rect = piece.get_rect()
        piece_rect.centerx = x
        piece_rect.centery = y
        screen.blit(piece, piece_rect)
    
def draw_warnings():
    """Draws the warnings check mate and draw"""
    for warning in warnings:
        screen.blit(warning.image, warning.rect)

def draw_movelog():
    """
    Draws a list of moves that happened in the game, on the right
    side of the board
    """
    #x0, y0 are the coordinates of the first move from the move log
    x0, y0 = MARGIN * 2 + BOARD_SIZE, MARGIN + movelist_scroll
    count = 0
    for entry in gs.log:
        board = entry[0]
        move = entry[1]
        #find out where the writing has to appear on screen
        row = count // 2
        column = count % 2
        x = x0 + column * MOVELIST_HORIZONTAL_SPACING
        y = y0 + row * MOVELIST_VERTICAL_SPACING
        count += 1
        #ignore moves that are outside the MOVELOG windowd
        if y < MARGIN or y > SCREEN_HEIGHT - MARGIN:
            continue
        #what writing has to appear (every row has to have the move nr)
        string = ''
        if column == 0:
            string += str(row + 1) + '. '
        string += nicer_print(move, board.state)
        #blit the actual writing on the screen
        move_writing = Writing(x, y, string, movelist_white, MOVELIST_FONT_SIZE, centered=False)
        screen.blit(move_writing.image, move_writing.rect)


def computer_turn():
    """
    Does what the computer should do on its turn:
    it chooses a move to be made by the computer.
    """
    next_moves = gs.next_legal_moves
    start_time = time.perf_counter()
    best_move = chessAI.find_best_move(gs.board, next_moves, depth=3)
    end_time = time.perf_counter()
    print('time:', end_time - start_time)
    if not gs.move(best_move):
        print('Computer provided invalid move:' + str(best_move) + ' / ' + nicer_print(best_move, gs.board.state))
    next_turn()

def change_pawn_menu(color, coord=(), always_queen=False):
    """
    It opens a menu for the player to chose with which piece
    to change his pawn that arrived on the last line.
    """
    if coord == ():
        pos = (MARGIN, MAGIN)
    else:
        pos = board_coord_to_window_coord(coord, gs.swapped)

    draw_board()
    draw_pieces()
    
    #we don't want the menu to get out of the screen
    if SCREEN_HEIGHT - pos[1] < 4 * square_size:
        inverted = True  
        pos = (pos[0], pos[1] - 3*square_size)
    else:
        inverted = False

    #shadow the rest of the board to focus on the pawn promotion menu
    shadow_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    shadow_surface.set_alpha(shadow_alpha)
    shadow_surface.fill(shadow_grey)
    screen.blit(shadow_surface, (0, 0))
    
    #create the pawn promotion menu
    menu_surface = pygame.Surface((square_size, 4 * square_size))
    menu_surface.fill(wood_white)
    screen.blit(menu_surface, pos)

    #draw the pieces
    x = pos[0]
    y = pos[1]
    piece_name_array = [queen, knight, rook, bishop]
    if inverted: #if the menu is on the bottom of the screen, it is inverted
        piece_name_array = piece_name_array[::-1]
    #draw the 4 piece choices
    for piece_name in piece_name_array:
        piece = piece_matrix[color][piece_name]
        piece_rect = piece.get_rect()
        piece_rect.move_ip(x, y)
        screen.blit(piece, piece_rect)
        y += square_size

    #update the screen
    pygame.display.update()

    #now loop until a piece is chosen
    while True:
        clock.tick(MAX_FPS) #to not exceed MAX_FPS
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                #if there is a click, return the piece the player clicked, 
                #or 0 if his click is not in the menu
                x, y = pygame.mouse.get_pos()
                if (y - pos[1]) // square_size < 0 or (y - pos[1]) // square_size > 3:
                    return 0
                if x < pos[0] or x > pos[0] + square_size:
                    return 0
                piece_name = piece_name_array[(y-pos[1])//square_size]
                return piece_name
            if event.type == pygame.QUIT: 
                sys.exit()

def move_piece(pos, action='grab'):
    """Function to start and finish a move by the player"""
    global in_hand
    
    x = pos[0] - MARGIN
    y = pos[1] - MARGIN
    #check that the click is on the board
    if not (x in range(BOARD_SIZE) and y in range(BOARD_SIZE)):
        in_hand.reset()
        return
    
    i, j = window_coord_to_board_coord(pos, gs.swapped)

    if action == 'grab':
        if in_hand.piece:
            return  #we already have another piece in hand
        if gs.board_matrix[i][j] == 0:
            return  #there is no piece here
        if gs.board_matrix[i][j] % 4 != gs.board.color_to_move:
            return # not the player's piece, so he can't move it
        in_hand.piece = gs.board_matrix[i][j]
        in_hand.taken_from = (i, j)
    
    elif action == 'let_down':
        if in_hand.piece:
            if gs.board_matrix[i][j]:
                capture = True
            else:
                capture = False
            move = matrix_to_array_coord(in_hand.taken_from), matrix_to_array_coord((i, j))
            #if the move is a pawn promotion we have to think about our promotion preference
            if in_hand.piece % 4 == white:
                last_rank = 0
            else:
                last_rank = 7
            if in_hand.piece // 4 == pawn and i == last_rank:
                promotion = change_pawn_menu(in_hand.piece % 4, (i, j))
                move = matrix_to_array_coord(in_hand.taken_from), matrix_to_array_coord((i, j)), promotion
            #make the move
            if gs.move(move):
                if (i, j) != in_hand.taken_from:
                    in_hand.reset()
                    next_turn()
            in_hand.reset()

def next_turn():
    """
    It does some checks: if the king is in check, 
    if there is check mate, or if there is a draw.
    """
    global warnings
    warnings = []
    
    color = gs.board.color_to_move
    opponent_color = black if color == white else white

    next_moves = gs.next_legal_moves

    if len(next_moves) == 0:
        if check(opponent_color, gs.board.state, gs.board.king_pos[color]):
            warnings.append(Writing(300, 300, 'CHECKMATE', warning_red, WARNING_FONT_SIZE))
            refresh()
            pygame.time.wait(2000)
            game_over()
        else:
            warnings.append(Writing( 300, 200, 'STALEMATE', warning_red, WARNING_FONT_SIZE))
            refresh()
            pygame.time.wait(2000)
            game_over()

    if swapping_board:
        gs.swap()
    
def game_over():
    """Called when the game ended. It just prints 'Game Over' and exits"""
    print('Game Over')
    sys.exit()

def refresh():
    """Draws the screen again"""
    draw_board()
    draw_pieces()
    draw_warnings()
    draw_movelog()
    #update the screen
    pygame.display.update()


def main():
    global warnings
    global player_color
    global swapping_board
    global clock
    global movelist_scroll
    init_pieces()
    warnings = [] #list of writings representing checkmate and stalemate. Mostly empty
    player_color = white #the color of the player in player vs computer game
    swapping_board = False #whether the board should swap perspective to the player who is next to move
    computer_game = True #whether the game is a player vs computer game
    movelist_scroll = 0
    if computer_game:
        swapping_board = False # no point swapping the board if there is only 1 real player
        #finds out the computer color and swap the board to player perspective
        if player_color == white: 
            computer_color = black
        else:
            gs.swap()
            computer_color = white

    clock = pygame.time.Clock()
    while True:
        clock.tick(MAX_FPS) #makes sure enough time passes each loop to not exceed MAX_FPS
        refresh() #draws everything
        #check if the computer has to supply a move
        player_turn = True if gs.board.color_to_move == player_color else False
        if computer_game and not player_turn:
            computer_turn()
            continue
        #now, this is a human player's turn:
        for event in pygame.event.get():
            
            #if mouse event, the player wants to move a piece
            if event.type == pygame.MOUSEBUTTONDOWN:
                move_piece(pygame.mouse.get_pos(), 'grab')
            if event.type == pygame.MOUSEBUTTONUP:
                move_piece(pygame.mouse.get_pos(), 'let_down')

            #if <u> is pressed, undo last move
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_u:
                    if gs.undo():
                        if swapping_board:
                            gs.swap()

            #enable user to scroll through move list using the UP and DOWN keyboard keys
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    movelist_scroll += MOVELIST_VERTICAL_SPACING
                elif event.key == pygame.K_DOWN:
                    movelist_scroll -= MOVELIST_VERTICAL_SPACING
            
            #so that the game quits when the user tries to close the window
            if event.type == pygame.QUIT: 
                sys.exit()


if __name__ == '__main__':
    main()



