# INTEGRATION GUIDE FOR AI TUTOR INTO game.py
# This file shows EXACTLY where to add code in run_pvp and run_pve

# ============================================================================
# STEP 1: Add import at top of game.py (after line 8):
# ============================================================================
# from engine.tutor import (
#     initialize_tutor_state,
#     update_tutor_state,
#     check_tutor_result,
#     check_for_blunder,
#     clear_blunder_state,
#     draw_evaluation_bar,
#     draw_hint_button,
#     draw_hint_highlight,
# )

# ============================================================================
# STEP 2: In run_pvp(), after line 1162 "settings_open = False", add:
# ============================================================================
#     
#     # AI Tutor initialization
#     tutor_state = initialize_tutor_state()
#     hint_button_rect = pygame.Rect(960, 700, 140, 45)  # Below captured pieces area

# ============================================================================
# STEP 3: In run_pvp(), replace the draw section (approx lines 1234-1236):
# Original:
#         draw_side_panels(screen, board_obj)
#         draw_board(screen, board_obj, valid_moves, check_king_pos, animation, hover_square)
#         draw_bottom_bar(screen, message)
#
# Replace with:
# ============================================================================
#         draw_side_panels(screen, board_obj)
#         draw_board(screen, board_obj, valid_moves, check_king_pos, animation, hover_square)
#         
#         # ==== AI Tutor: Draw Evaluation Bar ====
#         eval_bar_x = BOARD_X - 35
#         eval_bar_y = BOARD_Y
#         eval_bar_w = 22
#         eval_bar_h = BOARD_SIZE
#         draw_evaluation_bar(screen, tutor_state["ai_score"], eval_bar_x, eval_bar_y, 
#                            eval_bar_w, eval_bar_h)
#         
#         # ==== AI Tutor: Draw Hint Button ====
#         hint_btn_hover = hint_button_rect.collidepoint(pygame.mouse.get_pos())
#         draw_hint_button(screen, hint_button_rect, hint_btn_hover)
#         draw_text(screen, "Gợi ý (H)", 14, TEXT_DARK, hint_button_rect.centerx, 
#                  hint_button_rect.centery, center=True)
#         
#         # ==== AI Tutor: Draw Hint Highlight if active ====
#         if tutor_state["hint_toggle"] and tutor_state["best_move"] is not None:
#             start_pos, end_pos = tutor_state["best_move"]
#             draw_hint_highlight(screen, start_pos, end_pos, SQ_SIZE, BOARD_X, BOARD_Y)
#         
#         # ==== AI Tutor: Draw "AI analyzing..." text if computing ====
#         if tutor_state["is_computing"]:
#             draw_text(screen, "AI đang phân tích...", 12, TEXT_LIGHT, BOARD_X + 150, BOARD_Y - 20)
#         
#         # ==== AI Tutor: Show blunder warning if detected ====
#         if tutor_state["blunder_detected"]:
#             draw_text(screen, tutor_state["blunder_message"], 14, CAPTURE_HIGHLIGHT,
#                      WIDTH // 2, HEIGHT - 100, center=True, bold=True)
#         
#         draw_bottom_bar(screen, message)

# ============================================================================
# STEP 4: In run_pvp(), add keyboard handling in event loop (after line 1255):
# Original:
#         for event in pygame.event.get():
#             if event.type == pygame.QUIT:
#                 return "quit"
#
#             if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
#
# Add this BEFORE the MOUSEBUTTONDOWN check:
# ============================================================================
#             # ==== AI Tutor: Handle H key for hint toggle ====
#             if event.type == pygame.KEYDOWN:
#                 if event.key == pygame.K_h:
#                     tutor_state["hint_toggle"] = not tutor_state["hint_toggle"]
#                     if tutor_state["hint_toggle"] and tutor_state["best_move"] is None:
#                         # Request hint calculation if not done yet
#                         update_tutor_state(tutor_state, board_obj, board_obj, hint_requested=True)

# ============================================================================
# STEP 5: In run_pvp(), in MOUSEBUTTONDOWN handler (after line 1261 "pos = mouse"):
# Add this RIGHT AFTER getting pos, BEFORE settings_button check:
# ============================================================================
#                 # ==== AI Tutor: Handle Hint Button Click ====
#                 if hint_button_rect.collidepoint(pos):
#                     tutor_state["hint_toggle"] = not tutor_state["hint_toggle"]
#                     if tutor_state["hint_toggle"] and tutor_state["best_move"] is None:
#                         update_tutor_state(tutor_state, board_obj, board_obj, hint_requested=True)
#                     continue

# ============================================================================
# STEP 6: In run_pvp(), after animation updates (after player move):
# Around line 1345 where "message = f"{piece_name(animation['piece'])} đang di chuyển...""
# Add:
# ============================================================================
#                     # ==== AI Tutor: On new move, update evaluation ====
#                     update_tutor_state(tutor_state, board_obj, board_obj, hint_requested=False)
#                     
#                     # ==== AI Tutor: Check for blunder ====
#                     if tutor_state["prev_score"] is not None:
#                         check_for_blunder(tutor_state, tutor_state["prev_score"], 0.0)
#                     
#                     # Store current score for next blunder check
#                     tutor_state["prev_score"] = 0.0

# ============================================================================
# STEP 7: In run_pvp(), update tutor state periodically in main loop:
# Right after pygame.display.flip() and before pygame.clock.tick()
# ============================================================================
#         # ==== AI Tutor: Check if computation finished (non-blocking) ====
#         is_done, best_move, ai_score = check_tutor_result(tutor_state)
#         if is_done:
#             # Clear blunder warning on new calculation complete
#             if tutor_state["is_hint_requested"]:
#                 clear_blunder_state(tutor_state)

# ============================================================================
# SIMILAR STEPS for run_pve() - see TUTOR_INTEGRATION_PVE.py
# ============================================================================
