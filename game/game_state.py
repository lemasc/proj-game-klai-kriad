"""
Game state management module for tracking score, combos, and punch statistics.
Handles all game logic related to scoring and state updates.
"""

import time
from game.game_config import *

class GameState:
    """
    Manages the game state including score, combos, and punch tracking.
    Provides methods for updating state and retrieving current status.
    """

    def __init__(self):
        """Initialize game state with default values."""
        self.score = 0
        self.punch_count = 0
        self.combo_count = 0
        self.last_punch_time = 0
        self.combo_timeout = COMBO_TIMEOUT  # seconds

        # For tracking the most recent punch details
        self.last_punch_score = 0

    def register_punch(self, punch_strength, timestamp=None):
        """
        Register a successful punch and update game state.

        Args:
            punch_strength: Float (0-1) representing punch quality/strength
            timestamp: Optional timestamp, uses current time if None

        Returns:
            dict: Details about the punch registration including points awarded
        """
        if timestamp is None:
            timestamp = time.time()

        self.punch_count += 1

        # Calculate base points based on punch quality
        points = int(punch_strength * BASE_SCORE_MULTIPLIER)

        # Apply combo system
        combo_bonus = self._update_combo_system(timestamp)
        total_points = points + combo_bonus

        # Update score and tracking
        self.score += total_points
        self.last_punch_time = timestamp
        self.last_punch_score = total_points

        return {
            'base_points': points,
            'combo_bonus': combo_bonus,
            'total_points': total_points,
            'new_score': self.score,
            'combo_count': self.combo_count,
            'punch_count': self.punch_count
        }

    def _update_combo_system(self, timestamp):
        """
        Update combo system based on timing between punches.

        Args:
            timestamp: Current punch timestamp

        Returns:
            int: Bonus points from combo
        """
        time_since_last = timestamp - self.last_punch_time

        if time_since_last < self.combo_timeout and self.last_punch_time > 0:
            # Continue combo
            self.combo_count += 1
            combo_bonus = self.combo_count * COMBO_BONUS_POINTS
        else:
            # Start new combo
            self.combo_count = 1
            combo_bonus = 0

        return combo_bonus

    def reset_score(self):
        """Reset all game state to initial values."""
        self.score = 0
        self.punch_count = 0
        self.combo_count = 0
        self.last_punch_time = 0
        self.last_punch_score = 0

    def get_state_dict(self):
        """
        Get current game state as a dictionary.

        Returns:
            dict: Complete game state information
        """
        return {
            'score': self.score,
            'punch_count': self.punch_count,
            'combo_count': self.combo_count,
            'last_punch_score': self.last_punch_score,
            'last_punch_time': self.last_punch_time
        }

    def is_combo_active(self):
        """
        Check if a combo is currently active.

        Returns:
            bool: True if combo count > 1
        """
        return self.combo_count > 1

    def get_combo_multiplier(self):
        """
        Get current combo multiplier for display purposes.

        Returns:
            int: Current combo count (minimum 1)
        """
        return max(1, self.combo_count)

    def get_score(self):
        """Get current score."""
        return self.score

    def get_punch_count(self):
        """Get total punch count."""
        return self.punch_count