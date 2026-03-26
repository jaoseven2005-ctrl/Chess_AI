# engine/moves.py

def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def get_valid_moves(board_obj, row, col):
    board = board_obj.board
    piece = board[row][col]

    if piece == "--":
        return []

    color = piece[0]
    kind = piece[1]

    moves = []

    if kind == "P":
        moves = pawn_moves(board, row, col, color)
    elif kind == "R":
        moves = rook_moves(board, row, col, color)
    elif kind == "N":
        moves = knight_moves(board, row, col, color)
    elif kind == "B":
        moves = bishop_moves(board, row, col, color)
    elif kind == "Q":
        moves = queen_moves(board, row, col, color)
    elif kind == "K":
        moves = king_moves(board, row, col, color)

    return moves


def pawn_moves(board, row, col, color):
    moves = []
    direction = -1 if color == "w" else 1
    start_row = 6 if color == "w" else 1
    enemy = "b" if color == "w" else "w"

    # đi 1 ô
    nr = row + direction
    if in_bounds(nr, col) and board[nr][col] == "--":
        moves.append((nr, col))

        # đi 2 ô ở vị trí ban đầu
        nr2 = row + 2 * direction
        if row == start_row and in_bounds(nr2, col) and board[nr2][col] == "--":
            moves.append((nr2, col))

    # ăn chéo
    for dc in [-1, 1]:
        nc = col + dc
        nr = row + direction
        if in_bounds(nr, nc) and board[nr][nc] != "--" and board[nr][nc][0] == enemy:
            moves.append((nr, nc))

    return moves


def rook_moves(board, row, col, color):
    moves = []
    directions = [(-1,0), (1,0), (0,-1), (0,1)]
    enemy = "b" if color == "w" else "w"

    for dr, dc in directions:
        r, c = row + dr, col + dc
        while in_bounds(r, c):
            if board[r][c] == "--":
                moves.append((r, c))
            else:
                if board[r][c][0] == enemy:
                    moves.append((r, c))
                break
            r += dr
            c += dc

    return moves


def bishop_moves(board, row, col, color):
    moves = []
    directions = [(-1,-1), (-1,1), (1,-1), (1,1)]
    enemy = "b" if color == "w" else "w"

    for dr, dc in directions:
        r, c = row + dr, col + dc
        while in_bounds(r, c):
            if board[r][c] == "--":
                moves.append((r, c))
            else:
                if board[r][c][0] == enemy:
                    moves.append((r, c))
                break
            r += dr
            c += dc

    return moves


def knight_moves(board, row, col, color):
    moves = []
    enemy = "b" if color == "w" else "w"
    directions = [
        (-2,-1), (-2,1), (-1,-2), (-1,2),
        (1,-2), (1,2), (2,-1), (2,1)
    ]

    for dr, dc in directions:
        r, c = row + dr, col + dc
        if in_bounds(r, c):
            if board[r][c] == "--" or board[r][c][0] == enemy:
                moves.append((r, c))

    return moves


def queen_moves(board, row, col, color):
    return rook_moves(board, row, col, color) + bishop_moves(board, row, col, color)


def king_moves(board, row, col, color):
    moves = []
    enemy = "b" if color == "w" else "w"
    directions = [
        (-1,-1), (-1,0), (-1,1),
        (0,-1),          (0,1),
        (1,-1),  (1,0),  (1,1)
    ]

    for dr, dc in directions:
        r, c = row + dr, col + dc
        if in_bounds(r, c):
            if board[r][c] == "--" or board[r][c][0] == enemy:
                moves.append((r, c))

    return moves