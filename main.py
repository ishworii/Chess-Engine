from engine.evaluate import Evaluation
from engine.search import ChessEngine
import chess
from typing import List, Tuple

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
        "1R6/8/8/8/8/8/k1K5/8 w - - 42 22"
    ]

    for fen in positions:
        board = chess.Board(fen)
        evaluator = Evaluation(board)
        engine = ChessEngine(board, evaluator)

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
        depth = 20

        # Find the best move using ChessEngine
        best_move = engine.find_best_move(depth)

        print(f"Best Move at depth {depth}: {best_move} ({board.san(best_move)})")
        print(f"Engine Evaluation: {evaluator.evaluate():.2f}")
        print("-" * 50)

if __name__ == "__main__":
    main()

