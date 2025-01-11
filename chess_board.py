import pygame
import chess
import chess.pgn
from datetime import datetime
from engine.search import ChessEngine
import time
import os

class ChessBoard:
    def __init__(self, board):
        self.board = board
        self.square_size = 80
        self.board_size = self.square_size * 8
        self.info_height = 40
        self.history_width = 200
        self.window_size = (self.board_size + self.history_width, self.board_size + self.info_height)
        self.screen = None
        self.font = None
        self.engine = ChessEngine(board)
        self.depth = 4
        self.thinking_start_time = None
        self.move_history = []

        # Game information
        self.game = chess.pgn.Game()
        self.game.headers["Event"] = "Computer Self-Play"
        self.game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
        self.game.headers["White"] = "ChessEngine (White)"
        self.game.headers["Black"] = "ChessEngine (Black)"
        self.game.headers["Result"] = "*"

        # IMPORTANT for non-standard positions:
        self.game.headers["SetUp"] = "1"
        self.game.headers["FEN"] = self.board.fen()

        self.node = self.game

        # Colors
        self.LIGHT_SQUARE = pygame.Color("white")
        self.DARK_SQUARE = pygame.Color(100, 100, 100)
        self.HIGHLIGHT_COLOR = pygame.Color(255, 255, 0, 50)  # Yellow with transparency
        self.BACKGROUND_COLOR = pygame.Color("gray20")
        self.TEXT_COLOR = pygame.Color("white")

        # Load piece images
        self.piece_images = {}
        self.load_pieces()

    def load_pieces(self):
        """Loads and scales piece images."""
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
        """Draws the chessboard with coordinates."""
        self.screen.fill(self.BACKGROUND_COLOR)

        # Draw board squares
        for rank in range(8):
            for file in range(8):
                color = self.LIGHT_SQUARE if (rank + file) % 2 == 0 else self.DARK_SQUARE
                pygame.draw.rect(
                    self.screen,
                    color,
                    pygame.Rect(file * self.square_size, rank * self.square_size,
                                self.square_size, self.square_size)
                )

        # Draw coordinates
        for i in range(8):
            # File letters
            text = chr(ord('a') + i)
            text_surface = self.font.render(text, True, self.TEXT_COLOR)
            self.screen.blit(text_surface, (i * self.square_size + 5, self.board_size - 20))

            # Rank numbers
            text = str(8 - i)
            text_surface = self.font.render(text, True, self.TEXT_COLOR)
            self.screen.blit(text_surface, (5, i * self.square_size + 5))

    def highlight_last_move(self):
        """Highlights the squares of the last move."""
        if self.board.move_stack:
            last_move = self.board.peek()
            for square in [last_move.from_square, last_move.to_square]:
                file = chess.square_file(square)
                rank = 7 - chess.square_rank(square)
                rect = pygame.Rect(
                    file * self.square_size,
                    rank * self.square_size,
                    self.square_size,
                    self.square_size
                )
                pygame.draw.rect(self.screen, self.HIGHLIGHT_COLOR, rect)

    def draw_pieces(self):
        """Draws the chess pieces on the board."""
        piece_mapping = {
            'P': 'wp', 'N': 'wn', 'B': 'wb', 'R': 'wr', 'Q': 'wq', 'K': 'wk',
            'p': 'bp', 'n': 'bn', 'b': 'bb', 'r': 'br', 'q': 'bq', 'k': 'bk'
        }

        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                piece_key = piece_mapping[piece.symbol()]
                file = chess.square_file(square)
                rank = 7 - chess.square_rank(square)
                x = file * self.square_size
                y = rank * self.square_size
                self.screen.blit(self.piece_images[piece_key], (x, y))

    def draw_info(self, move_count):
        """Draws move information, evaluation, and thinking time."""
        info_rect = pygame.Rect(0, self.board_size, self.window_size[0], self.info_height)
        pygame.draw.rect(self.screen, self.BACKGROUND_COLOR, info_rect)

        # Move count and turn
        turn_text = f"Move {move_count} - {'White' if self.board.turn else 'Black'} to move"
        text_surface = self.font.render(turn_text, True, self.TEXT_COLOR)
        text_rect = text_surface.get_rect(center=(self.board_size//2, self.board_size + self.info_height//2))
        self.screen.blit(text_surface, text_rect)

        # Evaluation
        eval_text = f"Eval: {self.engine.evaluator.evaluate():.2f}"
        eval_surface = self.font.render(eval_text, True, self.TEXT_COLOR)
        self.screen.blit(eval_surface, (10, self.board_size + 10))

        # Thinking time
        if self.thinking_start_time:
            thinking_time = time.time() - self.thinking_start_time
            time_text = f"Time: {thinking_time:.1f}s"
            time_surface = self.font.render(time_text, True, self.TEXT_COLOR)
            self.screen.blit(time_surface, (self.board_size - 100, self.board_size + 10))

        # Current depth
        depth_text = f"Depth: {self.depth}"
        depth_surface = self.font.render(depth_text, True, self.TEXT_COLOR)
        self.screen.blit(depth_surface, (self.board_size - 200, self.board_size + 10))

    def draw_game_state(self):
        """Draws game state messages (checkmate, stalemate, etc.)."""
        if self.board.is_checkmate():
            state = "Checkmate!"
        elif self.board.is_stalemate():
            state = "Stalemate"
        elif self.board.is_insufficient_material():
            state = "Draw - Insufficient Material"
        else:
            return

        text_surface = self.font.render(state, True, pygame.Color("red"))
        text_rect = text_surface.get_rect(center=(self.board_size//2, self.board_size + self.info_height//2))
        self.screen.blit(text_surface, text_rect)

    def handle_input(self):
        """Handles keyboard input for depth control."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.depth = min(self.depth + 1, 6)
                elif event.key == pygame.K_DOWN:
                    self.depth = max(self.depth - 1, 1)
        return True

    def save_game(self, filename="games/game.pgn"):
        """Saves the game in PGN format."""
        try:
            # Update result if game is over
            if self.board.is_game_over():
                if self.board.is_checkmate():
                    # If board.turn is True, that means White to move, so White got checkmated -> black wins -> 0-1
                    self.game.headers["Result"] = "0-1" if self.board.turn else "1-0"
                else:
                    self.game.headers["Result"] = "1/2-1/2"

            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, "a") as pgn_file:
                exporter = chess.pgn.FileExporter(pgn_file)
                self.game.accept(exporter)
                # Extra blank line for readability
                print("\n", file=pgn_file)

            print(f"Game saved to {filename}")

        except Exception as e:
            print(f"Error saving game: {e}")

    def export_to_chess_com_pgn(self, filename="games/chess_com_game.pgn"):
        """Exports the game in chess.com-compatible format."""
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            # Format headers
            headers = (
                f'[Event "{self.game.headers["Event"]}"]\n'
                f'[Site "Local Engine Game"]\n'
                f'[Date "{self.game.headers["Date"]}"]\n'
                f'[Round "1"]\n'
                f'[White "{self.game.headers["White"]}"]\n'
                f'[Black "{self.game.headers["Black"]}"]\n'
                f'[Result "{self.game.headers["Result"]}"]\n'
                f'[TimeControl "-"]\n'
                f'[Variant "Standard"]\n'
                f'[ECO "?"]\n'
                f'[Opening "?"]\n'
                # Because we start from a custom FEN:
                f'[SetUp "1"]\n'
                f'[FEN "{self.board.fen()}"]\n'
            )

            # Format moves with proper numbering
            moves_text = ""
            node = self.game
            move_number = 1
            while node.variations:
                node = node.variation(0)
                # In PGN notation, we prepend the move number on White's move
                if node.parent.turn() == chess.WHITE:
                    moves_text += f"{move_number}. "
                moves_text += f"{node.san()} "
                if node.parent.turn() == chess.BLACK:
                    move_number += 1

            # Add final result at end
            moves_text += f" {self.game.headers['Result']}"

            with open(filename, "w") as pgn_file:
                pgn_file.write(headers + "\n" + moves_text + "\n\n")

            print(f"Game exported to {filename} in chess.com format")

        except Exception as e:
            print(f"Error exporting game: {e}")

    def draw_move_history(self):
        """Draws the move history panel with proper move formatting."""
        history_rect = pygame.Rect(self.board_size, 0, self.history_width, self.board_size)
        pygame.draw.rect(self.screen, self.BACKGROUND_COLOR, history_rect)

        # Draw border
        pygame.draw.rect(self.screen, pygame.Color("gray50"), history_rect, 1)

        # Draw "Move History" header
        header = self.font.render("Move History", True, self.TEXT_COLOR)
        header_rect = header.get_rect(center=(self.board_size + self.history_width//2, 20))
        self.screen.blit(header, header_rect)

        # Draw moves from stored history
        y = 50
        for i in range(0, len(self.move_history), 2):
            # White's move
            move_num = i // 2 + 1
            move_text = f"{move_num}. {self.move_history[i]}"
            text_surface = self.font.render(move_text, True, self.TEXT_COLOR)
            self.screen.blit(text_surface, (self.board_size + 10, y))

            # Black's move (if exists)
            if i + 1 < len(self.move_history):
                text_surface = self.font.render(self.move_history[i + 1], True, self.TEXT_COLOR)
                self.screen.blit(text_surface, (self.board_size + 80, y))

            y += 25
            if y >= self.board_size - 30:
                break

    def start_self_play(self, depth=4):
        """Starts a game where the engine plays against itself."""
        self.depth = depth
        pygame.init()
        self.screen = pygame.display.set_mode(self.window_size)
        pygame.display.set_caption("Chess Engine Self-Play")
        self.font = pygame.font.Font(None, 24)

        running = True
        move_count = 1
        clock = pygame.time.Clock()
        TARGET_FPS = 60

        while running:
            clock.tick(TARGET_FPS)
            running = self.handle_input()

            self.draw_board()
            self.highlight_last_move()
            self.draw_pieces()
            self.draw_info(move_count)
            self.draw_move_history()
            self.draw_game_state()
            pygame.display.flip()

            if not self.board.is_game_over():
                print(f"Move {move_count}: Engine thinking at depth {self.depth}...")
                self.thinking_start_time = time.time()
                best_move = self.engine.find_best_move(self.depth)
                self.thinking_start_time = None

                try:
                    # Get SAN notation before making the move
                    san_move = self.board.san(best_move)
                    self.move_history.append(san_move)

                    print(f"Move {move_count}: {san_move}")
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
                self.export_to_chess_com_pgn()
                time.sleep(3)
                running = False

        pygame.quit()


if __name__ == "__main__":
    # Test position
    fen = "4r3/1R6/8/p2Rn1p1/2P2k2/P5pP/5P2/6K1 b - - 0 41"
    board = chess.Board(fen=fen)
    chess_board_gui = ChessBoard(board)
    chess_board_gui.start_self_play(depth=7)
