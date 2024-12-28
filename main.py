from engine.evaluate import Evaluation
import chess

def main():
    positions = [
        "r4rk1/pp3ppp/2p3n1/3p4/4P3/4N3/PPP2PPP/2KRR3 w - - 0 3"
    ]

    for fen in positions:
        board = chess.Board(fen)
        evaluator = Evaluation(board)
        print("Board Position:")
        print(board.unicode())
        print(f"Evaluation: {evaluator.evaluate():.2f}")
        print("-" * 40)

if __name__ == "__main__":
    main()
