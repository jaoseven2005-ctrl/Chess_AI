import random
import time
from engine.moves import get_valid_moves

PIECE_SCORE = {"K": 0, "Q": 9, "R": 5, "B": 3.25, "N": 3, "P": 1}

KNIGHT_SCORES = [[0.0, 0.1, 0.2, 0.2, 0.2, 0.2, 0.1, 0.0],
                 [0.1, 0.3, 0.5, 0.5, 0.5, 0.5, 0.3, 0.1],
                 [0.2, 0.5, 0.6, 0.65, 0.65, 0.6, 0.5, 0.2],
                 [0.2, 0.55, 0.65, 0.7, 0.7, 0.65, 0.55, 0.2],
                 [0.2, 0.5, 0.65, 0.7, 0.7, 0.65, 0.5, 0.2],
                 [0.2, 0.55, 0.6, 0.65, 0.65, 0.6, 0.55, 0.2],
                 [0.1, 0.3, 0.5, 0.55, 0.55, 0.5, 0.3, 0.1],
                 [0.0, 0.1, 0.2, 0.2, 0.2, 0.2, 0.1, 0.0]]

BISHOP_SCORES = [[0.0, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.0],
                 [0.2, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.2],
                 [0.2, 0.4, 0.5, 0.6, 0.6, 0.5, 0.4, 0.2],
                 [0.2, 0.5, 0.5, 0.6, 0.6, 0.5, 0.5, 0.2],
                 [0.2, 0.4, 0.6, 0.6, 0.6, 0.6, 0.4, 0.2],
                 [0.2, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.2],
                 [0.2, 0.5, 0.4, 0.4, 0.4, 0.4, 0.5, 0.2],
                 [0.0, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.0]]

ROOK_SCORES = [[0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25],
               [0.5, 0.75, 0.75, 0.75, 0.75, 0.75, 0.75, 0.5],
               [0.0, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.0],
               [0.0, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.0],
               [0.0, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.0],
               [0.0, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.0],
               [0.0, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.0],
               [0.25, 0.25, 0.25, 0.5, 0.5, 0.25, 0.25, 0.25]]

QUEEN_SCORES = [[0.0, 0.2, 0.2, 0.3, 0.3, 0.2, 0.2, 0.0],
                [0.2, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.2],
                [0.2, 0.4, 0.5, 0.5, 0.5, 0.5, 0.4, 0.2],
                [0.3, 0.4, 0.5, 0.5, 0.5, 0.5, 0.4, 0.3],
                [0.4, 0.4, 0.5, 0.5, 0.5, 0.5, 0.4, 0.3],
                [0.2, 0.5, 0.5, 0.5, 0.5, 0.5, 0.4, 0.2],
                [0.2, 0.4, 0.5, 0.4, 0.4, 0.4, 0.4, 0.2],
                [0.0, 0.2, 0.2, 0.3, 0.3, 0.2, 0.2, 0.0]]

PAWN_SCORES = [[0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8],
               [0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7],
               [0.3, 0.3, 0.4, 0.5, 0.5, 0.4, 0.3, 0.3],
               [0.25, 0.25, 0.3, 0.45, 0.45, 0.3, 0.25, 0.25],
               [0.2, 0.2, 0.2, 0.4, 0.4, 0.2, 0.2, 0.2],
               [0.25, 0.15, 0.1, 0.2, 0.2, 0.1, 0.15, 0.25],
               [0.25, 0.3, 0.3, 0.0, 0.0, 0.3, 0.3, 0.25],
               [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2]]

POSITION_SCORES = {
    "wN": KNIGHT_SCORES,
    "bN": KNIGHT_SCORES[::-1],
    "wB": BISHOP_SCORES,
    "bB": BISHOP_SCORES[::-1],
    "wQ": QUEEN_SCORES,
    "bQ": QUEEN_SCORES[::-1],
    "wR": ROOK_SCORES,
    "bR": ROOK_SCORES[::-1],
    "wP": PAWN_SCORES,
    "bP": PAWN_SCORES[::-1],
}

CHECKMATE = 100000
STALEMATE = 0

LEVEL_SETTINGS = {
    "easy": {
        "min_depth": 1,
        "max_depth": 2,
        "random_rate": 0.30,
        "center_bonus": 0.10,
        "use_position_score": False,
        "time_limit": 1.0,
    },
    "normal": {
        "min_depth": 2,
        "max_depth": 3,
        "random_rate": 0.08,
        "center_bonus": 0.15,
        "use_position_score": False,
        "time_limit": 2.0,
    },
    "hard": {
        "min_depth": 4,
        "max_depth": 5,
        "random_rate": 0.0,
        "center_bonus": 0.20,
        "use_position_score": True,
        "time_limit": 3.0,
    },
}

