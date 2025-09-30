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

        # Check game mode and draw appropriate screen
        if game_state.is_menu():
            self._draw_menu_screen(image, game_state, width, height)
        elif game_state.is_countdown():
            self._draw_countdown_screen(image, game_state, width, height)
        elif game_state.is_game_over():
            self._draw_game_over_screen(image, game_state, width, height)
        else:
            # Draw all UI components for playing mode
            self._draw_ui_background(image)
            self._draw_game_stats(image, game_state)
            self._draw_timer(image, game_state, width)
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

    def _draw_menu_screen(self, image, game_state, width, height):
        """Draw the main menu screen."""
        # Dark overlay
        overlay = image.copy()
        cv2.rectangle(overlay, (0, 0), (width, height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, image, 0.3, 0, image)

        # Title
        title = "PUNCH DETECTION GAME"
        title_size = cv2.getTextSize(title, cv2.FONT_HERSHEY_BOLD, 1.5, 3)[0]
        title_x = (width - title_size[0]) // 2
        title_y = height // 3
        cv2.putText(image, title, (title_x, title_y),
                   cv2.FONT_HERSHEY_BOLD, 1.5, (255, 255, 255), 3)

        # High score display
        high_score_text = f"High Score: {game_state.get_high_score()}"
        hs_size = cv2.getTextSize(high_score_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
        hs_x = (width - hs_size[0]) // 2
        hs_y = height // 3 + 50
        cv2.putText(image, high_score_text, (hs_x, hs_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        # Instructions
        instructions = [
            "Press 'S' to START",
            "",
            "Connect your smartphone to begin",
            "Punch as many times as you can in 15 seconds!",
            "",
            "Press 'Q' to QUIT"
        ]

        start_y = height // 2
        for i, instruction in enumerate(instructions):
            text_size = cv2.getTextSize(instruction, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            text_x = (width - text_size[0]) // 2
            text_y = start_y + i * 40
            color = (0, 255, 0) if "START" in instruction else (200, 200, 200)
            cv2.putText(image, instruction, (text_x, text_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    def _draw_countdown_screen(self, image, game_state, width, height):
        """Draw the countdown screen (3-2-1-GO)."""
        # Dark overlay
        overlay = image.copy()
        cv2.rectangle(overlay, (0, 0), (width, height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.5, image, 0.5, 0, image)

        # Get countdown value
        countdown_value = game_state.get_countdown_value()

        if countdown_value is not None:
            if countdown_value == 0:
                text = "GO!"
                color = (0, 255, 0)
                font_scale = 3.0
            else:
                text = str(countdown_value)
                color = (255, 255, 255)
                font_scale = 4.0

            # Draw countdown number/text
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_BOLD, font_scale, 5)[0]
            text_x = (width - text_size[0]) // 2
            text_y = (height + text_size[1]) // 2
            cv2.putText(image, text, (text_x, text_y),
                       cv2.FONT_HERSHEY_BOLD, font_scale, color, 5)

    def _draw_game_over_screen(self, image, game_state, width, height):
        """Draw the game over screen with final stats."""
        # Dark overlay
        overlay = image.copy()
        cv2.rectangle(overlay, (0, 0), (width, height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, image, 0.3, 0, image)

        # Game Over title
        title = "TIME'S UP!"
        title_size = cv2.getTextSize(title, cv2.FONT_HERSHEY_BOLD, 2.0, 4)[0]
        title_x = (width - title_size[0]) // 2
        title_y = height // 4
        cv2.putText(image, title, (title_x, title_y),
                   cv2.FONT_HERSHEY_BOLD, 2.0, (0, 0, 255), 4)

        # High score indicator if new record
        if game_state.is_new_high_score():
            new_record = "NEW HIGH SCORE!"
            record_size = cv2.getTextSize(new_record, cv2.FONT_HERSHEY_BOLD, 1.2, 3)[0]
            record_x = (width - record_size[0]) // 2
            record_y = height // 4 + 60
            cv2.putText(image, new_record, (record_x, record_y),
                       cv2.FONT_HERSHEY_BOLD, 1.2, (0, 255, 0), 3)

        # Final stats
        stats = [
            f"FINAL SCORE: {game_state.get_score()}",
            f"Total Punches: {game_state.get_punch_count()}",
            f"Max Combo: {game_state.max_combo_this_game}x",
            "",
            f"High Score: {game_state.get_high_score()}"
        ]

        start_y = height // 2 - 40
        for i, stat in enumerate(stats):
            if stat == "":
                continue
            text_size = cv2.getTextSize(stat, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0]
            text_x = (width - text_size[0]) // 2
            text_y = start_y + i * 50
            color = (0, 255, 255) if "High Score" in stat else (255, 255, 255)
            cv2.putText(image, stat, (text_x, text_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)

        # Restart instructions
        restart_text = "Press 'R' to RESTART"
        restart_size = cv2.getTextSize(restart_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
        restart_x = (width - restart_size[0]) // 2
        restart_y = height - 100
        cv2.putText(image, restart_text, (restart_x, restart_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    def _draw_timer(self, image, game_state, width):
        """Draw the game timer during playing mode."""
        remaining = game_state.get_remaining_time()
        timer_text = f"Time: {remaining:.1f}s"

        # Change color when time is running low
        if remaining <= 5.0:
            color = (0, 0, 255)  # Red
        elif remaining <= 10.0:
            color = (0, 165, 255)  # Orange
        else:
            color = (255, 255, 255)  # White

        # Draw timer in top-right
        text_size = cv2.getTextSize(timer_text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0]
        text_x = width - text_size[0] - 20
        cv2.putText(image, timer_text, (text_x, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)