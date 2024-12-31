from engine.evaluate import Evaluation
from engine.search import ChessEngine
import chess
from typing import List, Tuple
import time

def evaluate_moves(board: chess.Board, evaluator: Evaluation) -> List[Tuple[chess.Move, float]]:
    """
    Evaluate all legal moves and return them sorted by evaluation.
    """
    move_evaluations = []

    for move in board.legal_moves:
        # Make the move
        board.push(move)
        # Check if the move leads to checkmate
        if board.is_checkmate():
            eval_score = 20000 if board.turn else -20000
        else:
            # Evaluate the position (don't negate the evaluation)
            eval_score = evaluator.evaluate()
        # Take back the move
        board.pop()

        move_evaluations.append((move, eval_score))

    # Sort moves by evaluation score (best to worst)
    return sorted(move_evaluations, key=lambda x: x[1], reverse=True)


def main():
    positions = [
    "8/5k2/2Bp4/3R4/4P3/3P4/1PK5/8 w - - 3 39"
    ]

    for fen in positions:
        board = chess.Board(fen=fen)
        evaluator = Evaluation(board)
        engine = ChessEngine(board)

        print("Board Position:")
        print(board.unicode())
        print(f"Initial Position Evaluation: {evaluator.evaluate():.3f}")
        print("\nAll Legal Moves Sorted by Evaluation:")
        print("-" * 50)
        print("Move    | Evaluation | SAN")
        print("-" * 50)

        # Get and display all moves with their evaluations
        moves_with_eval = evaluate_moves(board, evaluator)
        for move, eval_score in moves_with_eval:
            san_move = board.san(move)
            print(f"{move}  | {eval_score:9.2f} | {san_move}")

        print("\nEngine Search Result:")
        # Define search depth
        depth = 6

        # Find the best move using ChessEngine
        best_move = engine.find_best_move(depth)

        print(f"Best Move at depth {depth}: {best_move} ({board.san(best_move)})")
        print(f"Engine Evaluation: {evaluator.evaluate():.2f}")
        print("-" * 50)

def test_evaluation():
    """Test evaluation function against standard positions"""
    test_positions = [
        # Format: (FEN, expected_eval_range, description)
        (
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            (0, 0),
            "Starting position - should be equal"
        ),
        (
            "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
            (0, 0),
            "After 1.e4 e5 - should be equal"
        ),
        (
            "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
            (0, 0),
            "After 1.e4 - should be roughly equal"
        ),
        (
            "rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2",
            (0, 0),
            "After 1.e4 d5 - should be equal"
        ),
        (
            "rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2",
            (0, 0),
            "After 1.e4 c5 2.Nf3 - should be equal"
        ),
        # Material advantage positions
        (
            "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPPQPPP/RNB1KBNR b KQkq - 1 2",
            (-400, -300),
            "White up a knight"
        ),
        (
            "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
            (0, 0),
            "Equal position after e4 e5"
        ),
        # Checkmate positions
        (
            "k7/8/8/8/8/8/R7/K7 b - - 0 1",
            (19000, 20000),
            "White has mate in one"
        ),
        (
            "3k4/8/3K4/8/8/8/8/R7 b - - 0 1",
            (19000, 20000),
            "White has mate in one with rook"
        ),
        # Material imbalance positions
        (
            "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPPBPPP/RNBQK1NR b KQkq - 1 2",
            (0, 0),
            "Equal material (bishop vs knight)"
        ),
        (
            "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPPQPPP/RNB1KBNR b KQkq - 1 2",
            (-400, -300),
            "White up a knight"
        ),
        # Pawn structure positions
        (
            "rnbqkbnr/ppp2ppp/8/3pp3/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 0 3",
            (0, 0),
            "Equal pawn structure"
        ),
        # Stalemate position
        (
            "k7/8/1K6/8/8/8/8/8 b - - 0 1",
            (0, 0),
            "Stalemate position"
        ),
        # Insufficient material
        (
            "k7/8/K7/8/8/8/8/8 w - - 0 1",
            (0, 0),
            "Insufficient material (just kings)"
        ),
        (
            "k7/8/K7/8/8/8/8/B7 w - - 0 1",
            (0, 0),
            "Insufficient material (king and bishop vs king)"
        )
    ]

    for fen, expected_range, description in test_positions:
        board = chess.Board(fen)
        evaluator = Evaluation(board)
        score = evaluator.evaluate()
        min_expected, max_expected = expected_range

        print(f"\nTesting: {description}")
        print(f"FEN: {fen}")
        print(f"Evaluation: {score}")
        print(f"Expected range: {min_expected} to {max_expected}")

        if min_expected <= score <= max_expected:
            print("✅ Test passed")
        else:
            print("❌ Test failed")
            print(f"Score {score} outside expected range [{min_expected}, {max_expected}]")
        print(board)
        print("-" * 50)

if __name__ == "__main__":
    main()

