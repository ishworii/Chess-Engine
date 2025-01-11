import pygame
import chess
import chess.pgn
from datetime import datetime
from engine.search import ChessEngine
import time

class ChessBoard:
    def __init__(self, board):
        self.board = board
        self.square_size = 80
        self.board_size = self.square_size * 8
        self.info_height = 40  # Height for move information
        self.window_size = (self.board_size, self.board_size + self.info_height)
        self.screen = None
        self.font = None
        self.engine = ChessEngine(board)
        # Add game information
        self.game = chess.pgn.Game()
        self.game.headers["Event"] = "Computer Self-Play"
        self.game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
        self.game.headers["White"] = "ChessEngine (White)"
        self.game.headers["Black"] = "ChessEngine (Black)"
        self.game.headers["Result"] = "*"
        self.node = self.game
        # Load piece images
        self.piece_images = {}
        self.load_pieces()

    def load_pieces(self):
        """
        Loads and scales piece images.
        """
        pieces = ['p', 'n', 'b', 'r', 'q', 'k']
        colors = ['w', 'b']
        for piece in pieces:
            for color in colors:
                filename = f"images/{color}{piece}.png"
                try:
                    image = pygame.image.load(filename)
                    image = pygame.transform.scale(image, (self.square_size, self.square_size))
                    self.piece_images[f"{color}{piece}"] = image
                except pygame.error as e:
                    print(f"Error loading image {filename}: {e}")

    def draw_board(self):
        """
        Draws the chessboard on the screen.
        """
        # Fill background
        self.screen.fill(pygame.Color("gray20"))

        # Draw board squares
        colors = [pygame.Color("white"), pygame.Color(100, 100, 100)]  # Lighter gray for dark squares
        for rank in range(8):
            for file in range(8):
                color = colors[(rank + file) % 2]
                pygame.draw.rect(
                    self.screen,
                    color,
                    pygame.Rect(file * self.square_size, rank * self.square_size, self.square_size, self.square_size)
                )

        # Draw coordinates
        coord_color = pygame.Color("white")
        for i in range(8):
            # Draw file letters
            text = chr(ord('a') + i)
            text_surface = self.font.render(text, True, coord_color)
            self.screen.blit(text_surface, (i * self.square_size + 5, self.board_size - 20))

            # Draw rank numbers
            text = str(8 - i)
            text_surface = self.font.render(text, True, coord_color)
            self.screen.blit(text_surface, (5, i * self.square_size + 5))

    def draw_pieces(self):
        """
        Draws the chess pieces on the board.
        """
        piece_mapping = {
            'P': 'wp', 'N': 'wn', 'B': 'wb', 'R': 'wr', 'Q': 'wq', 'K': 'wk',
            'p': 'bp', 'n': 'bn', 'b': 'bb', 'r': 'br', 'q': 'bq', 'k': 'bk'
        }

        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                piece_symbol = piece.symbol()
                piece_key = piece_mapping[piece_symbol]

                file = chess.square_file(square)
                rank = 7 - chess.square_rank(square)

                x = file * self.square_size
                y = rank * self.square_size

                self.screen.blit(self.piece_images[piece_key], (x, y))

    def draw_info(self, move_count):
        """
        Draws move information and current turn at the bottom.
        """
        info_rect = pygame.Rect(0, self.board_size, self.window_size[0], self.info_height)
        pygame.draw.rect(self.screen, pygame.Color("gray20"), info_rect)

        # Draw move count and turn
        turn_text = f"Move {move_count} - {'White' if self.board.turn else 'Black'} to move"
        text_surface = self.font.render(turn_text, True, pygame.Color("white"))
        text_rect = text_surface.get_rect(center=(self.window_size[0]//2, self.board_size + self.info_height//2))
        self.screen.blit(text_surface, text_rect)

    def save_game(self, filename="games/game.pgn"):
        """
        Save the game in PGN format.
        """
        try:
            # Update result if game is over
            if self.board.is_game_over():
                if self.board.is_checkmate():
                    self.game.headers["Result"] = "0-1" if self.board.turn else "1-0"
                else:
                    self.game.headers["Result"] = "1/2-1/2"

            # Create directory if it doesn't exist
            import os
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            # Save game to PGN file
            with open(filename, "a") as pgn_file:
                exporter = chess.pgn.FileExporter(pgn_file)
                self.game.accept(exporter)
                print("\n", file=pgn_file)  # Add blank line between games

            print(f"Game saved to {filename}")

        except Exception as e:
            print(f"Error saving game: {e}")

    def start_self_play(self, depth=3):
        """
        Starts a game where the engine plays against itself.
        """
        pygame.init()
        self.screen = pygame.display.set_mode(self.window_size)
        pygame.display.set_caption("Chess Engine Self-Play")
        self.font = pygame.font.Font(None, 24)

        running = True
        move_count = 1
        clock = pygame.time.Clock()

        while running:
            time.sleep(0.1)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.draw_board()
            self.draw_pieces()
            self.draw_info(move_count)
            pygame.display.flip()

            if not self.board.is_game_over():
                print(f"Move {move_count}: Engine is thinking at depth {depth}...")
                best_move = self.engine.find_best_move(depth)

                try:
                    san_move = self.board.san(best_move)
                    print(f"Move {move_count}: Best move: {san_move}")

                    # Add move to game
                    self.node = self.node.add_variation(best_move)
                    self.board.push(best_move)
                    move_count += 1
                except ValueError as e:
                    print(f"Invalid move generated: {e}")
                    running = False
            else:
                result_text = f"Game Over: {self.board.result()}"
                print(result_text)
                self.save_game()
                running = False

            clock.tick(60)
        time.sleep(5)
        pygame.quit()

if __name__ == "__main__":
    fen = "r4r1k/pb2q1pp/np6/2p1N3/2Qp1P2/4PR2/P1P3PP/1R4K1 w - - 2 22"
    board = chess.Board(fen=fen)
    chess_board_gui = ChessBoard(board)
    chess_board_gui.start_self_play(depth=5)
    # chess_board_gui.export_to_chess_com_pgn()