# Cho AI bớt "máy móc"
OPENING_DEPTH = 2
MIDDLEGAME_DEPTH = 3
ENDGAME_DEPTH = 3

CENTER_SQUARES = {(3, 3), (3, 4), (4, 3), (4, 4)}
EXTENDED_CENTER = {
    (2, 2), (2, 3), (2, 4), (2, 5),
    (3, 2), (3, 3), (3, 4), (3, 5),
    (4, 2), (4, 3), (4, 4), (4, 5),
    (5, 2), (5, 3), (5, 4), (5, 5),
}

transposition_table = {}


def hash_board(board_obj):
    return (tuple(tuple(row) for row in board_obj.board), board_obj.white_to_move)


def count_pieces(board_obj):
    count = 0
    for row in board_obj.board:
        for piece in row:
            if piece != "--":
                count += 1
    return count


def get_search_depth(board_obj, level):
    level = level.lower() if isinstance(level, str) else "normal"
    settings = LEVEL_SETTINGS.get(level, LEVEL_SETTINGS["normal"])
    pieces = count_pieces(board_obj)

    if level == "easy":
        return settings["min_depth"] if pieces >= 18 else settings["max_depth"]
    if level == "normal":
        return settings["min_depth"] if pieces >= 20 else settings["max_depth"]
    return settings["min_depth"] if pieces >= 16 else settings["max_depth"]


def find_king(board_obj, color):
    target = color + "K"
    for r in range(8):
        for c in range(8):
            if board_obj.board[r][c] == target:
                return r, c
    return None


