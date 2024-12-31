import chess
import time
from engine.evaluate import  Evaluation
from typing import List,Tuple,Optional
class ChessEngine:
    def __init__(self, board: chess.Board):
        self.board = board
        self.evaluator = Evaluation(board)
        self.nodes_searched = 0
        self.MATE_SCORE = 20000
        self.PROMOTION_BONUS = 900
        self.CAPTURE_BASE_SCORE = 500

    def is_promising_check(self, move: chess.Move) -> bool:
        """
        Determine if a check is promising (leads to material gain or tactical advantage)
        """
        if not self.board.is_legal(move):
            return False

        self.board.push(move)
        is_promising = False

        if self.board.is_check():
            # Check if the opponent has very limited responses
            responses = list(self.board.legal_moves)
            if len(responses) <= 2:  # Limited escape squares
                is_promising = True
            else:
                # Check if we can win material after the check
                for response in responses:
                    self.board.push(response)
                    if self.board.is_valid():
                        attackers = len(list(self.board.attackers(not self.board.turn, response.to_square)))
                        defenders = len(list(self.board.attackers(self.board.turn, response.to_square)))
                        if attackers > defenders:
                            is_promising = True
                    self.board.pop()
                    if is_promising:
                        break

        self.board.pop()
        return is_promising

    def evaluate_capture(self, move: chess.Move) -> int:
        """
        Evaluate a capture move using MVV-LVA and static exchange evaluation
        """
        if not self.board.is_legal(move):
            return -1000  # Illegal move penalty

        victim = self.board.piece_type_at(move.to_square)
        attacker = self.board.piece_type_at(move.from_square)

        if not victim or not attacker:
            return 0

        # Basic MVV-LVA score
        score = self.evaluator.PIECE_VALUES[victim] - (self.evaluator.PIECE_VALUES[attacker] / 10)

        # Check if the capture is safe
        self.board.push(move)
        if self.board.is_valid():
            attackers = len(list(self.board.attackers(not self.board.turn, move.to_square)))
            defenders = len(list(self.board.attackers(self.board.turn, move.to_square)))
            if attackers > defenders:
                score //= 2  # Reduce score for unsafe captures
        self.board.pop()

        return score

    def order_moves(self, moves: List[chess.Move]) -> List[chess.Move]:
        """
        Order moves with emphasis on meaningful tactical moves
        """
        scored_moves = []

        for move in moves:
            if not self.board.is_legal(move):
                continue

            score = 0

            # Promotions
            if move.promotion:
                score += self.PROMOTION_BONUS + self.evaluator.PIECE_VALUES[move.promotion]

            # Captures
            if self.board.is_capture(move):
                score += self.CAPTURE_BASE_SCORE + self.evaluate_capture(move)

            # Checks (only if promising)
            self.board.push(move)
            if self.board.is_check() and self.is_promising_check(move):
                score += 400
            self.board.pop()

            # Pawn advances to 6th or 7th rank
            if self.board.piece_type_at(move.from_square) == chess.PAWN:
                to_rank = chess.square_rank(move.to_square)
                if (self.board.turn and to_rank in [5, 6]) or (not self.board.turn and to_rank in [1, 2]):
                    score += 50 * (to_rank if self.board.turn else 7 - to_rank)

            scored_moves.append((move, score))

        # Sort moves by score in descending order
        return [move for move, score in sorted(scored_moves, key=lambda x: x[1], reverse=True)]

    def alpha_beta(self, depth: int, alpha: float, beta: float, maximizing_player: bool,
                   start_time: float, time_limit: float) -> Tuple[float, Optional[chess.Move]]:
        """
        Enhanced alpha-beta search with focus on tactical play
        """
        if time.time() - start_time > time_limit:
            return 0, None

        if depth <= 0:
            return self.quiescence_search(alpha, beta, -2), None

        self.nodes_searched += 1

        if self.board.is_checkmate():
            return -self.MATE_SCORE if maximizing_player else self.MATE_SCORE, None

        if self.board.is_stalemate() or self.board.is_insufficient_material():
            return 0, None

        legal_moves = list(self.board.legal_moves)
        if not legal_moves:
            return 0, None

        best_move = None
        ordered_moves = self.order_moves(legal_moves)

        if maximizing_player:
            max_eval = float('-inf')
            for move in ordered_moves:
                if not self.board.is_legal(move):
                    continue

                self.board.push(move)
                eval_score, _ = self.alpha_beta(depth - 1, alpha, beta, False, start_time, time_limit)
                self.board.pop()

                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in ordered_moves:
                if not self.board.is_legal(move):
                    continue

                self.board.push(move)
                eval_score, _ = self.alpha_beta(depth - 1, alpha, beta, True, start_time, time_limit)
                self.board.pop()

                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move

    def quiescence_search(self, alpha: float, beta: float, depth: int) -> float:
        """
        Quiescence search focusing on captures and promising checks
        """
        stand_pat = self.evaluator.evaluate()

        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat
        if depth <= -4:
            return stand_pat

        legal_moves = list(self.board.legal_moves)
        moves = [move for move in legal_moves
                 if self.board.is_capture(move) or
                 (self.board.gives_check(move) and self.is_promising_check(move))]

        for move in self.order_moves(moves):
            if not self.board.is_legal(move):
                continue

            self.board.push(move)
            score = -self.quiescence_search(-beta, -alpha, depth - 1)
            self.board.pop()

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score

        return alpha

    def find_best_move(self, max_depth: int, time_limit: float = 5.0) -> Optional[chess.Move]:
        """
        Find best move using iterative deepening
        """
        self.nodes_searched = 0
        start_time = time.time()
        best_move = None

        try:
            for depth in range(1, max_depth + 1):
                score, move = self.alpha_beta(depth, float('-inf'), float('inf'),
                                              self.board.turn, start_time, time_limit)

                if move and self.board.is_legal(move):
                    best_move = move
                    print(f"Depth {depth}: Best move {move}, Score: {score}, Nodes: {self.nodes_searched}")

                if abs(score) > self.MATE_SCORE - 100:
                    break

                if time.time() - start_time > time_limit:
                    break

        except KeyboardInterrupt:
            pass

        # Return first legal move if no best move found
        if not best_move:
            legal_moves = list(self.board.legal_moves)
            if legal_moves:
                best_move = legal_moves[0]

        return best_move
