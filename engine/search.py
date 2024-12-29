import chess
from typing import Optional, Tuple
import time

class ChessEngine:
    def __init__(self, board, evaluator):
        self.board = board
        self.evaluator = evaluator
        self.nodes_searched = 0
        self.transposition_table = {}
        self.killer_moves = [[None] * 64 for _ in range(64)]  # Store good moves at each depth
        self.history_table = {}  # Store history heuristic scores

    def is_capture(self, move: chess.Move) -> bool:
        """Check if a move is a capture."""
        return self.board.is_capture(move)

    def move_ordering(self, moves, depth: int) -> list:
        """Order moves to improve alpha-beta pruning efficiency."""
        ordered_moves = []
        for move in moves:
            score = 0

            # Captures are examined first (MVV-LVA ordering)
            if self.is_capture(move):
                victim = self.board.piece_at(move.to_square)
                attacker = self.board.piece_at(move.from_square)
                if victim and attacker:
                    score = 10 * self.evaluator.PIECE_VALUES[victim.piece_type] - self.evaluator.PIECE_VALUES[attacker.piece_type]

            # Killer move bonus
            if self.killer_moves[depth][0] == move:
                score += 900000
            elif self.killer_moves[depth][1] == move:
                score += 800000

            # History heuristic bonus
            if move in self.history_table:
                score += self.history_table[move]

            ordered_moves.append((move, score))

        # Sort moves by score in descending order
        ordered_moves.sort(key=lambda x: x[1], reverse=True)
        return [move for move, _ in ordered_moves]

    def quiescence_search(self, alpha: int, beta: int, depth: int) -> int:
        """
        Quiescence search to handle tactical sequences.
        """
        stand_pat = self.evaluator.evaluate()

        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat
        if depth == -5:  # Maximum quiescence depth
            return stand_pat

        for move in self.board.legal_moves:
            if self.is_capture(move):
                self.board.push(move)
                score = -self.quiescence_search(-beta, -alpha, depth - 1)
                self.board.pop()

                if score >= beta:
                    return beta
                if score > alpha:
                    alpha = score

        return alpha

    def alpha_beta(self, depth, alpha, beta, maximizing_player):
        """
        Alpha-Beta pruning algorithm with mate detection.
        """
        # First, check for immediate checkmate
        if self.board.is_checkmate():
            return -20000 if maximizing_player else 20000  # If we're maximizing and find checkmate, we lost

        if depth == 0 or self.board.is_game_over():
            return self.evaluator.evaluate()

        if maximizing_player:
            max_eval = float("-inf")
            for move in self.board.legal_moves:
                self.board.push(move)
                eval = self.alpha_beta(depth - 1, alpha, beta, False)
                self.board.pop()

                # Adjust mate scores based on distance
                if eval > 19000:  # If we found a mate
                    eval -= 1  # Prefer shorter mates
                elif eval < -19000:  # If we're getting mated
                    eval += 1  # Prefer longer defenses

                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float("inf")
            for move in self.board.legal_moves:
                self.board.push(move)
                eval = self.alpha_beta(depth - 1, alpha, beta, True)
                self.board.pop()

                # Adjust mate scores based on distance
                if eval > 19000:  # If we found a mate
                    eval -= 1  # Prefer shorter mates
                elif eval < -19000:  # If we're getting mated
                    eval += 1  # Prefer longer defenses

                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval


    def find_best_move(self, depth):
        """
        Finds the best move using Alpha-Beta pruning with mate detection.
        """
        best_move = None
        best_eval = float("-inf")
        alpha = float("-inf")
        beta = float("inf")

        # Check for immediate mate in one
        for move in self.board.legal_moves:
            self.board.push(move)
            if self.board.is_checkmate():
                self.board.pop()
                return move
            self.board.pop()

        # Normal search if no immediate mate
        for move in self.board.legal_moves:
            self.board.push(move)
            eval = self.alpha_beta(depth - 1, alpha, beta, False)
            self.board.pop()

            # Update best move
            if eval > best_eval:
                best_eval = eval
                best_move = move
                alpha = max(alpha, eval)

        print(f"Depth {depth}: Best move {best_move}, Score: {best_eval}, Nodes: {self.nodes_searched}")
        return best_move

