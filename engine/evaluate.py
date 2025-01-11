import chess

class Evaluation:
    """
    Enhanced evaluation that considers:
    - Material
    - Piece positioning
    - Pawn structure
    - King safety
    - Piece mobility
    - Development (in opening)
    """

    PIECE_VALUES = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000
    }

    # Piece-square tables (in centipawns)
    PAWN_TABLE = [
        [0,   0,   0,   0,   0,   0,   0,   0],
        [50,  50,  50,  50,  50,  50,  50,  50],
        [10,  10,  20,  30,  30,  20,  10,  10],
        [5,   5,  10,  25,  25,  10,   5,   5],
        [0,   0,   0,  20,  20,   0,   0,   0],
        [5,  -5, -10,   0,   0, -10,  -5,   5],
        [5,  10,  10, -20, -20,  10,  10,   5],
        [0,   0,   0,   0,   0,   0,   0,   0]
    ]

    KNIGHT_TABLE = [
        [-50, -40, -30, -30, -30, -30, -40, -50],
        [-40, -20,   0,   5,   5,   0, -20, -40],
        [-30,   5,  10,  15,  15,  10,   5, -30],
        [-30,   0,  15,  20,  20,  15,   0, -30],
        [-30,   5,  15,  20,  20,  15,   5, -30],
        [-30,   0,  10,  15,  15,  10,   0, -30],
        [-40, -20,   0,   0,   0,   0, -20, -40],
        [-50, -40, -30, -30, -30, -30, -40, -50]
    ]

    BISHOP_TABLE = [
        [-20, -10, -10, -10, -10, -10, -10, -20],
        [-10,   5,   0,   0,   0,   0,   5, -10],
        [-10,  10,  10,  10,  10,  10,  10, -10],
        [-10,   0,  10,  10,  10,  10,   0, -10],
        [-10,   5,   5,  10,  10,   5,   5, -10],
        [-10,   0,   5,  10,  10,   5,   0, -10],
        [-10,   0,   0,   0,   0,   0,   0, -10],
        [-20, -10, -10, -10, -10, -10, -10, -20]
    ]

    ROOK_TABLE = [
        [0,   0,   0,   5,   5,   0,   0,   0],
        [-5,   0,   0,   0,   0,   0,   0,  -5],
        [-5,   0,   0,   0,   0,   0,   0,  -5],
        [-5,   0,   0,   0,   0,   0,   0,  -5],
        [-5,   0,   0,   0,   0,   0,   0,  -5],
        [-5,   0,   0,   0,   0,   0,   0,  -5],
        [5,  10,  10,  10,  10,  10,  10,   5],
        [0,   0,   0,   0,   0,   0,   0,   0]
    ]

    QUEEN_TABLE = [
        [-20, -10, -10,  -5,  -5, -10, -10, -20],
        [-10,   0,   5,   0,   0,   0,   0, -10],
        [-10,   5,   5,   5,   5,   5,   0, -10],
        [0,   0,   5,   5,   5,   5,   0,  -5],
        [-5,   0,   5,   5,   5,   5,   0,  -5],
        [-10,   0,   5,   5,   5,   5,   0, -10],
        [-10,   0,   0,   0,   0,   0,   0, -10],
        [-20, -10, -10,  -5,  -5, -10, -10, -20]
    ]

    KING_TABLE_MIDDLEGAME = [
        [20,  30,  10,   0,   0,  10,  30,  20],
        [20,  20,   0,   0,   0,   0,  20,  20],
        [-10, -20, -20, -20, -20, -20, -20, -10],
        [-20, -30, -30, -40, -40, -30, -30, -20],
        [-30, -40, -40, -50, -50, -40, -40, -30],
        [-30, -40, -40, -50, -50, -40, -40, -30],
        [-30, -40, -40, -50, -50, -40, -40, -30],
        [-30, -40, -40, -50, -50, -40, -40, -30]
    ]

    KING_TABLE_ENDGAME = [
        [-50, -30, -30, -30, -30, -30, -30, -50],
        [-30, -30,   0,   0,   0,   0, -30, -30],
        [-30, -10,  20,  30,  30,  20, -10, -30],
        [-30, -10,  30,  40,  40,  30, -10, -30],
        [-30, -10,  30,  40,  40,  30, -10, -30],
        [-30, -10,  20,  30,  30,  20, -10, -30],
        [-30, -20, -10,   0,   0, -10, -20, -30],
        [-50, -40, -30, -20, -20, -30, -40, -50]
    ]

    CHECKMATE = 1000000
    STALEMATE = 0
    SIDE_TO_MOVE_BONUS = 10

    def __init__(self, board: chess.Board):
        self.board = board

    def is_endgame(self) -> bool:
        """
        Determines if the position is in the endgame.
        Simple version: endgame starts when both sides have no queens or
        one side has a queen and the other has no other pieces except pawns.
        """
        queens = len(self.board.pieces(chess.QUEEN, chess.WHITE)) + \
                 len(self.board.pieces(chess.QUEEN, chess.BLACK))
        minor_pieces = len(self.board.pieces(chess.KNIGHT, chess.WHITE)) + \
                       len(self.board.pieces(chess.KNIGHT, chess.BLACK)) + \
                       len(self.board.pieces(chess.BISHOP, chess.WHITE)) + \
                       len(self.board.pieces(chess.BISHOP, chess.BLACK))

        return queens == 0 or (queens == 1 and minor_pieces <= 2)

    def get_piece_table_value(self, piece: chess.Piece, square: chess.Square) -> int:
        """Returns the piece-square table value for a given piece and square."""
        rank = chess.square_rank(square)
        file = chess.square_file(square)

        # Flip table coordinates for black pieces
        if not piece.color:
            rank = 7 - rank

        if piece.piece_type == chess.PAWN:
            return self.PAWN_TABLE[rank][file]
        elif piece.piece_type == chess.KNIGHT:
            return self.KNIGHT_TABLE[rank][file]
        elif piece.piece_type == chess.BISHOP:
            return self.BISHOP_TABLE[rank][file]
        elif piece.piece_type == chess.ROOK:
            return self.ROOK_TABLE[rank][file]
        elif piece.piece_type == chess.QUEEN:
            return self.QUEEN_TABLE[rank][file]
        elif piece.piece_type == chess.KING:
            if self.is_endgame():
                return self.KING_TABLE_ENDGAME[rank][file]
            return self.KING_TABLE_MIDDLEGAME[rank][file]
        return 0

    def evaluate_pawn_structure(self) -> int:
        """Evaluates pawn structure including doubled, isolated, and passed pawns."""
        score = 0
        white_pawn_files = [0] * 8
        black_pawn_files = [0] * 8

        # Count pawns on each file
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece and piece.piece_type == chess.PAWN:
                file = chess.square_file(square)
                if piece.color:
                    white_pawn_files[file] += 1
                else:
                    black_pawn_files[file] += 1

        # Evaluate doubled and isolated pawns
        for file in range(8):
            # Doubled pawns penalty
            if white_pawn_files[file] > 1:
                score -= 20 * (white_pawn_files[file] - 1)
            if black_pawn_files[file] > 1:
                score += 20 * (black_pawn_files[file] - 1)

            # Isolated pawns penalty
            if white_pawn_files[file] > 0:
                if (file == 0 or white_pawn_files[file-1] == 0) and \
                        (file == 7 or white_pawn_files[file+1] == 0):
                    score -= 10
            if black_pawn_files[file] > 0:
                if (file == 0 or black_pawn_files[file-1] == 0) and \
                        (file == 7 or black_pawn_files[file+1] == 0):
                    score += 10

        return score

    def evaluate_mobility(self) -> int:
        """Evaluates piece mobility (number of legal moves available)."""
        original_turn = self.board.turn

        # Count mobility for white
        self.board.turn = chess.WHITE
        white_mobility = len(list(self.board.legal_moves))

        # Count mobility for black
        self.board.turn = chess.BLACK
        black_mobility = len(list(self.board.legal_moves))

        # Restore original turn
        self.board.turn = original_turn

        return (white_mobility - black_mobility) * 2

    def evaluate_material_and_position(self) -> float:
        """Original material and piece-square table evaluation"""
        score = 0

        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece is not None:
                # Material score
                value = self.PIECE_VALUES[piece.piece_type]
                if piece.color == chess.WHITE:
                    score += value
                else:
                    score -= value

                # Position score
                position_score = self.get_piece_table_value(piece, square)
                if piece.color == chess.WHITE:
                    score += position_score
                else:
                    score -= position_score

        return score

    def count_pieces(self, color: bool) -> int:
        """Count number of pieces (excluding pawns and king)"""
        count = 0
        for piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
            count += len(self.board.pieces(piece_type, color))
        return count

    def evaluate_pawn_advancement(self, white_winning: bool) -> float:
        """Evaluate pawn advancement towards promotion"""
        score = 0
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece and piece.piece_type == chess.PAWN:
                rank = chess.square_rank(square)
                if piece.color == chess.WHITE:
                    score += rank * 10  # Higher rank = better for white
                else:
                    score += (7 - rank) * 10  # Lower rank = better for black

        return score if white_winning else -score

    def evaluate_king_proximity(self, white_winning: bool) -> float:
        """Evaluate king proximity in winning positions"""
        score = 0
        white_king = self.board.king(chess.WHITE)
        black_king = self.board.king(chess.BLACK)

        if white_king and black_king:
            distance = chess.square_distance(white_king, black_king)
            if white_winning:
                score -= distance * 10  # White king should get closer
            else:
                score += distance * 10  # Black king should get closer

        return score

    def evaluate_piece_centralization(self, white_winning: bool) -> float:
        """Evaluate piece centralization in winning positions"""
        score = 0
        central_squares = [chess.E4, chess.D4, chess.E5, chess.D5]

        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece and piece.piece_type != chess.KING and piece.piece_type != chess.PAWN:
                # Calculate distance to center
                min_distance = min(chess.square_distance(square, center) for center in central_squares)
                piece_score = (4 - min_distance) * 5  # 5 points per square closer to center

                if piece.color == chess.WHITE:
                    score += piece_score
                else:
                    score -= piece_score

        return score if white_winning else -score

    def evaluate_winning_position(self, white_winning: bool) -> float:
        """
        Additional evaluation terms for winning positions
        """
        score = 0

        # 1. Encourage piece exchanges when ahead
        piece_count_diff = self.count_pieces(chess.WHITE) - self.count_pieces(chess.BLACK)
        if white_winning:
            score -= piece_count_diff * 10  # White wants to trade when winning
        else:
            score += piece_count_diff * 10  # Black wants to trade when winning

        # 2. Evaluate pawn advancement
        score += self.evaluate_pawn_advancement(white_winning)

        # 3. Evaluate king proximity in winning positions
        score += self.evaluate_king_proximity(white_winning)

        # 4. Evaluate piece centralization
        score += self.evaluate_piece_centralization(white_winning)

        return score if white_winning else -score

    def evaluate_material(self) -> float:
        """Pure material evaluation"""
        score = 0
        for piece_type in chess.PIECE_TYPES:
            score += len(self.board.pieces(piece_type, chess.WHITE)) * self.PIECE_VALUES[piece_type]
            score -= len(self.board.pieces(piece_type, chess.BLACK)) * self.PIECE_VALUES[piece_type]
        return score

    def evaluate(self) -> float:
        """
        Main evaluation function.
        Returns score from White's perspective.
        """
        if self.board.is_checkmate():
            return -self.CHECKMATE if self.board.turn else self.CHECKMATE
        if self.board.is_stalemate() or self.board.is_insufficient_material():
            return 0

        # Basic material and position evaluation
        score = self.evaluate_material_and_position()

        # Additional evaluation for winning positions
        material_diff = self.evaluate_material()
        if abs(material_diff) > 200:  # If someone is clearly winning
            score += self.evaluate_winning_position(material_diff > 0)

        return score

