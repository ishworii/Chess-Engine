# search.py

import chess
import time
from typing import Tuple, Optional
import random
from engine.evaluate import Evaluation

class SearchTimeout(Exception):
    """Custom exception to handle search timeout."""
    pass

class ChessEngine:
    def __init__(self, board: chess.Board, engine_color: chess.Color = chess.WHITE):
        self.board = board
        self.evaluator = Evaluation(board)
        self.nodes_searched = 0
        self.MATE_SCORE = 1000000
        self.engine_color = engine_color
        self.best_move = None

    def negamax(self, depth: int, alpha: float, beta: float, color: int, start_time: float, time_limit: float, is_root: bool = False) -> float:
        """
        Negamax search with alpha-beta pruning.
        """
        # Time check
        if (time.time() - start_time) > time_limit:
            raise SearchTimeout

        # Check current position
        if self.board.is_checkmate():
            return -self.MATE_SCORE
        if self.board.is_stalemate() or self.board.is_insufficient_material():
            return 0

        # If at leaf node, return evaluation
        if depth == 0:
            return color * self.evaluator.evaluate()

        self.nodes_searched += 1
        max_score = -float('inf')
        best_local_move = None

        # Search through all legal moves
        for move in self.board.legal_moves:
            # Make move
            self.board.push(move)

            # If this move leads to checkmate, we found mate!
            if self.board.is_checkmate():
                score = self.MATE_SCORE
            else:
                # Otherwise, continue searching
                score = -self.negamax(depth - 1, -beta, -alpha, -color, start_time, time_limit)

            # Unmake move
            self.board.pop()

            if score > max_score:
                max_score = score
                best_local_move = move

            alpha = max(alpha, score)
            if alpha >= beta:
                break

        # If we're at root node, store the best move
        if is_root and best_local_move:
            self.best_move = best_local_move

        return max_score

    def find_best_move_iterative_deepening(self, max_depth: int, time_limit: float) -> Optional[chess.Move]:
        """
        Iterative deepening to find the best move within the time limit.
        """
        self.nodes_searched = 0
        self.best_move = None
        start_time = time.time()

        try:
            for depth in range(1, max_depth + 1):
                score = self.negamax(
                    depth=depth,
                    alpha=-float('inf'),
                    beta=float('inf'),
                    color=1 if self.engine_color == chess.WHITE else -1,
                    start_time=start_time,
                    time_limit=time_limit,
                    is_root=True
                )

                elapsed = time.time() - start_time
                print(f"[Depth {depth}] Score: {score}, Best Move: {self.best_move}, "
                      f"Nodes: {self.nodes_searched}, Time: {elapsed:.2f}s")

                # If we found a mate, no need to search deeper
                if abs(score) >= self.MATE_SCORE - 100:
                    break

        except SearchTimeout:
            print(f"Search stopped due to timeout.")

        if self.best_move is None:
            # Fallback to a random move if no move was found
            legal_moves = list(self.board.legal_moves)
            if legal_moves:
                self.best_move = random.choice(legal_moves)

        return self.best_move

    def find_best_move(self, max_depth: int, time_limit: float = 60.0) -> Optional[chess.Move]:
        """
        Public method to find the best move using iterative deepening.
        """
        return self.find_best_move_iterative_deepening(max_depth, time_limit)


# Test code
if __name__ == "__main__":
    # Test position with mate in 1
    fen = "4r3/8/8/8/8/8/3P4/4K3 b - - 0 1"  # Black to move, Re8-e1 is mate
    board = chess.Board(fen)

    print("Initial position:")
    print(board)

    engine = ChessEngine(board, chess.BLACK)
    best_move = engine.find_best_move(max_depth=3, time_limit=5.0)

    print("\nBest move found:", best_move)
    if best_move:
        board.push(best_move)
        print("\nPosition after best move:")
        print(board)
        if board.is_checkmate():
            print("Checkmate!")
