import chess
import chess.polyglot
import time
import random
from engine.evaluate import Evaluation
from enum import Enum
from typing import Optional, Dict, List


class SearchTimeout(Exception):
    """Custom exception to handle search timeout."""
    pass

class NodeType(Enum):
    """Node types for transposition table entries"""
    EXACT = 0    # Exact score
    ALPHA = 1    # Upper bound
    BETA = 2     # Lower bound

class TranspositionEntry:
    """Entry in the transposition table"""
    def __init__(self, key: int, depth: int, score: float, node_type: NodeType, best_move: Optional[chess.Move]):
        self.key = key
        self.depth = depth
        self.score = score
        self.node_type = node_type
        self.best_move = best_move

class ChessEngine:
    """
    Chess engine using minimax with alpha-beta pruning.
    """
    def __init__(self, board: chess.Board, engine_color: chess.Color = chess.WHITE):
        self.board = board
        self.evaluator = Evaluation(board)
        self.nodes_searched = 0
        self.MATE_SCORE = 1000000
        self.engine_color = engine_color
        self.best_move = None

        # Initialize transposition table
        self.tt_size = 1000000  # Size of transposition table
        self.tt: Dict[int, TranspositionEntry] = {}

        # Initialize killer moves
        self.max_depth = 100  # Maximum search depth
        self.killer_moves: List[List[Optional[chess.Move]]] = [[None, None] for _ in range(self.max_depth)]

    def get_ordered_moves(self, tt_move: Optional[chess.Move] = None, depth: int = 0) -> list:
        """Enhanced move ordering with winning position consideration"""
        moves = []
        material_eval = self.evaluator.evaluate_material()
        is_winning = abs(material_eval) > 200
        is_winning_side = (material_eval > 0) == (self.board.turn == chess.WHITE)

        for move in self.board.legal_moves:
            score = 0

            # TT move gets highest priority
            if tt_move and move == tt_move:
                score += 20000

            # Killer moves
            elif depth < len(self.killer_moves):
                if move == self.killer_moves[depth][0]:
                    score += 15000
                elif move == self.killer_moves[depth][1]:
                    score += 14000

            # Score move considering position
            score += self.score_move(move, is_winning and is_winning_side)

            moves.append((score, move))

        moves.sort(key=lambda x: x[0], reverse=True)
        return [move for score, move in moves]

    def store_killer_move(self, move: chess.Move, depth: int):
        """Store a killer move at the given depth"""
        if depth >= self.max_depth:
            return
        if move != self.killer_moves[depth][0]:
            self.killer_moves[depth][1] = self.killer_moves[depth][0]
            self.killer_moves[depth][0] = move

    def store_tt_entry(self, key: int, depth: int, score: float, node_type: NodeType, best_move: Optional[chess.Move]):
        """Store an entry in the transposition table"""
        if len(self.tt) >= self.tt_size:
            self.tt.clear()  # Simple table clearing when full
        self.tt[key] = TranspositionEntry(key, depth, score, node_type, best_move)

    def score_move(self, move: chess.Move, is_winning_position: bool = False) -> int:
        """Enhanced move scoring considering winning positions"""
        score = 0

        # Basic move scoring
        if self.board.is_capture(move):
            victim = self.board.piece_at(move.to_square)
            attacker = self.board.piece_at(move.from_square)
            if victim and attacker:
                victim_value = self.evaluator.PIECE_VALUES[victim.piece_type]
                attacker_value = self.evaluator.PIECE_VALUES[attacker.piece_type]
                score += 10000 + victim_value - (attacker_value // 10)

        if self.board.gives_check(move):
            score += 9000

        if move.promotion:
            score += 8000 + (1000 if move.promotion == chess.QUEEN else 0)

        # Additional scoring for winning positions
        if is_winning_position:
            # Encourage piece trades when winning
            if self.board.is_capture(move):
                score += 5000

            # Encourage pawn advances
            if self.board.piece_at(move.from_square).piece_type == chess.PAWN:
                rank = chess.square_rank(move.to_square)
                if self.board.turn == chess.WHITE:
                    score += rank * 100
                else:
                    score += (7 - rank) * 100

        return score

    def quiescence(self, alpha: float, beta: float, is_maximizing: bool, depth: int = 0, max_depth: int = 4) -> float:
        """Quiescence search with winning position consideration"""
        self.nodes_searched += 1

        stand_pat = self.evaluator.evaluate()

        if depth >= max_depth:
            return stand_pat

        if is_maximizing:
            if stand_pat < beta:
                beta = stand_pat

            for move in self.get_ordered_moves():
                if not (self.board.is_capture(move) or self.board.gives_check(move)):
                    continue

                self.board.push(move)
                score = self.quiescence(alpha, beta, False, depth + 1, max_depth)
                self.board.pop()

                if score < beta:
                    beta = score
                if alpha >= beta:
                    break
            return beta
        else:
            if stand_pat > alpha:
                alpha = stand_pat

            for move in self.get_ordered_moves():
                if not (self.board.is_capture(move) or self.board.gives_check(move)):
                    continue

                self.board.push(move)
                score = self.quiescence(alpha, beta, True, depth + 1, max_depth)
                self.board.pop()

                if score > alpha:
                    alpha = score
                if alpha >= beta:
                    break
            return alpha

    def minimax(self, depth: int, alpha: float, beta: float, is_maximizing: bool, start_time: float, time_limit: float, is_root: bool = False) -> float:
        """Enhanced minimax with winning position handling"""
        self.nodes_searched += 1

        if (time.time() - start_time) > time_limit:
            raise SearchTimeout

        # Check transposition table
        position_key = chess.polyglot.zobrist_hash(self.board)
        tt_entry = self.tt.get(position_key)
        tt_move = None

        if tt_entry and tt_entry.depth >= depth:
            if tt_entry.node_type == NodeType.EXACT:
                if is_root:
                    self.best_move = tt_entry.best_move
                return tt_entry.score
            elif tt_entry.node_type == NodeType.ALPHA and tt_entry.score <= alpha:
                return alpha
            elif tt_entry.node_type == NodeType.BETA and tt_entry.score >= beta:
                return beta
            tt_move = tt_entry.best_move

        if self.board.is_checkmate():
            return -self.MATE_SCORE + self.nodes_searched if is_maximizing else self.MATE_SCORE - self.nodes_searched
        if self.board.is_stalemate() or self.board.is_insufficient_material():
            return 0

        if depth == 0:
            return self.quiescence(alpha, beta, is_maximizing)

        ordered_moves = self.get_ordered_moves(tt_move, depth)
        best_move = None

        if is_maximizing:
            max_score = -self.MATE_SCORE
            for move in ordered_moves:
                self.board.push(move)
                score = self.minimax(depth - 1, alpha, beta, False, start_time, time_limit)
                self.board.pop()

                if score > max_score:
                    max_score = score
                    best_move = move
                    if is_root:
                        self.best_move = move

                alpha = max(alpha, score)
                if alpha >= beta:
                    self.store_killer_move(move, depth)
                    break

            node_type = NodeType.EXACT
            if max_score <= alpha:
                node_type = NodeType.ALPHA
            elif max_score >= beta:
                node_type = NodeType.BETA
            self.store_tt_entry(position_key, depth, max_score, node_type, best_move)

            return max_score
        else:
            min_score = self.MATE_SCORE
            for move in ordered_moves:
                self.board.push(move)
                score = self.minimax(depth - 1, alpha, beta, True, start_time, time_limit)
                self.board.pop()

                if score < min_score:
                    min_score = score
                    best_move = move
                    if is_root:
                        self.best_move = move

                beta = min(beta, score)
                if alpha >= beta:
                    self.store_killer_move(move, depth)
                    break

            node_type = NodeType.EXACT
            if min_score <= alpha:
                node_type = NodeType.ALPHA
            elif min_score >= beta:
                node_type = NodeType.BETA
            self.store_tt_entry(position_key, depth, min_score, node_type, best_move)

            return min_score

    def find_best_move_iterative_deepening(self, max_depth: int, time_limit: float) -> Optional[chess.Move]:
        """
        Enhanced iterative deepening with:
        - Better time management
        - Winning position handling
        - Previous iteration move usage
        - Score trend analysis
        """
        self.nodes_searched = 0
        self.best_move = None
        start_time = time.time()

        # Clear killer moves for new search
        self.killer_moves = [[None, None] for _ in range(self.max_depth)]

        # Track previous iterations
        previous_best_move = None
        previous_scores = []
        stable_count = 0

        try:
            for depth in range(1, max_depth + 1):
                is_maximizing = self.board.turn == chess.BLACK

                # Use previous best move for move ordering
                if previous_best_move:
                    position_key = chess.polyglot.zobrist_hash(self.board)
                    self.store_tt_entry(position_key, depth-1, 0, NodeType.EXACT, previous_best_move)

                score = self.minimax(
                    depth=depth,
                    alpha=-float('inf'),
                    beta=float('inf'),
                    is_maximizing=is_maximizing,
                    start_time=start_time,
                    time_limit=time_limit,
                    is_root=True
                )

                elapsed = time.time() - start_time
                print(f"[Depth {depth}] Score: {score}, Best Move: {self.best_move}, "
                      f"Nodes: {self.nodes_searched}, Time: {elapsed:.2f}s")

                # Store best move for next iteration
                previous_best_move = self.best_move
                previous_scores.append(score)

                # Early exit conditions
                material_eval = self.evaluator.evaluate_material()
                is_winning = abs(material_eval) > 200

                # If we found a mate
                if abs(score) >= self.MATE_SCORE - 100:
                    break

                # If we're clearly winning and score is stable
                if is_winning and len(previous_scores) >= 2:
                    if abs(previous_scores[-1] - previous_scores[-2]) < 50:
                        stable_count += 1
                    else:
                        stable_count = 0

                    # If score has been stable for 2 iterations in winning position
                    if stable_count >= 2:
                        # Only break if we have a forcing move (capture, check, or promotion)
                        if self.is_forcing_move(self.best_move):
                            break

                # Time management
                remaining_time = time_limit - elapsed
                estimated_next_time = elapsed * 4  # Estimate for next depth

                # Different time management for different positions
                time_threshold = time_limit * (0.5 if is_winning else 0.7)

                if elapsed > time_threshold or (depth < max_depth and estimated_next_time > remaining_time):
                    break

        except SearchTimeout:
            print(f"Search stopped due to timeout.")

        # If no move was found, try to get one from the transposition table
        if self.best_move is None:
            position_key = chess.polyglot.zobrist_hash(self.board)
            tt_entry = self.tt.get(position_key)
            if tt_entry and tt_entry.best_move:
                self.best_move = tt_entry.best_move
            else:
                # Last resort: get best move from a quick 1-ply search
                self.best_move = self.get_best_move_from_quick_search()

        return self.best_move

    def is_forcing_move(self, move: Optional[chess.Move]) -> bool:
        """Check if a move is forcing (capture, check, or promotion)"""
        if not move:
            return False

        return (self.board.is_capture(move) or
                self.board.gives_check(move) or
                move.promotion)

    def get_best_move_from_quick_search(self) -> Optional[chess.Move]:
        """Quick 1-ply search to find a reasonable move"""
        best_score = -float('inf') if self.board.turn == chess.WHITE else float('inf')
        best_move = None

        for move in self.get_ordered_moves():
            self.board.push(move)
            score = self.evaluator.evaluate()
            self.board.pop()

            if self.board.turn == chess.WHITE:
                if score > best_score:
                    best_score = score
                    best_move = move
            else:
                if score < best_score:
                    best_score = score
                    best_move = move

        return best_move or (list(self.board.legal_moves)[0] if self.board.legal_moves else None)



    def find_best_move(self, max_depth: int, time_limit: float = 60.0) -> Optional[chess.Move]:
        """
        Public method to find the best move using iterative deepening.
        """
        return self.find_best_move_iterative_deepening(max_depth, time_limit)



# Test code
if __name__ == "__main__":
    # Test position with a tactical sequence
    fen = "r2r2k1/p1p3pp/1p2b3/4Pp2/5P2/q1P1B1P1/PQ6/RR4K1 b - - 0 1"
    board = chess.Board(fen)

    print("Initial position:")
    print(board)

    engine = ChessEngine(board, chess.BLACK)
    best_move = engine.find_best_move(max_depth=4, time_limit=30.0)

    print("\nBest move found:", best_move)
    if best_move:
        board.push(best_move)
        print("\nPosition after best move:")
        print(board)
        if board.is_checkmate():
            print("Checkmate!")
