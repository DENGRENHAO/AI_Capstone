import sys
import pygame
from MineSweeperGame import MineSweeperGame
from MineSweeperAI import MineSweeperPlayer

difficulty = 'easy'
initial_safe_cells_times = 1

if len(sys.argv) > 1:
    difficulty = sys.argv[1]
if len(sys.argv) > 2:
    initial_safe_cells_times = int(sys.argv[2])

if difficulty.lower() == "easy":
    game = MineSweeperGame(rows=9, cols=9, mines=10, initial_safe_cells_times=initial_safe_cells_times)
elif difficulty.lower() == "medium":
    game = MineSweeperGame(rows=16, cols=16, mines=25, initial_safe_cells_times=initial_safe_cells_times)
elif difficulty.lower() == "hard":
    game = MineSweeperGame(rows=16, cols=30, mines=99, initial_safe_cells_times=initial_safe_cells_times)

player = MineSweeperPlayer(game)

# print game board
# game.draw_board_debug()

# Game loop
running = True
first_click = True
step = 0
win_or_lose = None
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            # Exit the game loop when the window is closed
            running = False

    if not win_or_lose:
        if game.win():
            win_or_lose = "You win!"
        elif game.lose():
            win_or_lose = "You lose!"

    if not win_or_lose:
        step += 1
        move = player.game_move()
        # print(f"step: {step}, move: {move}")

    # pygame.time.wait(100)
    # Draw the board
    game.draw_board(win_or_lose)
    # Update the screen
    pygame.display.flip()
# Quit Pygame
pygame.quit()