class Board:
    def __init__(self):
        self._setup_initial_position()

    def _setup_initial_position(self):
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bP"] * 8,
            ["--"] * 8,
            ["--"] * 8,
            ["--"] * 8,
            ["--"] * 8,
            ["wP"] * 8,
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"],
        ]
        self.white_to_move = True
        self.move_log = []
        self.en_passant_target = None
        self.piece_states = {}
        self.selected_square = None
        self.captured_white = []  # quân trắng đã ăn được (quân đen bị ăn)
        self.captured_black = []  # quân đen đã ăn được (quân trắng bị ăn)

    def reset(self):
        self._setup_initial_position()

    def get_piece(self, r, c):
        return self.board[r][c]

    def make_move(self, start, end):
        self.move_piece(start, end)

    def _record_capture(self, captured_piece):
        if captured_piece == "--":
            return
        if captured_piece[0] == "b":
            self.captured_white.append(captured_piece)
        else:
            self.captured_black.append(captured_piece)

    def _undo_capture(self, captured_piece):
        if captured_piece == "--":
            return
        if captured_piece[0] == "b":
            if self.captured_white:
                self.captured_white.pop()
        else:
            if self.captured_black:
                self.captured_black.pop()

    def move_piece(self, start, end):
        sr, sc = start
        er, ec = end

        piece = self.board[sr][sc]
        captured = self.board[er][ec]
        if piece == "--":
            return

        move = {
            "start": start,
            "end": end,
            "piece": piece,
            "moving_piece": piece,
            "captured": captured,
            "target_piece": captured,
            "promotion": None,
            "promotion_piece": None,
            "castling": None,
            "en_passant": None,
            "en_passant_target_prev": self.en_passant_target,
            "piece_states_prev": self.piece_states.copy(),
            "captured_white_prev_len": len(self.captured_white),
            "captured_black_prev_len": len(self.captured_black),
        }

        # En passant capture
        if piece[1] == "P" and self.en_passant_target is not None and (er, ec) == self.en_passant_target and captured == "--":
            cap_pos = (er + 1, ec) if piece[0] == "w" else (er - 1, ec)
            move["en_passant"] = cap_pos
            move["captured"] = self.board[cap_pos[0]][cap_pos[1]]
            move["target_piece"] = move["captured"]
            self.board[cap_pos[0]][cap_pos[1]] = "--"
            self._record_capture(move["captured"])
        elif captured != "--":
            self._record_capture(captured)

        # Move piece
        self.board[er][ec] = piece
        self.board[sr][sc] = "--"

        # Promotion (auto queen)
        if piece == "wP" and er == 0:
            self.board[er][ec] = "wQ"
            move["promotion"] = "wP"
            move["promotion_piece"] = "wQ"
        elif piece == "bP" and er == 7:
            self.board[er][ec] = "bQ"
            move["promotion"] = "bP"
            move["promotion_piece"] = "bQ"

        # Castling
        if piece[1] == "K" and abs(ec - sc) == 2:
            if ec > sc:
                rook_start = (sr, 7)
                rook_end = (sr, ec - 1)
            else:
                rook_start = (sr, 0)
                rook_end = (sr, ec + 1)

            rook_piece = self.board[rook_start[0]][rook_start[1]]
            self.board[rook_end[0]][rook_end[1]] = rook_piece
            self.board[rook_start[0]][rook_start[1]] = "--"
            move["castling"] = (rook_start, rook_end)
            self.piece_states[rook_end] = {"has_moved": True}
            if rook_start in self.piece_states:
                del self.piece_states[rook_start]

        # En passant target update
        if piece[1] == "P" and abs(er - sr) == 2:
            self.en_passant_target = ((sr + er) // 2, sc)
        else:
            self.en_passant_target = None

        # Update piece state
        self.piece_states[(er, ec)] = {"has_moved": True}
        if (sr, sc) in self.piece_states:
            del self.piece_states[(sr, sc)]

        self.move_log.append(move)
        self.selected_square = None
        self.white_to_move = not self.white_to_move

    def undo_move(self):
        if not self.move_log:
            return

        move = self.move_log.pop()
        sr, sc = move["start"]
        er, ec = move["end"]

        # Restore board squares
        self.board[sr][sc] = move["piece"]
        self.board[er][ec] = move["captured"]

        # Undo en passant
        if move["en_passant"]:
            r, c = move["en_passant"]
            self.board[er][ec] = "--"
            self.board[r][c] = move["captured"]

        # Undo castling rook move
        if move["castling"]:
            rook_start, rook_end = move["castling"]
            rook_piece = self.board[rook_end[0]][rook_end[1]]
            self.board[rook_start[0]][rook_start[1]] = rook_piece
            self.board[rook_end[0]][rook_end[1]] = "--"

        # Undo promotion
        if move["promotion"]:
            self.board[sr][sc] = move["promotion"]

        self.en_passant_target = move["en_passant_target_prev"]
        self.piece_states = move["piece_states_prev"].copy()
        self.selected_square = None
        self.white_to_move = not self.white_to_move

        # Restore captured lists to exact previous lengths
        self.captured_white = self.captured_white[:move["captured_white_prev_len"]]
        self.captured_black = self.captured_black[:move["captured_black_prev_len"]]
