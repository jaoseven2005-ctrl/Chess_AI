# engine/tutor.py
# AI Tutor - Evaluation Bar, Hint System, Threading Support

import random
import time
import copy
import threading
import math
import pygame

# ============================================================================
# PART 1: AI Mock Function (Replace this with real Minimax later)
# ============================================================================

def get_best_move_and_score(board_obj, current_turn):
    """
    Simulate AI evaluation and best move suggestion.
    
    Args:
        board_obj: Board object
        current_turn: "w" for white, "b" for black
    
    Returns:
        tuple: (best_move, ai_score)
        - best_move: ((from_row, from_col), (to_row, to_col)) or None
        - ai_score: float between -10.0 and +10.0
    
    TODO: Replace with real Minimax/Alpha-Beta implementation
    """
    from engine.moves import get_valid_moves
    
    # Collect all legal moves
    all_moves = []
    for r in range(8):
        for c in range(8):
            piece = board_obj.board[r][c]
            # Only consider pieces of current turn color
            if piece != "--" and piece[0] == current_turn:
                moves = get_valid_moves(board_obj, r, c)
                for move in moves:
                    all_moves.append(((r, c), move))
    
    if not all_moves:
        return None, 0.0
    
    # Pick a random move (placeholder)
    best_move = random.choice(all_moves)
    
    # Simulate score: random value between -10 and +10
    # Bias slightly towards positive if white's turn
    if current_turn == "w":
        ai_score = random.uniform(-3.0, 8.0)
    else:
        ai_score = random.uniform(-8.0, 3.0)
    
    return best_move, ai_score


# ============================================================================
# PART 2: Sigmoid-like function to smooth score-to-pixel conversion
# ============================================================================

def sigmoid(x, steepness=0.5):
    """
    Smooth sigmoid function to convert score (-10..+10) to ratio (0..1).
    
    Args:
        x: Score value (-10 to +10)
        steepness: Controls curve steepness (default 0.5)
    
    Returns:
        float: Ratio from 0 to 1
    """
    try:
        return 1.0 / (1.0 + math.exp(-steepness * x))
    except:
        return 0.5


# ============================================================================
# PART 3: Evaluation Bar Drawing
# ============================================================================

def draw_evaluation_bar(screen, ai_score, bar_x, bar_y, bar_width, bar_height,
                        white_color=(234, 240, 225), black_color=(100, 120, 100),
                        border_color=(45, 60, 45)):
    """
    Draw evaluation bar showing position assessment (white ratio vs black ratio).
    
    Args:
        screen: pygame surface
        ai_score: float (-10 to +10), positive = white advantage
        bar_x, bar_y: top-left position
        bar_width, bar_height: dimensions
        white_color, black_color: RGB tuples
        border_color: RGB tuple for border
    """
    # Clamp score to reasonable range
    clamped_score = max(-10.0, min(10.0, ai_score))
    
    # Convert score to white ratio using smooth sigmoid
    white_ratio = sigmoid(clamped_score, steepness=0.4)
    
    # Calculate split height
    white_height = int(bar_height * white_ratio)
    black_height = bar_height - white_height
    
    # Draw white section (top)
    white_rect = pygame.Rect(bar_x, bar_y, bar_width, white_height)
    pygame.draw.rect(screen, white_color, white_rect)
    
    # Draw black section (bottom)
    black_rect = pygame.Rect(bar_x, bar_y + white_height, bar_width, black_height)
    pygame.draw.rect(screen, black_color, black_rect)
    
    # Draw border
    full_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
    pygame.draw.rect(screen, border_color, full_rect, 2, border_radius=4)
    
    return white_rect, black_rect


# ============================================================================
# PART 4: Hint System Drawing
# ============================================================================

def draw_hint_button(screen, btn_rect, hover=False):
    """
    Draw minimalist hint button.
    
    Args:
        screen: pygame surface
        btn_rect: pygame.Rect for button
        hover: boolean, True if mouse hovering
    
    Returns:
        button rectangle
    """
    # Button styling
    bg_color = (240, 245, 238) if hover else (250, 252, 248)  # Cream/white
    border_color = (45, 60, 45)  # Dark text (**NOT** hover color)
    text_color = (45, 60, 45)
    
    # Draw background
    pygame.draw.rect(screen, bg_color, btn_rect, border_radius=12)
    
    # Draw border
    border_width = 2 if hover else 1
    pygame.draw.rect(screen, border_color, btn_rect, border_width, border_radius=12)
    
    # Draw text (using font from game module)
    # We'll return and let caller handle text rendering via get_font
    
    return btn_rect


def draw_hint_highlight(screen, start_pos, end_pos, sq_size, board_x, board_y,
                        highlight_color=(255, 255, 153, 100)):
    """
    Draw semi-transparent highlight on source and destination squares for hint.
    
    Args:
        screen: pygame surface
        start_pos: (row, col) source square
        end_pos: (row, col) destination square
        sq_size: size of one square in pixels
        board_x, board_y: board top-left position
        highlight_color: RGBA tuple
    """
    # Create transparent surface
    highlight_surface = pygame.Surface((sq_size, sq_size), pygame.SRCALPHA)
    pygame.draw.rect(highlight_surface, highlight_color, highlight_surface.get_rect(), border_radius=8)
    
    # Draw on source square
    sr, sc = start_pos
    screen.blit(highlight_surface, (board_x + sc * sq_size, board_y + sr * sq_size))
    
    # Draw on destination square
    er, ec = end_pos
    screen.blit(highlight_surface, (board_x + ec * sq_size, board_y + er * sq_size))


