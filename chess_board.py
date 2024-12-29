import pygame
import chess
import chess.pgn
from datetime import datetime
from engine.search import ChessEngine
from engine.evaluate import Evaluation

class ChessBoard:
    def __init__(self, board):
        self.board = board
        self.square_size = 80
        self.window_size = self.square_size * 8
        self.screen = None
        self.font = None
        self.engine = ChessEngine(board, Evaluation(board))
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
                image = pygame.image.load(filename)
                # Scale image to fit square size
                image = pygame.transform.scale(image, (self.square_size, self.square_size))
                self.piece_images[f"{color}{piece}"] = image

    def draw_board(self):
        """
        Draws the chessboard on the screen.
        """
        colors = [pygame.Color("white"), pygame.Color("gray")]
        for rank in range(8):
            for file in range(8):
                color = colors[(rank + file) % 2]
                pygame.draw.rect(
                    self.screen,
                    color,
                    pygame.Rect(file * self.square_size, rank * self.square_size, self.square_size, self.square_size)
                )

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

                # Calculate position
                file = chess.square_file(square)
                rank = 7 - chess.square_rank(square)  # Flip rank for correct orientation

                x = file * self.square_size
                y = rank * self.square_size

                self.screen.blit(self.piece_images[piece_key], (x, y))

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

            # Append to PGN file
            with open(filename, "a") as pgn_file:
                print(self.game, file=pgn_file)
                print("\n", file=pgn_file)  # Add blank line between games

            print(f"Game saved to {filename}")

        except Exception as e:
            print(f"Error saving game: {e}")

    def start_self_play(self, depth=3):
        """
        Starts a game where the engine plays against itself.
        """
        pygame.init()
        self.screen = pygame.display.set_mode((self.window_size, self.window_size))
        pygame.display.set_caption("Chess Engine Self-Play")
        self.font = pygame.font.Font(None, 36)

        running = True
        move_count = 1
        clock = pygame.time.Clock()

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.draw_board()
            self.draw_pieces()
            pygame.display.flip()

            if not self.board.is_game_over():
                print(f"Move {move_count}: Engine is thinking at depth {depth}...")
                best_move = self.engine.find_best_move(depth)
                print(f"Move {move_count}: Best move: {best_move}")

                # Add move to game
                self.node = self.node.add_variation(best_move)

                self.board.push(best_move)
                move_count += 1
            else:
                result_text = f"Game Over: {self.board.result()}"
                print(result_text)
                # Save game when it's over
                self.save_game()
                running = False

            clock.tick(60)  # Limit to 60 FPS

        pygame.quit()

    def export_to_chess_com_format(self, filename="games/chess_com_game.txt"):
        """
        Export the game in a format that can be imported to chess.com
        """
        try:
            # Create directory if it doesn't exist
            import os
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            with open(filename, "w") as f:
                # Write moves in chess.com format
                moves = []
                current_node = self.game
                while current_node.variations:
                    current_node = current_node.variation(0)
                    moves.append(current_node.move.uci())

                # Join moves with commas
                f.write(",".join(moves))

            print(f"Game exported for chess.com to {filename}")

        except Exception as e:
            print(f"Error exporting game: {e}")

    def save_game_with_timestamp(self):
        """
        Save the game with a timestamp in the filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"games/game_{timestamp}.pgn"
        self.save_game(filename)

    def add_comment(self, comment: str):
        """
        Add a comment to the current position
        """
        self.node.comment = comment

    def add_evaluation(self, eval_score: float):
        """
        Add evaluation score as a comment
        """
        self.node.comment = f"Evaluation: {eval_score}"


if __name__ == "__main__":
    board = chess.Board()
    chess_board_gui = ChessBoard(board)
    chess_board_gui.start_self_play(depth=3)
    chess_board_gui.export_to_chess_com_format()
