"""
UI Manager module for handling all game visualization and visual effects.
Separates UI rendering logic from the main game loop.
"""

import cv2
import time
import math
from game.game_config import *

class UIManager:
    """
    Manages all UI rendering including game stats, visual effects, and instructions.
    Provides a clean interface for drawing game elements on video frames.
    """

    def __init__(self):
        """Initialize the UI manager with default settings."""
        self.punch_effect_timer = 0
        self.punch_effect_duration = PUNCH_EFFECT_DURATION

    def draw_game_ui(self, image, game_state):
        """
        Draw complete game UI on the provided image.

        Args:
            image: OpenCV image/frame to draw on
            game_state: GameState instance with current game data

        Returns:
            None (modifies image in place)
        """
        height, width = image.shape[:2]

        # Draw all UI components
        self._draw_ui_background(image)
        self._draw_game_stats(image, game_state)
        self._draw_punch_effects(image, width, height)
        self._draw_instructions(image, game_state, height)

    def _draw_ui_background(self, image):
        """Draw the UI panel background."""
        cv2.rectangle(image, UI_PANEL_POSITION,
                     (UI_PANEL_POSITION[0] + UI_PANEL_SIZE[0], UI_PANEL_POSITION[1] + UI_PANEL_SIZE[1]),
                     UI_BACKGROUND_COLOR, -1)
        cv2.rectangle(image, UI_PANEL_POSITION,
                     (UI_PANEL_POSITION[0] + UI_PANEL_SIZE[0], UI_PANEL_POSITION[1] + UI_PANEL_SIZE[1]),
                     UI_BORDER_COLOR, 2)

    def _draw_game_stats(self, image, game_state):
        """Draw score, punch count, and combo information."""
        # Score display
        cv2.putText(image, f"Score: {game_state.get_score()}", (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, SCORE_COLOR, 2)

        # Punch count
        cv2.putText(image, f"Punches: {game_state.get_punch_count()}", (20, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, NORMAL_TEXT_COLOR, 2)

        # Combo display
        combo_color = COMBO_COLOR if game_state.is_combo_active() else NORMAL_TEXT_COLOR
        cv2.putText(image, f"Combo: {game_state.get_combo_multiplier()}x", (20, 100),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, combo_color, 2)


    def _draw_punch_effects(self, image, width, height):
        """Draw punch visual effects (flash and text)."""
        current_time = time.time()
        if current_time - self.punch_effect_timer < self.punch_effect_duration:
            # Flash effect
            alpha = 1.0 - (current_time - self.punch_effect_timer) / self.punch_effect_duration
            overlay = image.copy()
            cv2.rectangle(overlay, (0, 0), (width, height), (0, 255, 0), -1)
            cv2.addWeighted(overlay, alpha * PUNCH_EFFECT_ALPHA, image, 1.0, 0, image)

            # "PUNCH!" text
            text_size = cv2.getTextSize("PUNCH!", cv2.FONT_HERSHEY_SIMPLEX, 2, 3)[0]
            text_x = (width - text_size[0]) // 2
            text_y = (height + text_size[1]) // 2
            cv2.putText(image, "PUNCH!", (text_x, text_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 2, PUNCH_TEXT_COLOR, 3)

    def _draw_instructions(self, image, game_state, height):
        """Draw instructional text for new players."""
        if game_state.get_punch_count() == 0:
            instructions = [
                "1. Open smartphone web interface",
                "2. Start punching while holding phone",
                "3. Face the camera for best results"
            ]
            for i, instruction in enumerate(instructions):
                cv2.putText(image, instruction, (20, height - 80 + i * 25),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, INSTRUCTION_COLOR, 1)


    def trigger_punch_effect(self):
        """Trigger the visual punch effect."""
        self.punch_effect_timer = time.time()

    def is_punch_effect_active(self):
        """Check if punch effect is currently being displayed."""
        current_time = time.time()
        return current_time - self.punch_effect_timer < self.punch_effect_duration

    def reset_effects(self):
        """Reset all visual effects."""
        self.punch_effect_timer = 0