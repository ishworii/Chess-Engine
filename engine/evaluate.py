import chess

class Evaluation:
    # Values in centipawns
    PIECE_VALUES = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000
    }

    # Piece-square tables (values adjusted for centipawns)
    PAWN_TABLE = [
        0,   0,   0,   0,   0,   0,   0,   0,
        50,  50,  50,  50,  50,  50,  50,  50,
        10,  10,  20,  30,  30,  20,  10,  10,
        5,   5,  10,  25,  25,  10,   5,   5,
        0,   0,   0,  20,  20,   0,   0,   0,
        5,  -5, -10,   0,   0, -10,  -5,   5,
        5,  10,  10, -20, -20,  10,  10,   5,
        0,   0,   0,   0,   0,   0,   0,   0
    ]

    KNIGHT_TABLE = [
        -50, -40, -30, -30, -30, -30, -40, -50,
        -40, -20,   0,   0,   0,   0, -20, -40,
        -30,   0,  10,  15,  15,  10,   0, -30,
        -30,   5,  15,  20,  20,  15,   5, -30,
        -30,   0,  15,  20,  20,  15,   0, -30,
        -30,   5,  10,  15,  15,  10,   5, -30,
        -40, -20,   0,   5,   5,   0, -20, -40,
        -50, -40, -30, -30, -30, -30, -40, -50
    ]

    BISHOP_TABLE = [
        -20, -10, -10, -10, -10, -10, -10, -20,
        -10,   0,   0,   0,   0,   0,   0, -10,
        -10,   0,   5,  10,  10,   5,   0, -10,
        -10,   5,   5,  10,  10,   5,   5, -10,
        -10,   0,  10,  10,  10,  10,   0, -10,
        -10,  10,  10,  10,  10,  10,  10, -10,
        -10,   5,   0,   0,   0,   0,   5, -10,
        -20, -10, -10, -10, -10, -10, -10, -20
    ]

    ROOK_TABLE = [
        0,   0,   0,   0,   0,   0,   0,   0,
        5,  10,  10,  10,  10,  10,  10,   5,
        -5,   0,   0,   0,   0,   0,   0,  -5,
        -5,   0,   0,   0,   0,   0,   0,  -5,
        -5,   0,   0,   0,   0,   0,   0,  -5,
        -5,   0,   0,   0,   0,   0,   0,  -5,
        -5,   0,   0,   0,   0,   0,   0,  -5,
        0,   0,   0,   5,   5,   0,   0,   0
    ]

    QUEEN_TABLE = [
        -20, -10, -10,  -5,  -5, -10, -10, -20,
        -10,   0,   0,   0,   0,   0,   0, -10,
        -10,   0,   5,   5,   5,   5,   0, -10,
        -5,    0,   5,   5,   5,   5,   0,  -5,
        0,     0,   5,   5,   5,   5,   0,  -5,
        -10,   5,   5,   5,   5,   5,   0, -10,
        -10,   0,   5,   0,   0,   0,   0, -10,
        -20, -10, -10,  -5,  -5, -10, -10, -20
    ]

    KING_MIDDLEGAME_TABLE = [
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -20, -30, -30, -40, -40, -30, -30, -20,
        -10, -20, -20, -20, -20, -20, -20, -10,
        20,  20,   0,   0,   0,   0,  20,  20,
        20,  30,  10,   0,   0,  10,  30,  20
    ]

    KING_ENDGAME_TABLE = [
        -50, -40, -30, -20, -20, -30, -40, -50,
        -30, -20, -10,   0,   0, -10, -20, -30,
        -30, -10,  20,  30,  30,  20, -10, -30,
        -30, -10,  30,  40,  40,  30, -10, -30,
        -30, -10,  30,  40,  40,  30, -10, -30,
        -30, -10,  20,  30,  30,  20, -10, -30,
        -30, -30,   0,   0,   0,   0, -30, -30,
        -50, -30, -30, -30, -30, -30, -30, -50
    ]

    def __init__(self, board: chess.Board):
        self.board = board

    def get_game_phase(self) -> float:
        """
        Returns a value between 0 (opening) and 1 (endgame)
        based on material remaining
        """
        total_material = sum(len(self.board.pieces(piece_type, color))
                             for piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
                             for color in [chess.WHITE, chess.BLACK])

        max_material = 16  # 2 queens + 4 rooks + 4 bishops + 4 knights
        return 1 - (total_material / max_material)

    def material_evaluation(self) -> int:
        """Evaluate material balance"""
        score = 0
        phase = self.get_game_phase()

        for piece_type, value in self.PIECE_VALUES.items():
            # White pieces
            for square in self.board.pieces(piece_type, chess.WHITE):
                score += value
                if piece_type == chess.KING:
                    if phase < 0.5:
                        score += self.KING_MIDDLEGAME_TABLE[square]
                    else:
                        score += self.KING_ENDGAME_TABLE[square]
                else:
                    piece_square_table = {
                        chess.PAWN: self.PAWN_TABLE,
                        chess.KNIGHT: self.KNIGHT_TABLE,
                        chess.BISHOP: self.BISHOP_TABLE,
                        chess.ROOK: self.ROOK_TABLE,
                        chess.QUEEN: self.QUEEN_TABLE
                    }.get(piece_type, [0] * 64)
                    score += piece_square_table[square]

            # Black pieces
            for square in self.board.pieces(piece_type, chess.BLACK):
                score -= value
                if piece_type == chess.KING:
                    if phase < 0.5:
                        score -= self.KING_MIDDLEGAME_TABLE[chess.square_mirror(square)]
                    else:
                        score -= self.KING_ENDGAME_TABLE[chess.square_mirror(square)]
                else:
                    piece_square_table = {
                        chess.PAWN: self.PAWN_TABLE,
                        chess.KNIGHT: self.KNIGHT_TABLE,
                        chess.BISHOP: self.BISHOP_TABLE,
                        chess.ROOK: self.ROOK_TABLE,
                        chess.QUEEN: self.QUEEN_TABLE
                    }.get(piece_type, [0] * 64)
                    score -= piece_square_table[chess.square_mirror(square)]

        return score

    def mobility_evaluation(self) -> int:
        """Evaluate piece mobility"""
        original_turn = self.board.turn

        # Count white moves
        self.board.turn = chess.WHITE
        white_mobility = len(list(self.board.legal_moves))

        # Count black moves
        self.board.turn = chess.BLACK
        black_mobility = len(list(self.board.legal_moves))

        # Restore original turn
        self.board.turn = original_turn

        return (white_mobility - black_mobility) * 10

    def pawn_structure_evaluation(self) -> int:
        """Evaluate pawn structure"""
        score = 0

        # Evaluate doubled pawns
        for file in range(8):
            white_pawns = 0
            black_pawns = 0
            for rank in range(8):
                square = chess.square(file, rank)
                piece = self.board.piece_at(square)
                if piece and piece.piece_type == chess.PAWN:
                    if piece.color == chess.WHITE:
                        white_pawns += 1
                    else:
                        black_pawns += 1

            # Penalty for doubled pawns
            if white_pawns > 1:
                score -= 20 * (white_pawns - 1)
            if black_pawns > 1:
                score += 20 * (black_pawns - 1)

        # Evaluate isolated pawns
        for file in range(8):
            for color in [chess.WHITE, chess.BLACK]:
                if self.has_isolated_pawn(file, color):
                    score += -15 if color == chess.WHITE else 15

        # Evaluate passed pawns
        for square in chess.SQUARES:
            if self.board.piece_at(square) and self.board.piece_at(square).piece_type == chess.PAWN:
                if self.is_passed_pawn(square):
                    color = self.board.piece_at(square).color
                    score += 50 if color == chess.WHITE else -50

        return score

    def has_isolated_pawn(self, file: int, color: bool) -> bool:
        """Check if there is an isolated pawn on the given file"""
        has_pawn_on_file = False
        has_adjacent_pawn = False

        for rank in range(8):
            square = chess.square(file, rank)
            piece = self.board.piece_at(square)
            if piece and piece.piece_type == chess.PAWN and piece.color == color:
                has_pawn_on_file = True

        for adjacent_file in [file - 1, file + 1]:
            if 0 <= adjacent_file <= 7:
                for rank in range(8):
                    square = chess.square(adjacent_file, rank)
                    piece = self.board.piece_at(square)
                    if piece and piece.piece_type == chess.PAWN and piece.color == color:
                        has_adjacent_pawn = True

        return has_pawn_on_file and not has_adjacent_pawn

    def is_passed_pawn(self, square: int) -> bool:
        """Check if the pawn on the given square is passed"""
        if not self.board.piece_at(square) or self.board.piece_at(square).piece_type != chess.PAWN:
            return False

        piece = self.board.piece_at(square)
        color = piece.color
        file = chess.square_file(square)
        rank = chess.square_rank(square)

        # Check if there are any opposing pawns ahead of this pawn
        direction = 1 if color == chess.WHITE else -1
        target_ranks = range(rank + direction, 8 if color == chess.WHITE else -1, direction)

        for r in target_ranks:
            for f in [file - 1, file, file + 1]:
                if 0 <= f <= 7:
                    s = chess.square(f, r)
                    p = self.board.piece_at(s)
                    if p and p.piece_type == chess.PAWN and p.color != color:
                        return False
        return True

    def king_safety_evaluation(self) -> int:
        """Evaluate king safety"""
        score = 0
        phase = self.get_game_phase()

        if phase < 0.7:  # Only consider king safety in opening/middlegame
            for color in [chess.WHITE, chess.BLACK]:
                king_square = self.board.king(color)
                if king_square is None:
                    continue

                # Pawn shield
                shield_value = self.evaluate_pawn_shield(king_square, color)
                score += shield_value if color == chess.WHITE else -shield_value

                # King attackers
                attackers_value = self.evaluate_king_attackers(king_square, color)
                score += attackers_value if color == chess.WHITE else -attackers_value

        return score

    def evaluate_pawn_shield(self, king_square: int, color: bool) -> int:
        """Evaluate pawn shield in front of the king"""
        score = 0
        rank = chess.square_rank(king_square)
        file = chess.square_file(king_square)

        # Define pawn shield squares
        shield_ranks = [rank + 1] if color == chess.WHITE else [rank - 1]
        shield_files = [max(0, file - 1), file, min(7, file + 1)]

        for r in shield_ranks:
            if 0 <= r <= 7:
                for f in shield_files:
                    square = chess.square(f, r)
                    piece = self.board.piece_at(square)
                    if piece and piece.piece_type == chess.PAWN and piece.color == color:
                        score += 10

        return score

    def evaluate_king_attackers(self, king_square: int, color: bool) -> int:
        """Evaluate pieces attacking squares around the king"""
        score = 0
        opponent_color = not color

        # Define squares around the king
        rank = chess.square_rank(king_square)
        file = chess.square_file(king_square)

        for r in range(max(0, rank - 1), min(8, rank + 2)):
            for f in range(max(0, file - 1), min(8, file + 2)):
                square = chess.square(f, r)
                attackers = self.board.attackers(opponent_color, square)
                score -= len(list(attackers)) * 10

        return score

    def evaluate(self) -> int:
        """Main evaluation function"""
        if self.board.is_checkmate():
            return -20000 if self.board.turn else 20000

        if self.board.is_stalemate() or self.board.is_insufficient_material():
            return 0

        score = 0

        # Material and piece position evaluation
        score += self.material_evaluation()

        # Mobility evaluation
        score += self.mobility_evaluation()

        # Pawn structure evaluation
        score += self.pawn_structure_evaluation()

        # King safety evaluation
        score += self.king_safety_evaluation()

        # Add a small random factor to prevent repetition
        score += hash(self.board.fen()) % 10

        return score if self.board.turn else -score

