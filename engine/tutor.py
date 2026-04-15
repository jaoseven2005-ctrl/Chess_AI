# engine/tutor.py
# AI Tutor - Professional evaluation, hints, move classification, and blunder detection

import time
import copy
import threading
import math
import pygame
from engine.ai import find_best_move, score_board

# Time budgets for analysis
ANALYSIS_TIME_LIMIT = 0.45
HINT_TIME_LIMIT = 0.80
CACHE_MAX_ENTRIES = 128


def clamp_score(score):
    try:
        return max(-10.0, min(10.0, float(score)))
    except Exception:
        return 0.0


def format_score_text(score):
    return f"{'+' if score >= 0 else ''}{score:.1f}"


def sigmoid(x, steepness=0.8):
    try:
        return 1.0 / (1.0 + math.exp(-steepness * x))
    except Exception:
        return 0.5


def compute_board_score(board_obj):
    return clamp_score(score_board(board_obj))


def simulate_move_score(board_obj, move):
    if move is None:
        return compute_board_score(board_obj)

    snapshot = copy.deepcopy(board_obj)
    snapshot.move_piece(move[0], move[1])
    return compute_board_score(snapshot)


def classify_player_move(tutor_state, actual_move, moved_color, current_score):
    if actual_move is None or tutor_state["best_move"] is None:
        return None

    best_move = tutor_state["best_move"]
    best_move_score = tutor_state.get("best_move_score")

    if actual_move == best_move:
        return "Best Move"

    if best_move_score is not None and current_score >= best_move_score + 0.7:
        return "Brilliant"

    return None


def detect_blunder(prev_score, current_score, moved_color):
    if prev_score is None or current_score is None:
        return None, 0.0

    human_before = prev_score if moved_color == "w" else -prev_score
    human_after = current_score if moved_color == "w" else -current_score
    score_drop = (human_before - human_after) * 3

    if score_drop < 0.5:
        return "Best", score_drop
    if score_drop < 1.5:
        return "Inaccuracy", score_drop
    if score_drop < 3.0:
        return "Mistake", score_drop
    return "Blunder", score_drop


def initialize_tutor_state():
    return {
        "ai_score": 0.0,
        "display_score": 0.0,
        "prev_score": None,
        "best_move": None,
        "best_move_score": None,
        "hint_setup": False,
        "hint_toggle": False,
        "show_hint": False,
        "is_computing": False,
        "hint_ready": False,
        "is_hint_requested": False,
        "last_board_hash": None,
        "cache": {},
        "result": {},
        "task_id_holder": {"current": 0},
        "lock": threading.Lock(),
        "blunder_type": None,
        "blunder_detail": "",
        "blunder_cooldown_end": 0.0,
        "is_blunder": False,
        "move_classification": None,
        "last_move_squares": None,
    }


def update_display_score(tutor_state):
    target = tutor_state.get("ai_score", 0.0)
    display = tutor_state.get("display_score", target)
    display = display * 0.85 + target * 0.15
    if abs(display - target) < 0.02:
        display = target
    tutor_state["display_score"] = display
    return display


def store_cache(tutor_state, board_hash, data):
    if not board_hash:
        return
    tutor_state["cache"][board_hash] = data
    if len(tutor_state["cache"]) > CACHE_MAX_ENTRIES:
        oldest = next(iter(tutor_state["cache"]))
        tutor_state["cache"].pop(oldest, None)


def tutor_ai_worker(board_snapshot, is_white_turn, result_dict, lock, task_id, task_id_holder, hint_requested=False):
    try:
        board_snapshot.white_to_move = is_white_turn
        level = "hard" if hint_requested else "normal"
        time_limit = HINT_TIME_LIMIT if hint_requested else ANALYSIS_TIME_LIMIT
        best_move = find_best_move(board_snapshot, level=level, time_limit=time_limit)
        score = compute_board_score(board_snapshot)
        best_score = simulate_move_score(board_snapshot, best_move) if best_move else score

        board_hash = (tuple(tuple(row) for row in board_snapshot.board), board_snapshot.white_to_move)

        with lock:
            if task_id != task_id_holder.get("current"):
                return
            result_dict.update({
                "move": best_move,
                "score": score,
                "best_move_score": best_score,
                "hint_requested": hint_requested,
                "board_hash": board_hash,
            })
    except Exception as e:
        print(f"ERROR in tutor_ai_worker: {e}")


