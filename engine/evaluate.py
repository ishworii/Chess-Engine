# evaluation.py

import chess
import random

class Evaluation:
    # Piece values in centipawns
    PIECE_VALUES = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000
    }

    # Piece-square tables (simplified for brevity)
    PAWN_TABLE = [0]*64
    KNIGHT_TABLE = [0]*64
    BISHOP_TABLE = [0]*64
    ROOK_TABLE = [0]*64
    QUEEN_TABLE = [0]*64
    KING_MIDDLEGAME_TABLE = [0]*64
    KING_ENDGAME_TABLE = [0]*64

    def __init__(self, board: chess.Board):
        self.board = board
        self.initialize_zobrist()

    def initialize_zobrist(self):
        """
        Initialize Zobrist hashing table
        """
        random.seed(0)  # For reproducibility
        self.zobrist_table = {}
        pieces = list(chess.PIECE_TYPES)
        colors = [chess.WHITE, chess.BLACK]
        for piece_type in pieces:
            for color in colors:
                for square in chess.SQUARES:
                    self.zobrist_table[(piece_type, color, square)] = random.getrandbits(64)
        # Castling rights represented as strings
        for castling_right in ['KINGSIDE', 'QUEENSIDE']:
            self.zobrist_table[(castling_right, chess.WHITE)] = random.getrandbits(64)
            self.zobrist_table[(castling_right, chess.BLACK)] = random.getrandbits(64)
        # En passant
        for square in chess.SQUARES:
            self.zobrist_table[('ep', square)] = random.getrandbits(64)

    def transposition_key(self, board: chess.Board) -> int:
        """
        Compute Zobrist hash for the current board
        """
        key = 0
        for square, piece in board.piece_map().items():
            key ^= self.zobrist_table.get((piece.piece_type, piece.color, square), 0)
        # Castling rights
        if board.has_kingside_castling_rights(chess.WHITE):
            key ^= self.zobrist_table.get(('KINGSIDE', chess.WHITE), 0)
        if board.has_queenside_castling_rights(chess.WHITE):
            key ^= self.zobrist_table.get(('QUEENSIDE', chess.WHITE), 0)
        if board.has_kingside_castling_rights(chess.BLACK):
            key ^= self.zobrist_table.get(('KINGSIDE', chess.BLACK), 0)
        if board.has_queenside_castling_rights(chess.BLACK):
            key ^= self.zobrist_table.get(('QUEENSIDE', chess.BLACK), 0)
        # En passant
        if board.ep_square:
            key ^= self.zobrist_table.get(('ep', board.ep_square), 0)
        return key

    def get_piece_square_table_value(self, piece: chess.Piece, square: chess.Square) -> int:
        """Get the piece-square table value for a given piece and square."""
        if piece.piece_type == chess.PAWN:
            table = self.PAWN_TABLE
        elif piece.piece_type == chess.KNIGHT:
            table = self.KNIGHT_TABLE
        elif piece.piece_type == chess.BISHOP:
            table = self.BISHOP_TABLE
        elif piece.piece_type == chess.ROOK:
            table = self.ROOK_TABLE
        elif piece.piece_type == chess.QUEEN:
            table = self.QUEEN_TABLE
        else:  # King
            table = self.KING_ENDGAME_TABLE if self.is_endgame() else self.KING_MIDDLEGAME_TABLE

        # For black pieces, mirror the square vertically
        if not piece.color:
            square = chess.square_mirror(square)

        return table[square]

    def evaluate_piece_mobility(self) -> int:
        """
        Evaluate piece mobility (number of legal moves available).
        """
        original_turn = self.board.turn

        # Count white's moves
        self.board.turn = chess.WHITE
        white_mobility = sum(1 for _ in self.board.legal_moves)

        # Count black's moves
        self.board.turn = chess.BLACK
        black_mobility = sum(1 for _ in self.board.legal_moves)

        # Restore original turn
        self.board.turn = original_turn

        return (white_mobility - black_mobility) * 10

    def evaluate_pawn_structure(self) -> int:
        """
        Evaluate pawn structure (doubled, isolated, and passed pawns).
        """
        score = 0

        for color in [chess.WHITE, chess.BLACK]:
            multiplier = 1 if color == chess.WHITE else -1

            # Get all pawns for this color
            pawns_bb = self.board.pieces(chess.PAWN, color)
            pawns_bitmask = int(pawns_bb)

            # Count pawns on each file
            files = [0] * 8
            for square in chess.SQUARES:
                if pawns_bitmask & chess.BB_SQUARES[square]:
                    file = chess.square_file(square)
                    files[file] += 1

            # Evaluate doubled and isolated pawns
            for file in range(8):
                if files[file] > 1:
                    score -= 20 * multiplier  # Doubled pawns penalty
                if files[file] > 0:
                    # Check if the pawn is isolated
                    left = file - 1 if file > 0 else None
                    right = file + 1 if file < 7 else None
                    if (left is not None and files[left] == 0) and \
                            (right is not None and files[right] == 0):
                        score -= 10 * multiplier  # Isolated pawn penalty

            # Evaluate passed pawns
            for square in chess.SQUARES:
                if pawns_bitmask & chess.BB_SQUARES[square]:
                    if self.is_passed_pawn(square, color):
                        score += 50 * multiplier  # Passed pawn bonus

        return score

    def is_passed_pawn(self, square: chess.Square, color: chess.Color) -> bool:
        """
        Determine if a pawn is passed (no opposing pawns ahead on same or adjacent files).
        """
        file = chess.square_file(square)
        rank = chess.square_rank(square)

        # Direction to check (up for white, down for black)
        direction = 1 if color == chess.WHITE else -1
        enemy_color = not color

        # Check files: same, left, and right
        for f in range(max(0, file - 1), min(8, file + 2)):
            # Check ranks ahead
            if color == chess.WHITE:
                ranks_ahead = range(rank + 1, 8)
            else:
                ranks_ahead = range(rank - 1, -1, -1)

            for r in ranks_ahead:
                check_square = chess.square(f, r)
                piece = self.board.piece_at(check_square)
                if piece and piece.piece_type == chess.PAWN and piece.color == enemy_color:
                    return False
        return True

    def calculate_game_phase(self) -> float:
        """
        Calculate game phase (0 = opening/middlegame, 1 = endgame)
        Based on material remaining
        """
        material = 0
        for piece_type in chess.PIECE_TYPES[:-1]:  # Exclude king from material count
            white_bb = self.board.pieces(piece_type, chess.WHITE)
            black_bb = self.board.pieces(piece_type, chess.BLACK)
            white_bitmask = int(white_bb)
            black_bitmask = int(black_bb)
            material += white_bitmask.bit_count() * self.PIECE_VALUES[piece_type]
            material += black_bitmask.bit_count() * self.PIECE_VALUES[piece_type]
        # Max material = 14 * 900 (assuming all queens, which is unrealistic but serves as an upper bound)
        return 1.0 - min(1.0, material / (14 * 900))

    def evaluate_center_control(self) -> int:
        """
        Evaluate control of the center squares (d4, d5, e4, e5)
        """
        center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
        score = 0
        for square in center_squares:
            white_attackers = len(self.board.attackers(chess.WHITE, square))
            black_attackers = len(self.board.attackers(chess.BLACK, square))
            score += 10 * (white_attackers - black_attackers)
            # Bonus for piece occupation
            piece = self.board.piece_at(square)
            if piece:
                if piece.color == chess.WHITE:
                    score += 20
                else:
                    score -= 20
        return score

    def evaluate_piece_coordination(self) -> int:
        """
        Evaluate piece coordination and connectivity
        """
        score = 0
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if not piece or piece.piece_type == chess.KING:
                continue

            defenders = len(self.board.attackers(piece.color, square))
            if piece.color == chess.WHITE:
                score += defenders * 5
            else:
                score -= defenders * 5

            # Extra bonus for pieces supporting each other in the center
            file = chess.square_file(square)
            rank = chess.square_rank(square)
            if 2 <= file <= 5 and 2 <= rank <= 5:
                if piece.color == chess.WHITE:
                    score += defenders * 3
                else:
                    score -= defenders * 3
        return score

    def evaluate_king_tropism(self) -> int:
        """
        Evaluate attacking pieces' distance to enemy king
        Only relevant in middlegame
        """
        if self.calculate_game_phase() >= 0.7:  # Skip in endgame
            return 0

        score = 0
        w_king_square = self.board.king(chess.WHITE)
        b_king_square = self.board.king(chess.BLACK)

        if not w_king_square or not b_king_square:  # Should never happen in legal position
            return 0

        attacking_pieces = [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]

        for piece_type in attacking_pieces:
            # White pieces attacking black king
            attackers = self.board.attackers(chess.WHITE, b_king_square)
            for attacker_square in attackers:
                piece = self.board.piece_at(attacker_square)
                if piece and piece.piece_type == piece_type:
                    distance = chess.square_distance(attacker_square, b_king_square)
                    score += (8 - distance) * 2

            # Black pieces attacking white king
            attackers = self.board.attackers(chess.BLACK, w_king_square)
            for attacker_square in attackers:
                piece = self.board.piece_at(attacker_square)
                if piece and piece.piece_type == piece_type:
                    distance = chess.square_distance(attacker_square, w_king_square)
                    score -= (8 - distance) * 2

        return score

    def evaluate_trapped_pieces(self) -> int:
        """
        Penalize trapped pieces with limited mobility
        """
        score = 0
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if not piece or piece.piece_type == chess.PAWN:
                continue

            mobility = len(self.board.attacks(square))
            if mobility <= 2:  # Piece has very limited mobility
                penalty = self.PIECE_VALUES[piece.piece_type] // 4
                if piece.color == chess.WHITE:
                    score -= penalty
                else:
                    score += penalty

            # Extra penalty for trapped bishops
            if piece.piece_type == chess.BISHOP and mobility <= 3:
                if piece.color == chess.WHITE:
                    score -= 50
                else:
                    score += 50
        return score

    def get_material_score(self) -> int:
        """
        Calculate material score for both sides.
        Returns positive score if white is ahead in material,
        negative score if black is ahead.
        """
        score = 0
        # Count material for each piece type
        for piece_type in chess.PIECE_TYPES[:-1]:  # Exclude king from material count
            # Count white pieces and multiply by piece value
            white_bb = self.board.pieces(piece_type, chess.WHITE)
            white_bitmask = int(white_bb)
            white_count = white_bitmask.bit_count()
            score += white_count * self.PIECE_VALUES[piece_type]

            # Count black pieces and subtract (multiply by piece value)
            black_bb = self.board.pieces(piece_type, chess.BLACK)
            black_bitmask = int(black_bb)
            black_count = black_bitmask.bit_count()
            score -= black_count * self.PIECE_VALUES[piece_type]

            # Add piece-square table values
            for square in self.board.pieces(piece_type, chess.WHITE):
                piece = chess.Piece(piece_type, chess.WHITE)
                score += self.get_piece_square_table_value(piece, square)

            for square in self.board.pieces(piece_type, chess.BLACK):
                piece = chess.Piece(piece_type, chess.BLACK)
                score -= self.get_piece_square_table_value(piece, square)

        return score

    def evaluate(self) -> int:
        """
        Main evaluation function combining all components
        """
        if self.board.is_checkmate():
            return -20000 if self.board.turn else 20000

        if self.board.is_stalemate() or self.board.is_insufficient_material():
            return 0

        score = 0

        # Material
        score += self.get_material_score()

        # Positional factors
        game_phase = self.calculate_game_phase()

        if game_phase < 0.7:  # Middlegame
            score += self.evaluate_center_control()
            score += self.evaluate_piece_coordination()
            score += self.evaluate_king_tropism()
        else:  # Endgame
            score += self.evaluate_center_control() // 2  # Less important in endgame

        # Always evaluate
        score += self.evaluate_trapped_pieces()

        # Small bonus for side to move
        score += 10 if self.board.turn else -10

        return score

    def is_endgame(self) -> bool:
        """
        Determine if the current position is in the endgame.
        Simple heuristic: few pieces left.
        """
        # Count total material excluding kings
        total_material = 0
        for piece_type in chess.PIECE_TYPES[:-1]:
            total_material += len(self.board.pieces(piece_type, chess.WHITE)) * self.PIECE_VALUES[piece_type]
            total_material += len(self.board.pieces(piece_type, chess.BLACK)) * self.PIECE_VALUES[piece_type]
        return total_material < 1500  # Threshold can be adjusted

