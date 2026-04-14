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
        moves = pawn_moves(board_obj, row, col, color)
    elif kind == "R":
        moves = rook_moves(board, row, col, color)
    elif kind == "N":
        moves = knight_moves(board, row, col, color)
    elif kind == "B":
        moves = bishop_moves(board, row, col, color)
    elif kind == "Q":
        moves = queen_moves(board, row, col, color)
    elif kind == "K":
        moves = king_moves(board_obj, row, col, color)

    return moves


def pawn_moves(board_obj, row, col, color):
    board = board_obj.board
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

    # En passant
    if board_obj.move_log:
        last_move = board_obj.move_log[-1]
        if (last_move["moving_piece"] == enemy + "P" and 
            abs(last_move["start"][0] - last_move["end"][0]) == 2 and
            last_move["end"][0] == row and
            abs(last_move["end"][1] - col) == 1):
            # Can capture en passant
            moves.append((row + direction, last_move["end"][1]))

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


def king_moves(board_obj, row, col, color):
    board = board_obj.board
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

    # Castling
    if not board_obj.piece_states.get((row, col), {}).get('has_moved', False):
        # Kingside
        if (board[row][7] == color + "R" and 
            not board_obj.piece_states.get((row, 7), {}).get('has_moved', False) and
            board[row][5] == "--" and board[row][6] == "--"):
            moves.append((row, 6))
        # Queenside
        if (board[row][0] == color + "R" and 
            not board_obj.piece_states.get((row, 0), {}).get('has_moved', False) and
            board[row][1] == "--" and board[row][2] == "--" and board[row][3] == "--"):
            moves.append((row, 2))

    return moves