def update_tutor_state(tutor_state, current_board, hint_requested=False, force=False):
    board_hash = (tuple(tuple(row) for row in current_board.board), current_board.white_to_move)
    if not force and tutor_state.get("last_board_hash") == board_hash and not hint_requested:
        return

    if tutor_state["is_computing"]:
        return

    cached = tutor_state["cache"].get(board_hash)
    if cached and (not hint_requested or cached.get("search_level") == "hard"):
        tutor_state["best_move"] = cached.get("move")
        tutor_state["best_move_score"] = cached.get("best_move_score")
        tutor_state["ai_score"] = cached.get("score", tutor_state.get("ai_score", 0.0))
        tutor_state["last_board_hash"] = board_hash
        tutor_state["hint_ready"] = hint_requested
        tutor_state["show_hint"] = hint_requested
        tutor_state["is_hint_requested"] = hint_requested
        return

    with tutor_state["lock"]:
        tutor_state["is_computing"] = True
        tutor_state["hint_ready"] = False
        tutor_state["is_hint_requested"] = hint_requested
        tutor_state["task_id_holder"]["current"] += 1
        task_id = tutor_state["task_id_holder"]["current"]

    board_snapshot = copy.deepcopy(current_board)
    thread = threading.Thread(
        target=tutor_ai_worker,
        args=(
            board_snapshot,
            current_board.white_to_move,
            tutor_state["result"],
            tutor_state["lock"],
            task_id,
            tutor_state["task_id_holder"],
            hint_requested,
        ),
        daemon=True,
    )
    thread.start()


def check_tutor_result(tutor_state):
    with tutor_state["lock"]:
        result = tutor_state["result"].copy()

    if result.get("board_hash") is None:
        return False, None, None

    with tutor_state["lock"]:
        tutor_state["is_computing"] = False
        tutor_state["hint_ready"] = tutor_state["is_hint_requested"]
        tutor_state["best_move"] = result.get("move")
        tutor_state["best_move_score"] = result.get("best_move_score")
        tutor_state["ai_score"] = result.get("score", 0.0)
        tutor_state["last_board_hash"] = result.get("board_hash")
        tutor_state["result"] = {}

        cache_entry = {
            "move": result.get("move"),
            "score": result.get("score", 0.0),
            "best_move_score": result.get("best_move_score"),
            "search_level": "hard" if result.get("hint_requested") else "normal",
        }
        store_cache(tutor_state, result.get("board_hash"), cache_entry)

    return True, result.get("move"), result.get("score", 0.0)


def apply_move_analysis(tutor_state, board_obj, actual_move, moved_color):
    current_score = compute_board_score(board_obj)
    prev_score = tutor_state.get("prev_score")

    blunder_type, score_drop = detect_blunder(prev_score, current_score, moved_color)
    classification = classify_player_move(tutor_state, actual_move, moved_color, current_score)

    tutor_state["prev_score"] = current_score
    tutor_state["last_move_squares"] = actual_move
    tutor_state["move_classification"] = classification
    tutor_state["show_hint"] = False
    tutor_state["hint_ready"] = False
    tutor_state["hint_toggle"] = False

    if blunder_type in ("Mistake", "Blunder"):
        now = time.time()
        if now >= tutor_state.get("blunder_cooldown_end", 0.0):
            tutor_state["is_blunder"] = True
            tutor_state["blunder_type"] = blunder_type
            tutor_state["blunder_detail"] = (
                f"{format_score_text(prev_score)} → {format_score_text(current_score)}"
            )
            tutor_state["blunder_cooldown_end"] = now + 2.8
        else:
            tutor_state["is_blunder"] = tutor_state["is_blunder"] and now < tutor_state["blunder_cooldown_end"]
    else:
        tutor_state["is_blunder"] = False
        tutor_state["blunder_type"] = None
        tutor_state["blunder_detail"] = ""

    return classification