# ============================================================================
# PART 5: Threading Worker & State Management
# ============================================================================

def tutor_ai_worker(board_snapshot, is_white_turn, result_dict, lock, task_id, task_id_holder):
    """
    Worker thread for computing best move and evaluation score.
    
    Args:
        board_snapshot: deep copy of board
        is_white_turn: boolean
        result_dict: shared dict to store {"move": ..., "score": ...}
        lock: threading lock
        task_id: current task ID for cancellation checking
        task_id_holder: dict with {"current": ...} current task
    """
    try:
        current_turn = "w" if is_white_turn else "b"
        best_move, ai_score = get_best_move_and_score(board_snapshot, current_turn)
        
        # Check if task was cancelled while computing
        with lock:
            if task_id != task_id_holder.get("current"):
                return
            result_dict["move"] = best_move
            result_dict["score"] = ai_score
    except Exception as e:
        print(f"ERROR in tutor_ai_worker: {e}")


def update_tutor_state(tutor_state, current_board, board_obj, hint_requested=False):
    """
    Safely update tutor state via threading.
    Called when:
    - Game starts / board changes
    - User requests hint (H key)
    - Player makes a move (to check for blundle)
    
    Args:
        tutor_state: dict with tutor state
        current_board: board to analyze
        board_obj: for getting white_to_move
        hint_requested: boolean, force hint calculation
    """
    # Prevent overlapping threads
    with tutor_state["lock"]:
        if tutor_state["is_computing"] and not hint_requested:
            return  # Already computing
        
        tutor_state["is_computing"] = True
        tutor_state["hint_ready"] = False
        tutor_state["is_hint_requested"] = hint_requested
        
        # Increment task ID to cancel previous task
        tutor_state["task_id_holder"]["current"] += 1
        current_task_id = tutor_state["task_id_holder"]["current"]
    
    # Spawn thread (non-blocking)
    board_snapshot = copy.deepcopy(current_board)
    is_white = current_board.white_to_move
    
    thread = threading.Thread(
        target=tutor_ai_worker,
        args=(
            board_snapshot,
            is_white,
            tutor_state["result"],
            tutor_state["lock"],
            current_task_id,
            tutor_state["task_id_holder"]
        ),
        daemon=True
    )
    thread.start()


def check_tutor_result(tutor_state):
    """
    Check if tutor calculation finished. Non-blocking.
    
    Returns:
        tuple: (is_done, best_move, ai_score)
    """
    with tutor_state["lock"]:
        result = tutor_state["result"].copy()
    
    if result.get("move") is not None:
        # Calculation done
        with tutor_state["lock"]:
            tutor_state["is_computing"] = False
            tutor_state["hint_ready"] = tutor_state["is_hint_requested"]
            tutor_state["best_move"] = result["move"]
            tutor_state["ai_score"] = result.get("score", 0.0)
        return True, result["move"], result.get("score", 0.0)
    
    return False, None, None


# ============================================================================
# PART 6: Blunder Detection
# ============================================================================

def check_for_blunder(tutor_state, prev_score, current_score, blunder_threshold=-5.0):
    """
    Detect if player made a blunder (score dropped significantly).
    
    Args:
        tutor_state: dict
        prev_score: float, score before last move
        current_score: float, score after last move
        blunder_threshold: float, score drop threshold (e.g., -5.0 means drop of 5 is blunder)
    
    Returns:
        boolean: True if blunder detected
    """
    if prev_score is None or current_score is None:
        return False
    
    score_change = current_score - prev_score
    is_blunder = score_change <= blunder_threshold
    
    if is_blunder:
        tutor_state["blunder_detected"] = True
        tutor_state["blunder_message"] = f"Bạn vừa đi một nước tồi tệ! (-{abs(score_change):.1f})"
    
    return is_blunder


def initialize_tutor_state():
    """
    Create and return empty tutor state dict.
    Call this once at game start.
    """
    return {
        "is_computing": False,
        "hint_ready": False,
        "is_hint_requested": False,
        "best_move": None,
        "ai_score": 0.0,
        "prev_score": None,  # For blunder detection
        "blunder_detected": False,
        "blunder_message": "",
        "hint_toggle": False,  # Shows highlight
        "lock": threading.Lock(),
        "result": {},  # {"move": ..., "score": ...}
        "task_id_holder": {"current": 0},
    }


# ============================================================================
# PART 7: Helper to clear blunder state
# ============================================================================

def clear_blunder_state(tutor_state):
    """Reset blunder detection for next move."""
    tutor_state["blunder_detected"] = False
    tutor_state["blunder_message"] = ""
