# engine/board.py

class Board:
    def __init__(self):
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bP", "bP", "bP", "bP", "bP", "bP", "bP", "bP"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wP", "wP", "wP", "wP", "wP", "wP", "wP", "wP"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ]

        self.white_to_move = True
        self.selected_square = None
        self.captured_white = []
        self.captured_black = []
        self.move_log = []
        self.piece_states = {}  # Track piece states like has_moved
        self.initialize_piece_states()

    def initialize_piece_states(self):
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece != "--":
                    self.piece_states[(r, c)] = {'has_moved': False}

    def get_piece(self, row, col):
        return self.board[row][col]

    def set_piece(self, row, col, piece):
        self.board[row][col] = piece

    def move_piece(self, start, end):
        sr, sc = start
        er, ec = end

        moving_piece = self.board[sr][sc]
        target_piece = self.board[er][ec]
        promoted_from = None
        castling = False
        en_passant = False

        # Handle castling
        if moving_piece[1] == "K" and abs(sc - ec) == 2:
            castling = True
            # Move the rook
            if ec == 6:  # Kingside
                rook_start = (sr, 7)
                rook_end = (sr, 5)
            else:  # Queenside
                rook_start = (sr, 0)
                rook_end = (sr, 3)
            self.board[rook_end[0]][rook_end[1]] = self.board[rook_start[0]][rook_start[1]]
            self.board[rook_start[0]][rook_start[1]] = "--"
            # Update piece states for rook
            if rook_start in self.piece_states:
                self.piece_states[rook_end] = self.piece_states.pop(rook_start)
                self.piece_states[rook_end]['has_moved'] = True

        # Handle en passant
        if moving_piece[1] == "P" and sc != ec and target_piece == "--":
            en_passant = True
            # Remove the captured pawn
            captured_row = sr
            self.board[captured_row][ec] = "--"
            if moving_piece[0] == "w":
                self.captured_black.append("bP")
            else:
                self.captured_white.append("wP")

        if target_piece != "--" and not en_passant:
            if target_piece[0] == "w":
                self.captured_white.append(target_piece)
            else:
                self.captured_black.append(target_piece)

        self.board[er][ec] = moving_piece
        self.board[sr][sc] = "--"

        # Update piece states
        has_moved_before = self.piece_states.get(start, {}).get('has_moved', False)
        if start in self.piece_states:
            self.piece_states[end] = self.piece_states.pop(start)
            self.piece_states[end]['has_moved'] = True

        rook_has_moved_before = None
        if castling:
            rook_has_moved_before = self.piece_states.get(rook_start, {}).get('has_moved', False)

        # Check for pawn promotion (auto-promote to Queen for now)
        if moving_piece == "wP" and er == 0:
            promoted_from = "wP"
            self.board[er][ec] = "wQ"
        elif moving_piece == "bP" and er == 7:
            promoted_from = "bP"
            self.board[er][ec] = "bQ"

        self.move_log.append({
            "start": start,
            "end": end,
            "moving_piece": moving_piece,
            "target_piece": target_piece,
            "promoted_from": promoted_from,
            "castling": castling,
            "en_passant": en_passant,
            "has_moved_before": has_moved_before,
            "rook_has_moved_before": rook_has_moved_before,
        })
        self.white_to_move = not self.white_to_move

        return promoted_from

    def make_move(self, start, end):
        self.move_piece(start, end)

    def undo_move(self):
        if not self.move_log:
            return

        last_move = self.move_log.pop()
        (sr, sc) = last_move["start"]
        (er, ec) = last_move["end"]
        moving_piece = last_move["moving_piece"]
        target_piece = last_move["target_piece"]
        promoted_from = last_move.get("promoted_from")
        castling = last_move.get("castling", False)
        en_passant = last_move.get("en_passant", False)
        has_moved_before = last_move.get("has_moved_before", False)
        rook_has_moved_before = last_move.get("rook_has_moved_before")

        self.board[sr][sc] = moving_piece
        self.board[er][ec] = target_piece

        # Restore piece states
        if (er, ec) in self.piece_states:
            self.piece_states[(sr, sc)] = self.piece_states.pop((er, ec))
            self.piece_states[(sr, sc)]['has_moved'] = has_moved_before

        if castling:
            # Undo rook move
            if ec == 6:  # Kingside
                rook_start = (sr, 7)
                rook_end = (sr, 5)
            else:  # Queenside
                rook_start = (sr, 0)
                rook_end = (sr, 3)
            self.board[rook_start[0]][rook_start[1]] = self.board[rook_end[0]][rook_end[1]]
            self.board[rook_end[0]][rook_end[1]] = "--"
            # Restore rook state
            if rook_end in self.piece_states:
                self.piece_states[rook_start] = self.piece_states.pop(rook_end)
                self.piece_states[rook_start]['has_moved'] = rook_has_moved_before

        if en_passant:
            # Restore the captured pawn
            captured_row = sr
            captured_piece = "bP" if moving_piece[0] == "w" else "wP"
            self.board[captured_row][ec] = captured_piece
            if moving_piece[0] == "w":
                self.captured_black.pop()
            else:
                self.captured_white.pop()

        if target_piece != "--" and not en_passant:
            if target_piece[0] == "w" and self.captured_white:
                self.captured_white.pop()
            elif target_piece[0] == "b" and self.captured_black:
                self.captured_black.pop()

        if promoted_from:
            self.board[er][ec] = promoted_from

        self.white_to_move = not self.white_to_move
        self.selected_square = None

    def reset(self):
        self.__init__()
