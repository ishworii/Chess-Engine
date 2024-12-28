import chess
import chess.engine
import random
from engine.evaluate import Evaluation

STOCKFISH_PATH = "stockfish_17/bin/stockfish"

def generate_random_positions(num_positions=10):
    """
    Generate random chess positions for testing.

    Args:
        num_positions (int): Number of positions to generate.

    Returns:
        list of chess.Board: Generated positions.
    """
    positions = []
    for _ in range(num_positions):
        board = chess.Board()
        for _ in range(random.randint(5, 20)):
            if board.is_game_over():
                break
            legal_moves = list(board.legal_moves)
            move = random.choice(legal_moves)
            board.push(move)
        positions.append(board)
    return positions

def test_evaluation():
    """
    Test the custom evaluation function against Stockfish.
    """
    # Initialize Stockfish
    engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)

    # Generate positions
    positions = generate_random_positions()

    for i, board in enumerate(positions):
        # Custom evaluation
        evaluator = Evaluation(board)
        custom_eval = evaluator.evaluate()

        # Stockfish evaluation
        stockfish_eval = engine.analyse(board, chess.engine.Limit(depth=15))['score'].white().score(mate_score=100000)
        stockfish_eval /= 100
        # Compare
        print(f"Position {i+1}:")
        print(board.fen())
        print(board.unicode())
        print(f"Custom Evaluation: {custom_eval:.2f}")
        print(f"Stockfish Evaluation: {stockfish_eval}")
        print("-" * 40)

    engine.quit()

if __name__ == "__main__":
    test_evaluation()
