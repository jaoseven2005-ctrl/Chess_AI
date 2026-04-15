# engine/moves.py

def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def find_king(board_obj, color):
    target = color + "K"
    for r in range(8):
        for c in range(8):
            if board_obj.board[r][c] == target:
                return r, c
    return None


def is_square_attacked(board_obj, target_row, target_col, attacker_color):
    board = board_obj.board

    # Pawn attacks
    direction = -1 if attacker_color == "w" else 1
    for dc in (-1, 1):
        nr = target_row - direction
        nc = target_col - dc
        if in_bounds(nr, nc) and board[nr][nc] == attacker_color + "P":
            return True

    # Knight attacks
    for dr, dc in [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]:
        nr, nc = target_row + dr, target_col + dc
        if in_bounds(nr, nc) and board[nr][nc] == attacker_color + "N":
            return True

    # Bishop / Queen diagonals
    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        r, c = target_row + dr, target_col + dc
        while in_bounds(r, c):
            piece = board[r][c]
            if piece != "--":
                if piece == attacker_color + "B" or piece == attacker_color + "Q":
                    return True
                break
            r += dr
            c += dc

    # Rook / Queen lines
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        r, c = target_row + dr, target_col + dc
        while in_bounds(r, c):
            piece = board[r][c]
            if piece != "--":
                if piece == attacker_color + "R" or piece == attacker_color + "Q":
                    return True
                break
            r += dr
            c += dc

    # King attacks
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = target_row + dr, target_col + dc
            if in_bounds(nr, nc) and board[nr][nc] == attacker_color + "K":
                return True

    return False


def is_in_check(board_obj, color):
    king_pos = find_king(board_obj, color)
    if king_pos is None:
        return True
    enemy = "b" if color == "w" else "w"
    return is_square_attacked(board_obj, king_pos[0], king_pos[1], enemy)


def get_valid_moves(board_obj, row, col):
    board = board_obj.board
    piece = board[row][col]
    if piece == "--":
        return []

    color = piece[0]
    kind = piece[1]

    if kind == "P":
        return pawn_moves(board_obj, row, col, color)
    if kind == "R":
        return rook_moves(board, row, col, color)
    if kind == "N":
        return knight_moves(board, row, col, color)
    if kind == "B":
        return bishop_moves(board, row, col, color)
    if kind == "Q":
        return queen_moves(board, row, col, color)
    if kind == "K":
        return king_moves(board_obj, row, col, color)
    return []


def pawn_moves(board_obj, row, col, color):
    board = board_obj.board
    moves = []
    direction = -1 if color == "w" else 1
    start_row = 6 if color == "w" else 1
    enemy = "b" if color == "w" else "w"

    nr = row + direction
    if in_bounds(nr, col) and board[nr][col] == "--":
        moves.append((nr, col))
        nr2 = row + 2 * direction
        if row == start_row and in_bounds(nr2, col) and board[nr2][col] == "--":
            moves.append((nr2, col))

    for dc in (-1, 1):
        nc = col + dc
        nr = row + direction
        if in_bounds(nr, nc) and board[nr][nc] != "--" and board[nr][nc][0] == enemy:
            moves.append((nr, nc))

    # En passant based on dedicated target square
    if board_obj.en_passant_target is not None:
        target_r, target_c = board_obj.en_passant_target
        if target_r == row + direction and abs(target_c - col) == 1:
            side_piece = board[row][target_c]
            if side_piece == enemy + "P":
                moves.append((target_r, target_c))

    return moves


def rook_moves(board, row, col, color):
    moves = []
    enemy = "b" if color == "w" else "w"
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
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
    enemy = "b" if color == "w" else "w"
    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
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
    for dr, dc in [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]:
        r, c = row + dr, col + dc
        if in_bounds(r, c) and (board[r][c] == "--" or board[r][c][0] == enemy):
            moves.append((r, c))
    return moves


def queen_moves(board, row, col, color):
    return rook_moves(board, row, col, color) + bishop_moves(board, row, col, color)


def king_moves(board_obj, row, col, color):
    board = board_obj.board
    moves = []
    enemy = "b" if color == "w" else "w"

    for dr, dc in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
        r, c = row + dr, col + dc
        if in_bounds(r, c) and (board[r][c] == "--" or board[r][c][0] == enemy):
            moves.append((r, c))

    # Castling
    if not board_obj.piece_states.get((row, col), {}).get("has_moved", False):
        if (board[row][7] == color + "R"
                and not board_obj.piece_states.get((row, 7), {}).get("has_moved", False)
                and board[row][5] == "--" and board[row][6] == "--"
                and not is_in_check(board_obj, color)
                and not is_square_attacked(board_obj, row, 5, enemy)
                and not is_square_attacked(board_obj, row, 6, enemy)):
            moves.append((row, 6))

        if (board[row][0] == color + "R"
                and not board_obj.piece_states.get((row, 0), {}).get("has_moved", False)
                and board[row][1] == "--" and board[row][2] == "--" and board[row][3] == "--"
                and not is_in_check(board_obj, color)
                and not is_square_attacked(board_obj, row, 3, enemy)
                and not is_square_attacked(board_obj, row, 2, enemy)):
            moves.append((row, 2))

    return moves
