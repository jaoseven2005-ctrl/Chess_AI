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
        self.captured_white = []   # quân trắng bị ăn
        self.captured_black = []   # quân đen bị ăn
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

        if target_piece != "--":
            if target_piece[0] == "w":
                self.captured_white.append(target_piece)
            else:
                self.captured_black.append(target_piece)

        self.board[er][ec] = moving_piece
        self.board[sr][sc] = "--"

        # phong cấp đơn giản: tốt lên cuối bàn thì thành hậu
        if moving_piece == "wP" and er == 0:
            self.board[er][ec] = "wQ"
        elif moving_piece == "bP" and er == 7:
            self.board[er][ec] = "bQ"

        self.move_log.append((start, end, moving_piece, target_piece))
        self.white_to_move = not self.white_to_move

    def reset(self):
        self.__init__()