def draw_evaluation_bar(screen, ai_score, bar_x, bar_y, bar_width, bar_height,
                        white_color=(255,255,255), black_color=(40,40,40),
                        border_color=(120,120,120), text_color=(48,48,48)):
    clamped_score = clamp_score(ai_score)
    adjusted_score = clamped_score * 2.8
    ratio = sigmoid(adjusted_score)

    white_height = int(bar_height * ratio)
    black_height = bar_height - white_height

    black_rect = pygame.Rect(bar_x, bar_y, bar_width, black_height)
    pygame.draw.rect(screen, black_color, black_rect, border_radius=10)

    white_rect = pygame.Rect(bar_x, bar_y + black_height, bar_width, white_height)
    pygame.draw.rect(screen, white_color, white_rect, border_radius=10)

    full_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
    pygame.draw.rect(screen, border_color, full_rect, 2, border_radius=10)

    text_surface = pygame.font.SysFont('segoeui', 16, bold=True).render(
        format_score_text(clamped_score), True, text_color
    )
    text_rect = text_surface.get_rect(center=(bar_x + bar_width//2, bar_y - 18))
    screen.blit(text_surface, text_rect)

    return white_rect, black_rect


def draw_hint_highlight(screen, start_pos, end_pos, sq_size, board_x, board_y):
    if not start_pos or not end_pos:
        return

    neon_start = (78, 255, 180, 130)
    neon_end = (250, 205, 80, 140)
    arrow_color = (144, 255, 202)

    start_center = (
        board_x + start_pos[1] * sq_size + sq_size // 2,
        board_y + start_pos[0] * sq_size + sq_size // 2,
    )
    end_center = (
        board_x + end_pos[1] * sq_size + sq_size // 2,
        board_y + end_pos[0] * sq_size + sq_size // 2,
    )

    square_surface = pygame.Surface((sq_size, sq_size), pygame.SRCALPHA)
    pygame.draw.rect(square_surface, neon_start, square_surface.get_rect(), border_radius=12)
    pygame.draw.rect(square_surface, (*neon_start[:3], 200), square_surface.get_rect(), 3, border_radius=12)
    screen.blit(square_surface, (board_x + start_pos[1] * sq_size, board_y + start_pos[0] * sq_size))

    square_surface = pygame.Surface((sq_size, sq_size), pygame.SRCALPHA)
    pygame.draw.rect(square_surface, neon_end, square_surface.get_rect(), border_radius=12)
    pygame.draw.rect(square_surface, (244, 191, 94, 220), square_surface.get_rect(), 3, border_radius=12)
    screen.blit(square_surface, (board_x + end_pos[1] * sq_size, board_y + end_pos[0] * sq_size))

    arrow_surface = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
    for width, alpha in ((12, 40), (8, 90), (4, 200)):
        pygame.draw.line(arrow_surface, (*arrow_color[:3], alpha), start_center, end_center, width)

    dx = end_center[0] - start_center[0]
    dy = end_center[1] - start_center[1]
    angle = math.atan2(dy, dx)
    arrow_head = [
        (end_center[0] - 12 * math.cos(angle - 0.3), end_center[1] - 12 * math.sin(angle - 0.3)),
        (end_center[0] - 12 * math.cos(angle + 0.3), end_center[1] - 12 * math.sin(angle + 0.3)),
        end_center,
    ]
    pygame.draw.polygon(arrow_surface, arrow_color, arrow_head)
    screen.blit(arrow_surface, (0, 0))


def draw_blunder_popup(screen, tutor_state, screen_width, screen_height):
    if not tutor_state.get("is_blunder"):
        return
    if time.time() >= tutor_state.get("blunder_cooldown_end", 0.0):
        tutor_state["is_blunder"] = False
        return

    popup_w = 420
    popup_h = 92
    rect = pygame.Rect(
        (screen_width - popup_w) // 2,
        screen_height - popup_h - 24,
        popup_w,
        popup_h,
    )

    bg = pygame.Surface((popup_w, popup_h), pygame.SRCALPHA)
    pygame.draw.rect(bg, (255, 244, 240, 230), bg.get_rect(), border_radius=18)
    pygame.draw.rect(bg, (202, 96, 78), bg.get_rect(), 2, border_radius=18)
    screen.blit(bg, rect.topleft)

    title = "Sai lầm nghiêm trọng!" if tutor_state.get("blunder_type") == "Blunder" else "Sai lầm!"
    title_font = pygame.font.SysFont('segoeui', 20, bold=True)
    details_font = pygame.font.SysFont('segoeui', 16)

    title_text = title_font.render(title, True, (133, 27, 27))
    detail_text = details_font.render(tutor_state.get("blunder_detail", ""), True, (90, 30, 30))

    screen.blit(title_text, (rect.x + 20, rect.y + 18))
    screen.blit(detail_text, (rect.x + 20, rect.y + 46))


def finalize_move_evaluation(tutor_state, board_obj, actual_move, moved_color):
    classification = apply_move_analysis(tutor_state, board_obj, actual_move, moved_color)
    return classification


def clear_blunder_state(tutor_state):
    tutor_state["is_blunder"] = False
    tutor_state["blunder_type"] = None
    tutor_state["blunder_detail"] = ""
    tutor_state["blunder_cooldown_end"] = 0.0
