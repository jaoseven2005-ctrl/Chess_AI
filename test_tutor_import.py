#!/usr/bin/env python3
# Quick test to verify tutor module imports work

import sys
sys.path.insert(0, r'd:\Vibe code\Chess_AI')

try:
    from engine.tutor import (
        initialize_tutor_state,
        update_tutor_state,
        check_tutor_result,
        draw_evaluation_bar,
        get_best_move_and_score,
    )
    print("✓ All tutor imports successful!")
    
    # Test initialization
    state = initialize_tutor_state()
    print(f"✓ Tutor state initialized: {list(state.keys())}")
    
    print("\nTutor module is ready to use!")
except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
