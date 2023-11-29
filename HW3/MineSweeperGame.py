import math
import pygame
import random

# Define some colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

CELL_SIZE = 40

class MineSweeperGame():
    def __init__(self, rows, cols, mines, initial_safe_cells_times):
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.width = self.cols * CELL_SIZE
        self.height = self.rows * CELL_SIZE
        self.board = []
        self.initial_safe_cells_times = initial_safe_cells_times
        self.create_board()
        self.generate_mine()
        self.screen = self.initialize_pygame()
        self.initial_random_safes = self.get_initial_safe_cells()

    def initialize_pygame(self):
        # Initialize Pygame
        pygame.init()
        pygame.display.set_caption("Minesweeper")
        screen = pygame.display.set_mode((self.width, self.height))
        return screen
    
    def create_board(self):
        # Create the game board
        for row in range(self.rows):
            self.board.append([])
            for col in range(self.cols):
                self.board[row].append({'mine': False, 'revealed': False, 'marked': False})

    def generate_mine(self):
        # Add some random mines
        mine_count = 0
        while mine_count < self.mines:
            row = random.randint(0, self.rows-1)
            col = random.randint(0, self.cols-1)
            if not self.board[row][col]['mine']:
                self.board[row][col]['mine'] = True
                mine_count += 1

    def get_initial_safe_cells(self):
        num_initial_safe_cells = round(math.sqrt(self.rows * self.cols)) * self.initial_safe_cells_times
        safe_cells = set()
        while len(safe_cells) < num_initial_safe_cells:
            row = random.randint(0, self.rows - 1)
            col = random.randint(0, self.cols - 1)
            if not self.board[row][col]['mine'] and (row, col) not in safe_cells:
                safe_cells.add((row, col))
        return safe_cells

    def get_adjacent_mines(self, row, col):
        count = 0
        for r in range(max(row-1, 0), min(row+2, self.rows)):
            for c in range(max(col-1, 0), min(col+2, self.cols)):
                if self.board[r][c]['mine']:
                    count += 1
        return count

    def draw_board(self, win_or_lose=None):
        self.screen.fill(GRAY)
        for row in range(self.rows):
            for col in range(self.cols):
                x = col * CELL_SIZE
                y = row * CELL_SIZE
                cell = self.board[row][col]
                if not cell['revealed']:
                    color = WHITE
                    if cell['marked']:
                        pygame.draw.rect(self.screen, RED, (x, y, CELL_SIZE, CELL_SIZE))
                else:
                    color = BLACK
                    if cell['mine']:
                        pygame.draw.circle(self.screen, BLACK, (x+CELL_SIZE//2, y+CELL_SIZE//2), CELL_SIZE//4)
                    else:
                        count = self.get_adjacent_mines(row, col)
                        if count >= 0:
                            font = pygame.font.SysFont(None, CELL_SIZE//2)
                            text = font.render(str(count), True, BLACK)
                            self.screen.blit(text, (x+CELL_SIZE//4, y+CELL_SIZE//4))
                pygame.draw.rect(self.screen, color, (x, y, CELL_SIZE, CELL_SIZE), 1)
        if win_or_lose is not None:
            font = pygame.font.SysFont(None, 50)
            text = font.render(win_or_lose, True, BLUE)
            self.screen.blit(text, (self.width/2 - text.get_width()/2, self.height/2 - text.get_height()/2))
    
    # draw board
    # X is for mine == True
    # U is for revealed == False
    # M is for marked == True
    # 0-8 is for mines number from get_adjacent_mines(row, col)
    def draw_board_debug(self):
        for row in range(self.rows):
            for col in range(self.cols):
                cell = self.board[row][col]
                if cell['mine']:
                    print('X', end=' ')
                elif cell['revealed']:
                    print(self.get_adjacent_mines(row, col), end=' ')
                elif cell['marked']:
                    print('M', end=' ')
                else:
                    print('U', end=' ')
            print()
    
    def mark_safe(self, row, col):
        cell = self.board[row][col]
        if not cell['revealed']:
            cell['revealed'] = True    
    
    def mark_mine(self, row, col):
        cell = self.board[row][col]
        if not cell['marked']:
            cell['marked'] = True

    def get_unmarked_neighbors_and_mine_count(self, row, col):
        neighbors = []
        mine_count = 0
        for r in range(max(row-1, 0), min(row+2, self.rows)):
            for c in range(max(col-1, 0), min(col+2, self.cols)):
                if (r != row or c != col): 
                    if not self.board[r][c]['revealed'] and not self.board[r][c]['marked']:
                        if self.board[r][c]['mine']:
                            mine_count += 1
                        neighbors.append((r, c))
        return neighbors, mine_count
    
    def lose(self):
        for row in range(self.rows):
            for col in range(self.cols):
                cell = self.board[row][col]
                if cell['revealed'] and cell['mine']:
                    return True
        return False
    
    def win(self):
        marked_mines = 0
        for row in range(self.rows):
            for col in range(self.cols):
                cell = self.board[row][col]
                if cell['marked'] and cell['mine']:
                    marked_mines += 1
                if not cell['revealed'] and not cell['marked']:
                    return False
        if marked_mines != self.mines:
            return False
        return True
