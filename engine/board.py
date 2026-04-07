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

        if target_piece != "--":
            if target_piece[0] == "w":
                self.captured_white.append(target_piece)
            else:
                self.captured_black.append(target_piece)

        self.board[er][ec] = moving_piece
        self.board[sr][sc] = "--"

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
        })
        self.white_to_move = not self.white_to_move

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

        self.board[sr][sc] = moving_piece
        self.board[er][ec] = target_piece

        if target_piece != "--":
            if target_piece[0] == "w" and self.captured_white:
                self.captured_white.pop()
            elif target_piece[0] == "b" and self.captured_black:
                self.captured_black.pop()

        self.white_to_move = not self.white_to_move
        self.selected_square = None

    def reset(self):
        self.__init__()