def is_square_attacked(board_obj, target_row, target_col, attacker_color):
    board = board_obj.board
    # Tối ưu: implement trực tiếp thay vì gọi get_valid_moves nhiều lần
    enemy = "b" if attacker_color == "w" else "w"

    # Pawn attacks
    direction = -1 if attacker_color == "w" else 1
    for dc in (-1, 1):
        nr = target_row - direction
        nc = target_col - dc
        if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == attacker_color + "P":
            return True

    # Knight attacks
    knight_dirs = [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]
    for dr, dc in knight_dirs:
        nr, nc = target_row + dr, target_col + dc
        if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == attacker_color + "N":
            return True

    # Bishop/Queen diagonal
    for dr, dc in [(-1,-1), (-1,1), (1,-1), (1,1)]:
        r, c = target_row + dr, target_col + dc
        while 0 <= r < 8 and 0 <= c < 8:
            piece = board[r][c]
            if piece != "--":
                if piece == attacker_color + "B" or piece == attacker_color + "Q":
                    return True
                break
            r += dr
            c += dc

    # Rook/Queen straight
    for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
        r, c = target_row + dr, target_col + dc
        while 0 <= r < 8 and 0 <= c < 8:
            piece = board[r][c]
            if piece != "--":
                if piece == attacker_color + "R" or piece == attacker_color + "Q":
                    return True
                break
            r += dr
            c += dc

    # King attacks
    for dr in (-1,0,1):
        for dc in (-1,0,1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = target_row + dr, target_col + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == attacker_color + "K":
                return True

    return False


def is_in_check(board_obj, color):
    king_pos = find_king(board_obj, color)
    if king_pos is None:
        return True
    enemy = "b" if color == "w" else "w"
    return is_square_attacked(board_obj, king_pos[0], king_pos[1], enemy)


def get_legal_moves_for_piece(board_obj, row, col):
    piece = board_obj.board[row][col]
    if piece == "--":
        return []

    color = piece[0]
    legal_moves = []
    for move in get_valid_moves(board_obj, row, col):
        board_obj.make_move((row, col), move)
        if not is_in_check(board_obj, color):
            legal_moves.append(move)
        board_obj.undo_move()
    return legal_moves


def get_all_legal_moves(board_obj):
    moves = []
    current_color = "w" if board_obj.white_to_move else "b"
    for row in range(8):
        for col in range(8):
            piece = board_obj.board[row][col]
            if piece != "--" and piece[0] == current_color:
                for end in get_legal_moves_for_piece(board_obj, row, col):
                    moves.append(((row, col), end))
    return moves


def count_legal_moves_for_color(board_obj, color):
    original_turn = board_obj.white_to_move
    board_obj.white_to_move = (color == "w")
    moves = get_all_legal_moves(board_obj)
    board_obj.white_to_move = original_turn
    return len(moves)


def opening_bonus(piece, start, end, piece_count):
    if piece_count < 26:
        return 0

    sr, sc = start
    er, ec = end
    bonus = 0

    if piece[1] in ("N", "B") and end in EXTENDED_CENTER:
        bonus += 0.35

    if piece[1] == "P" and end in CENTER_SQUARES:
        bonus += 0.25

    if piece[1] == "Q" and sr in (0, 7):
        bonus -= 0.30

    if piece[1] == "R" and sr in (0, 7) and sc in (0, 7):
        bonus -= 0.10

    return bonus


def move_order_score(board_obj, move):
    (sr, sc), (er, ec) = move
    piece = board_obj.board[sr][sc]
    target = board_obj.board[er][ec]

    score = 0.0

    if target != "--":
        score += 100 * PIECE_SCORE[target[1]] - PIECE_SCORE[piece[1]]

    # Promotion bonus
    if piece[1] == "P" and ((piece[0] == "w" and er == 0) or (piece[0] == "b" and er == 7)):
        score += 90  # High bonus for promotion

    if (er, ec) in CENTER_SQUARES:
        score += 1.2
    elif (er, ec) in EXTENDED_CENTER:
        score += 0.4

    score += PIECE_SCORE[piece[1]] * 0.08
    score += opening_bonus(piece, (sr, sc), (er, ec), count_pieces(board_obj))

    # Tối ưu: hạn chế make_move/undo, chỉ check check nếu cần
    # Giả sử check chỉ khi capture hoặc promotion
    if target != "--" or (piece[1] == "P" and ((piece[0] == "w" and er == 0) or (piece[0] == "b" and er == 7))):
        board_obj.make_move(*move)
        opponent_color = "b" if not board_obj.white_to_move else "w"
        if is_in_check(board_obj, opponent_color):
            score += 15.0
        board_obj.undo_move()

    return score


def order_moves(board_obj, moves):
    return sorted(moves, key=lambda mv: move_order_score(board_obj, mv), reverse=True)


def get_capture_moves(board_obj):
    moves = []
    current_color = "w" if board_obj.white_to_move else "b"
    for row in range(8):
        for col in range(8):
            piece = board_obj.board[row][col]
            if piece != "--" and piece[0] == current_color:
                for end in get_legal_moves_for_piece(board_obj, row, col):
                    if board_obj.board[end[0]][end[1]] != "--":
                        moves.append(((row, col), end))
    return moves


def quiescence_search(board_obj, alpha, beta, turn_multiplier, level, max_depth=None):
    stand_pat = turn_multiplier * evaluate_board(board_obj, level)
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat

    if max_depth is not None and max_depth <= 0:
        return alpha

    # Tối ưu: chỉ generate capture moves thay vì all moves
    capture_moves = get_capture_moves(board_obj)
    if not capture_moves:
        return alpha

    for move in order_moves(board_obj, capture_moves):
        board_obj.make_move(*move)
        # Giới hạn depth max 3 cho quiescence search
        score = -quiescence_search(board_obj, -beta, -alpha, -turn_multiplier, level, max_depth=3 if max_depth is None else max_depth - 1)
        board_obj.undo_move()

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


def evaluate_pawn_structure(board_obj):
    score = 0.0
    board = board_obj.board
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece == "--" or piece[1] != "P":
                continue
            color = piece[0]
            has_adjacent_file_pawn = False
            for nc in (col - 1, col + 1):
                if 0 <= nc < 8:
                    for r in range(8):
                        if board[r][nc] == color + "P":
                            has_adjacent_file_pawn = True
                            break
                if has_adjacent_file_pawn:
                    break
            if not has_adjacent_file_pawn:
                score += 0.18 if color == "w" else -0.18
    return score


def evaluate_mobility(board_obj):
    # Tối ưu: chỉ tính 2 lần cho white và black
    current_turn = board_obj.white_to_move
    board_obj.white_to_move = True
    white_mobility = len(get_all_legal_moves(board_obj))
    board_obj.white_to_move = False
    black_mobility = len(get_all_legal_moves(board_obj))
    board_obj.white_to_move = current_turn
    return 0.04 * (white_mobility - black_mobility)


def evaluate_king_safety(board_obj):
    score = 0.0
    for color in ("w", "b"):
        king_pos = find_king(board_obj, color)
        if king_pos is None:
            continue

        kr, kc = king_pos
        defenders = 0
        attackers_near = 0
        enemy = "b" if color == "w" else "w"

        # Đếm số quân bảo vệ vua (pawn và pieces gần)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr = kr + dr
                nc = kc + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    piece = board_obj.board[nr][nc]
                    if piece != "--" and piece[0] == color:
                        if piece[1] == "P":
                            defenders += 1
                        else:
                            defenders += 0.5  # Pieces khác ít quan trọng hơn

        # Kiểm tra vua có bị tấn công không
        in_check = is_in_check(board_obj, color)
        if in_check:
            attackers_near += 1  # Penalty cho check

        # Penalty nếu vua ở góc hoặc biên
        edge_penalty = 0
        if kr in (0, 7) or kc in (0, 7):
            edge_penalty = 0.2
        if (kr in (0, 7) and kc in (0, 7)):
            edge_penalty = 0.4  # Góc tệ hơn

        local_score = 0.1 * defenders - 0.3 * attackers_near - edge_penalty

        if color == "w":
            score += local_score
        else:
            score -= local_score

    return score


def score_board(board_obj):
    current_color = "w" if board_obj.white_to_move else "b"
    legal_moves = get_all_legal_moves(board_obj)

    if not legal_moves:
        if is_in_check(board_obj, current_color):
            return -CHECKMATE if current_color == "w" else CHECKMATE
        return STALEMATE

    score = 0
    piece_count = count_pieces(board_obj)

    for row in range(8):
        for col in range(8):
            piece = board_obj.board[row][col]
            if piece == "--":
                continue

            piece_value = PIECE_SCORE[piece[1]]
            position_value = POSITION_SCORES.get(piece, [[0] * 8 for _ in range(8)])[row][col]

            local = piece_value + position_value

            if piece[1] in ("N", "B") and (row, col) in EXTENDED_CENTER:
                local += 0.10

            if piece[1] == "Q" and piece_count >= 26:
                if row not in (0, 7):
                    local -= 0.20

            if piece[0] == "w":
                score += local
            else:
                score -= local

    score += evaluate_mobility(board_obj)
    score += evaluate_king_safety(board_obj)
    score += evaluate_pawn_structure(board_obj)

    if is_in_check(board_obj, "b"):
        score += 0.35
    if is_in_check(board_obj, "w"):
        score -= 0.35

    # Endgame: King centralization
    if piece_count <= 12:  # Endgame khi ít quân
        for color in ("w", "b"):
            king_pos = find_king(board_obj, color)
            if king_pos:
                kr, kc = king_pos
                center_distance = abs(3.5 - kr) + abs(3.5 - kc)
                king_bonus = max(0, 1.5 - center_distance * 0.3)
                if color == "w":
                    score += king_bonus
                else:
                    score -= king_bonus

    return score


def evaluate_material(board_obj):
    score = 0
    for row in board_obj.board:
        for piece in row:
            if piece == "--":
                continue
            value = PIECE_SCORE[piece[1]]
            score += value if piece[0] == "w" else -value
    return score


def evaluate_board(board_obj, level):
    level = level.lower() if isinstance(level, str) else "normal"
    legal_moves = get_all_legal_moves(board_obj)
    current_color = "w" if board_obj.white_to_move else "b"

    if not legal_moves:
        if is_in_check(board_obj, current_color):
            return -CHECKMATE if current_color == "w" else CHECKMATE
        return STALEMATE

    if level == "easy":
        score = evaluate_material(board_obj)
        # Thêm bonus khi chiếu ngay cả easy
        if is_in_check(board_obj, "b"):
            score += 0.5
        if is_in_check(board_obj, "w"):
            score -= 0.5
        return score

    if level == "normal":
        score = evaluate_material(board_obj)
        for row in range(8):
            for col in range(8):
                piece = board_obj.board[row][col]
                if piece == "--":
                    continue
                sign = 1 if piece[0] == "w" else -1
                if (row, col) in CENTER_SQUARES:
                    score += sign * 0.12
                elif (row, col) in EXTENDED_CENTER:
                    score += sign * 0.05
        score += evaluate_pawn_structure(board_obj)
        score += evaluate_king_safety(board_obj)
        # Thêm bonus khi chiếu
        if is_in_check(board_obj, "b"):
            score += 0.5
        if is_in_check(board_obj, "w"):
            score -= 0.5
        return score

    # Hard: sử dụng score_board đầy đủ
    return score_board(board_obj)


def negamax_alpha_beta(board_obj, depth, alpha, beta, turn_multiplier, level, start_time=None, time_limit=None):
    legal_moves = get_all_legal_moves(board_obj)
    if depth == 0 or not legal_moves:
        if level == "easy":
            return turn_multiplier * evaluate_board(board_obj, level), None
        # Quiescence search: luôn xét capture khi depth=0 để tránh horizon effect
        return quiescence_search(board_obj, alpha, beta, turn_multiplier, level, max_depth=None), None

    best_score = -CHECKMATE
    best_move = None
    original_alpha = alpha
    key = hash_board(board_obj)

    if level == "hard" and key in transposition_table:
        entry = transposition_table[key]
        if entry["depth"] >= depth:
            if entry["flag"] == "exact":
                return entry["score"], entry.get("best_move")
            if entry["flag"] == "lowerbound":
                alpha = max(alpha, entry["score"])
            elif entry["flag"] == "upperbound":
                beta = min(beta, entry["score"])
            if alpha >= beta:
                return entry["score"], entry.get("best_move")

    for move in order_moves(board_obj, legal_moves):
        if time_limit and time.time() - start_time >= time_limit:
            return best_score, best_move  # Trả về kết quả hiện tại nếu hết thời gian

        board_obj.make_move(*move)
        score, _ = negamax_alpha_beta(board_obj, depth - 1, -beta, -alpha, -turn_multiplier, level, start_time, time_limit)
        score = -score
        board_obj.undo_move()

        if score > best_score:
            best_score = score
            best_move = move

        alpha = max(alpha, best_score)
        if alpha >= beta:
            break

    if level == "hard":
        if best_score <= original_alpha:
            flag = "upperbound"
        elif best_score >= beta:
            flag = "lowerbound"
        else:
            flag = "exact"
        transposition_table[key] = {
            "score": best_score,
            "depth": depth,
            "flag": flag,
            "best_move": best_move,
        }

    return best_score, best_move


def choose_best_move(scored_moves, threshold=0.01):
    scored_moves.sort(key=lambda x: x[0], reverse=True)
    best_score = scored_moves[0][0]
    top_moves = [move for score, move in scored_moves if best_score - score <= threshold]
    return random.choice(top_moves)


def choose_human_like_move(scored_moves):
    """
    Không luôn chọn nước tốt nhất tuyệt đối.
    Chọn ngẫu nhiên trong nhóm nước tốt nhất để AI đỡ "máy".
    """
    scored_moves.sort(key=lambda x: x[0], reverse=True)
    best_score = scored_moves[0][0]

    candidates = []
    for score, move in scored_moves:
        if best_score - score <= 0.35:
            candidates.append((score, move))

    # Ưu tiên nước tốt hơn nhưng vẫn có ngẫu nhiên
    weights = []
    for score, _ in candidates:
        weights.append(max(0.1, 1.0 - (best_score - score)))

    return random.choices([m for _, m in candidates], weights=weights, k=1)[0]


def find_best_move(board_obj, level="normal", depth=None, time_limit=None):
    legal_moves = get_all_legal_moves(board_obj)
    if not legal_moves:
        return None

    level = level.lower() if isinstance(level, str) else "normal"
    settings = LEVEL_SETTINGS.get(level, LEVEL_SETTINGS["normal"])

    if time_limit is None:
        time_limit = settings["time_limit"]

    start_time = time.time()

    # Iterative deepening với time limit, ưu tiên best move trước
    best_move = None
    for current_depth in range(1, settings["max_depth"] + 1):
        if time.time() - start_time >= time_limit:
            break

        if level == "easy" and random.random() < settings["random_rate"]:
            return random.choice(legal_moves)

        # Uu tiên best_move từ depth trước, kiểm tra trước khi remove
        if best_move and best_move in legal_moves:
            legal_moves.remove(best_move)
            legal_moves.insert(0, best_move)

        random.shuffle(legal_moves)
        turn_multiplier = 1 if board_obj.white_to_move else -1
        alpha = -CHECKMATE
        beta = CHECKMATE

        scored_moves = []

        for move in order_moves(board_obj, legal_moves):
            if time.time() - start_time >= time_limit:
                break

            board_obj.make_move(*move)
            score, _ = negamax_alpha_beta(board_obj, current_depth - 1, -beta, -alpha, -turn_multiplier, level, start_time, time_limit)
            score = -score
            board_obj.undo_move()

            if level != "hard":
                score += random.uniform(-0.03, 0.03)  # Tắt random cho hard
            scored_moves.append((score, move))
            alpha = max(alpha, score)

        if scored_moves:
            if level == "easy":
                if random.random() < settings["random_rate"]:
                    best_move = random.choice(legal_moves)
                else:
                    best_move = choose_human_like_move(scored_moves)
            elif level == "normal":
                if random.random() < settings["random_rate"]:
                    best_move = choose_best_move(scored_moves, threshold=0.20)
                else:
                    best_move = choose_human_like_move(scored_moves)
            else:  # hard
                best_move = choose_best_move(scored_moves, threshold=0.0)  # Luôn chọn best move, tắt random, tắt random

    return best_move
