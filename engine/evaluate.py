import chess

class Evaluation:
    PIECE_VALUES = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3.1,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0
    }

    # Piece-square tables
    PAWN_TABLE = [
        0,   0,   0,   0,   0,   0,   0,   0,
        2,   3,   3, -10, -10,   3,   3,   2,
        3,   0,  -2,   5,   5,  -2,   0,   3,
        0,   0,   5,  10,  10,   5,   0,   0,
        2,   3,   8,  15,  15,   8,   3,   2,
        5,   5,  10,  20,  20,  10,   5,   5,
        50,  50,  50,  50,  50,  50,  50,  50,
        0,   0,   0,   0,   0,   0,   0,   0,
    ]


    KNIGHT_TABLE = [
        -50, -40, -30, -30, -30, -30, -40, -50,
        -40, -20,   0,   0,   0,   0, -20, -40,
        -30,   0,  10,  15,  15,  10,   0, -30,
        -30,   5,  15,  20,  20,  15,   5, -30,
        -30,   0,  15,  20,  20,  15,   0, -30,
        -30,   5,  10,  15,  15,  10,   5, -30,
        -40, -20,   0,   5,   5,   0, -20, -40,
        -50, -40, -30, -30, -30, -30, -40, -50,
    ]

    BISHOP_TABLE = [
        -20, -10, -10, -10, -10, -10, -10, -20,
        -10,   5,   0,   0,   0,   0,   5, -10,
        -10,  10,  10,  10,  10,  10,  10, -10,
        -10,   0,  10,  10,  10,  10,   0, -10,
        -10,   5,   5,  10,  10,   5,   5, -10,
        -10,   0,   5,  10,  10,   5,   0, -10,
        -10,   0,   0,   0,   0,   0,   0, -10,
        -20, -10, -10, -10, -10, -10, -10, -20,
    ]

    ROOK_TABLE = [
        0,   0,   0,   5,   5,   0,   0,   0,
        -5,   0,   0,   0,   0,   0,   0,  -5,
        -5,   0,   0,   0,   0,   0,   0,  -5,
        -5,   0,   0,   0,   0,   0,   0,  -5,
        -5,   0,   0,   0,   0,   0,   0,  -5,
        -5,   0,   0,   0,   0,   0,   0,  -5,
        5,  10,  10,  10,  10,  10,  10,   5,
        0,   0,   0,   5,   5,   0,   0,   0,
    ]

    QUEEN_TABLE = [
        -20, -10, -10,  -5,  -5, -10, -10, -20,
        -10,   0,   0,   0,   0,   0,   0, -10,
        -10,   0,   5,   5,   5,   5,   0, -10,
        -5,   0,   5,   5,   5,   5,   0,  -5,
        0,   0,   5,   5,   5,   5,   0,  -5,
        -10,   5,   5,   5,   5,   5,   0, -10,
        -10,   0,   5,   0,   0,   0,   0, -10,
        -20, -10, -10,  -5,  -5, -10, -10, -20,
    ]

    KING_MIDGAME_TABLE = [
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -20, -30, -30, -40, -40, -30, -30, -20,
        -10, -20, -20, -20, -20, -20, -20, -10,
        20,  20,   0,   0,   0,   0,  20,  20,
        20,  30,  10,   0,   0,  10,  30,  20,
    ]

    PIECE_SQUARE_TABLES = {
        chess.PAWN: PAWN_TABLE,
        chess.KNIGHT: KNIGHT_TABLE,
        chess.BISHOP: BISHOP_TABLE,
        chess.ROOK: ROOK_TABLE,
        chess.QUEEN: QUEEN_TABLE,
        chess.KING: KING_MIDGAME_TABLE
    }

    #Scaling factor
    SCALING_FACTOR = 0.1

    # Bonus for having both bishops
    BISHOP_PAIR_BONUS = 0.5

    # Penalty for having both rooks (redundancy)
    ROOK_PAIR_PENALTY = 0.25

    # Penalty for the knight pair (as two knights are less successful against the rook than any other pair of minor pieces)
    KNIGHT_PENALTY = 0.25

    def __init__(self, board: chess.Board):
            self.board = board

    def material_evaluation(self) -> float:
        """
        Evaluate the position based on material count and piece-square tables.

        Returns:
            float: Material evaluation score (positive for White, negative for Black).
        """
        evaluation = 0

        for piece_type, value in self.PIECE_VALUES.items():
            for square in self.board.pieces(piece_type, chess.WHITE):
                evaluation += value
                evaluation += self.SCALING_FACTOR *self.PIECE_SQUARE_TABLES.get(piece_type, [0] * 64)[square]

            for square in self.board.pieces(piece_type, chess.BLACK):
                evaluation -= value
                evaluation -= self.SCALING_FACTOR*self.PIECE_SQUARE_TABLES.get(piece_type, [0] * 64)[chess.square_mirror(square)]
        print(f"Material evaluation: {evaluation}")
        return evaluation

    def bishop_pair_bonus(self) -> float:
        """
        Add a bonus for having both bishops.

        Returns:
            float: Bonus for having both bishops (positive for White, negative for Black).
        """
        white_bishops = len(self.board.pieces(chess.BISHOP, chess.WHITE))
        black_bishops = len(self.board.pieces(chess.BISHOP, chess.BLACK))

        bonus = 0
        if white_bishops >= 2:
            bonus += self.BISHOP_PAIR_BONUS
        if black_bishops >= 2:
            bonus -= self.BISHOP_PAIR_BONUS
        print(f"Bonus for having bishops: {bonus}")
        return bonus

    def rook_pair_penalty(self) -> float:
        """
        Add a penalty for having both rooks on the board (redundancy).

        Returns:
            float: Penalty for having both rooks (positive for Black, negative for White).
        """
        white_rooks = len(self.board.pieces(chess.ROOK, chess.WHITE))
        black_rooks = len(self.board.pieces(chess.ROOK, chess.BLACK))

        penalty = 0
        if white_rooks >= 2:
            penalty -= self.ROOK_PAIR_PENALTY
        if black_rooks >= 2:
            penalty += self.ROOK_PAIR_PENALTY
        print(f"Penalty for having rooks: {penalty}")
        return penalty

    def knight_pair_penalty(self) -> float:
        """
        Add a penalty for having both knights on the board.

        Returns:
            float: Penalty for having both knights (positive for Black, negative for White).
        """
        white_knights = len(self.board.pieces(chess.KNIGHT, chess.WHITE))
        black_knights = len(self.board.pieces(chess.KNIGHT, chess.BLACK))

        penalty = 0
        if white_knights >= 2:
            penalty -= self.KNIGHT_PENALTY
        if black_knights >= 2:
            penalty += self.KNIGHT_PENALTY
        print(f"Penalty for having knights: {penalty}")
        return penalty

    def isolated_pawn_penalty(self) -> float:
        """
        Calculate a penalty for isolated pawns.

        Returns:
            float: Total penalty for isolated pawns (positive for Black, negative for White).
        """
        penalty = 0
        for color in [chess.WHITE, chess.BLACK]:
            pawns = self.board.pieces(chess.PAWN, color)
            for square in pawns:
                file = chess.square_file(square)
                # Check adjacent files for pawns
                adjacent_files = {file - 1, file + 1}
                has_adjacent_pawn = any(
                    chess.square_file(p) in adjacent_files for p in pawns
                )
                if not has_adjacent_pawn:
                    penalty += -0.5 if color == chess.WHITE else 0.5
        print(f"Penalty for isolated pawns: {penalty}")
        return penalty

    def king_safety(self) -> float:
        """
        Evaluate the king's safety based on pawn shield, pawn storm, and king tropism.

        Returns:
            float: King safety score (positive for White, negative for Black).
        """
        score = 0
        for color in [chess.WHITE, chess.BLACK]:
            king_square = self.board.king(color)
            if king_square is None:
                continue  # In case the king is missing (unlikely in normal play)

            # Pawn shield evaluation
            shield_score = self.pawn_shield(king_square, color)

            # Pawn storm evaluation
            storm_score = self.pawn_storm(king_square, color)

            # King tropism evaluation
            tropism_score = self.king_tropism(king_square, color)

            # Combine the scores
            king_score = shield_score - storm_score - tropism_score
            score += king_score if color == chess.WHITE else -king_score
        print(f"King safety score: {score}")
        return score

    def pawn_shield(self, king_square, color) -> float:
        """
        Evaluate the king's pawn shield.

        Args:
            king_square (int): The square where the king is located.
            color (bool): The color of the king (True for White, False for Black).

        Returns:
            float: Pawn shield score.
        """
        score = 0
        king_file = chess.square_file(king_square)
        king_rank = chess.square_rank(king_square)
        shield_rank = king_rank + (-1 if color == chess.WHITE else 1)

        # Ensure the shield rank is within bounds
        if 0 <= shield_rank <= 7:
            shield_pawns = [
                chess.square(king_file + i, shield_rank)
                for i in [-1, 0, 1]
                if 0 <= king_file + i <= 7  # Check file bounds
            ]
            for pawn_square in shield_pawns:
                if self.board.piece_at(pawn_square) == chess.Piece(chess.PAWN, color):
                    score += 0.5  # Bonus for intact pawn shield
                elif self.board.piece_at(pawn_square):
                    score -= 0.2  # Penalty for missing or advanced pawns
        return score


    def pawn_storm(self, king_square, color) -> float:
        """
        Penalize enemy pawns advancing near the king.

        Args:
            king_square (int): The square where the king is located.
            color (bool): The color of the king (True for White, False for Black).

        Returns:
            float: Penalty for enemy pawn storm.
        """
        score = 0
        opponent_color = not color
        king_file = chess.square_file(king_square)
        for square in self.board.pieces(chess.PAWN, opponent_color):
            file = chess.square_file(square)
            if abs(file - king_file) <= 1:  # Nearby file
                rank_diff = abs(chess.square_rank(square) - chess.square_rank(king_square))
                if rank_diff <= 2:  # Near the king
                    score += 0.3  # Penalize pawn proximity
        return score

    def king_tropism(self, king_square, color) -> float:
        """
        Evaluate the proximity of opponent pieces to the king.

        Args:
            king_square (int): The square where the king is located.
            color (bool): The color of the king (True for White, False for Black).

        Returns:
            float: King tropism score.
        """
        score = 0
        opponent_color = not color
        for square in self.board.pieces(chess.QUEEN, opponent_color):
            distance = chess.square_distance(king_square, square)
            score += 2 / distance if distance > 0 else 5  # Queen has high influence

        for square in self.board.pieces(chess.ROOK, opponent_color):
            distance = chess.square_distance(king_square, square)
            score += 1 / distance if distance > 0 else 3

        for square in self.board.pieces(chess.BISHOP, opponent_color):
            distance = chess.square_distance(king_square, square)
            score += 0.8 / distance if distance > 0 else 2

        for square in self.board.pieces(chess.KNIGHT, opponent_color):
            distance = chess.square_distance(king_square, square)
            score += 0.5 / distance if distance > 0 else 1

        return score



    def evaluate(self) -> float:
        """
        Combine all evaluation factors.

        Returns:
            float: Final evaluation score (positive for White, negative for Black).
        """
        evaluation = 0

        evaluation += self.material_evaluation()
        evaluation += self.bishop_pair_bonus()
        evaluation += self.rook_pair_penalty()
        evaluation += self.knight_pair_penalty()
        evaluation += self.isolated_pawn_penalty()
        evaluation += self.king_safety()

        return evaluation