def test_material_counting():
    """Test specific material counting scenarios"""
    test_positions = [
        (
            # White up a knight (Black missing a knight)
            "rnbqkb1r/pppp1ppp/8/4p3/4P3/8/PPPPQPPP/RNB1KBNR b KQkq - 1 2",
            320,  # White up a knight
            "White up a knight (Black missing knight)"
        ),
        (
            "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
            0,  # Equal material
            "Equal material after 1.e4 e5"
        ),
        (
            "rnbqkb1r/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKB1R w KQkq - 0 2",
            320,  # White up a knight
            "White up a knight (Black missing knight)"
        ),
        (
            "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKB1R b KQkq - 0 2",
            -320,  # Black up a knight
            "Black up a knight (Black missing knight)"
        ),
        (
            "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPPBPPP/RNBQK1NR b KQkq - 1 2",
            0,  # Equal material (bishop vs knight)
            "Equal material (bishop vs knight)"
        )
    ]

    for fen, expected_score, description in test_positions:
        board = chess.Board(fen)
        evaluator = Evaluation(board)
        actual_score = evaluator.evaluate()

        print(f"\nTesting: {description}")
        print(f"FEN: {fen}")
        print(f"Expected score: {expected_score}")
        print(f"Actual score: {actual_score}")
        print(board)

        if actual_score == expected_score:
            print("✅ Test passed")
        else:
            print("❌ Test failed")
            # Print detailed material count for debugging
            print("\nDetailed material count:")
            for piece_type in chess.PIECE_TYPES[:-1]:
                white_bitmask = int(board.pieces(piece_type, chess.WHITE))
                black_bitmask = int(board.pieces(piece_type, chess.BLACK))
                white_count = white_bitmask.bit_count()
                black_count = black_bitmask.bit_count()
                print(f"{chess.piece_name(piece_type).capitalize()}:")
                print(f"  White: {white_count} ({white_count * evaluator.PIECE_VALUES[piece_type]})")
                print(f"  Black: {black_count} ({black_count * evaluator.PIECE_VALUES[piece_type]})")

        print("-" * 50)

if __name__ == "__main__":
    test_material_counting()
