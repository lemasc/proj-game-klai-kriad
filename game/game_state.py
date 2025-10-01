"""
Game state management module for tracking score, combos, and punch statistics.
Handles all game logic related to scoring and state updates.
"""

import time
import json
import os
from enum import Enum
from game.game_config import *

class GameMode(Enum):
    """Game mode states"""
    MENU = "menu"
    COUNTDOWN = "countdown"
    PLAYING = "playing"
    GAME_OVER = "game_over"

class GameState:
    """
    Manages the game state including score, combos, and punch tracking.
    Provides methods for updating state and retrieving current status.
    """

    def __init__(self, event_manager=None):
        """Initialize game state with default values.

        Args:
            event_manager: Optional event manager for triggering game mode changes
        """
        self.event_manager = event_manager
        self.score = 0
        self.punch_count = 0
        self.combo_count = 0
        self.last_punch_time = 0
        self.combo_timeout = COMBO_TIMEOUT  # seconds

        # For tracking the most recent punch details
        self.last_punch_score = 0

        # Game mode management
        self.game_mode = GameMode.MENU
        self.game_timer = 0
        self.game_duration = 15.0  # 15 seconds game time
        self.countdown_start_time = 0
        self.game_start_time = 0

        # High score tracking
        self.high_score = 0
        self.high_score_file = "game/high_score.json"
        self.max_combo_this_game = 0
        self._load_high_score()

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

        # Track max combo this game
        if self.combo_count > self.max_combo_this_game:
            self.max_combo_this_game = self.combo_count

        return combo_bonus

    def reset_score(self):
        """Reset all game state to initial values."""
        self.score = 0
        self.punch_count = 0
        self.combo_count = 0
        self.last_punch_time = 0
        self.last_punch_score = 0
        self.max_combo_this_game = 0

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

    def start_game(self):
        """Start countdown sequence."""
        self.game_mode = GameMode.COUNTDOWN
        self.countdown_start_time = time.time()
        self.reset_score()
        self._trigger_mode_changed()

    def start_countdown(self):
        """Alias for start_game for clarity."""
        self.start_game()

    def begin_playing(self):
        """Begin the actual playing phase after countdown."""
        self.game_mode = GameMode.PLAYING
        self.game_start_time = time.time()
        self.game_timer = 0
        self._trigger_mode_changed()

    def update_timer(self):
        """Update game timer and check for game over."""
        if self.game_mode == GameMode.PLAYING:
            self.game_timer = time.time() - self.game_start_time
            if self.game_timer >= self.game_duration:
                self.end_game()

    def end_game(self):
        """End the game and transition to game over screen."""
        self.game_mode = GameMode.GAME_OVER
        self.game_timer = self.game_duration
        self._check_and_save_high_score()
        self._trigger_mode_changed()

    def return_to_menu(self):
        """Return to menu screen."""
        self.game_mode = GameMode.MENU
        self.reset_score()
        self._trigger_mode_changed()

    def get_remaining_time(self):
        """Get remaining time in seconds."""
        if self.game_mode == GameMode.PLAYING:
            return max(0, self.game_duration - self.game_timer)
        return self.game_duration

    def is_playing(self):
        """Check if game is in playing mode."""
        return self.game_mode == GameMode.PLAYING

    def is_game_over(self):
        """Check if game is over."""
        return self.game_mode == GameMode.GAME_OVER

    def is_menu(self):
        """Check if in menu mode."""
        return self.game_mode == GameMode.MENU

    def is_countdown(self):
        """Check if in countdown mode."""
        return self.game_mode == GameMode.COUNTDOWN

    def get_countdown_value(self):
        """Get current countdown value (3, 2, 1, or 0 for GO)."""
        if self.game_mode != GameMode.COUNTDOWN:
            return None
        elapsed = time.time() - self.countdown_start_time
        if elapsed < 1.0:
            return 3
        elif elapsed < 2.0:
            return 2
        elif elapsed < 3.0:
            return 1
        elif elapsed < 3.5:
            return 0  # GO!
        else:
            # Countdown finished, start playing
            self.begin_playing()
            return None

    def _load_high_score(self):
        """Load high score from file."""
        try:
            if os.path.exists(self.high_score_file):
                with open(self.high_score_file, 'r') as f:
                    data = json.load(f)
                    self.high_score = data.get('high_score', 0)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Could not load high score: {e}")
            self.high_score = 0

    def _check_and_save_high_score(self):
        """Check if current score is a high score and save if it is."""
        if self.score > self.high_score:
            self.high_score = self.score
            self._save_high_score()

    def _save_high_score(self):
        """Save high score to file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.high_score_file), exist_ok=True)

            data = {
                'high_score': self.high_score,
                'timestamp': time.time()
            }
            with open(self.high_score_file, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Could not save high score: {e}")

    def get_high_score(self):
        """Get the current high score."""
        return self.high_score

    def is_new_high_score(self):
        """Check if the current score is a new high score."""
        return self.score == self.high_score and self.score > 0

    def _trigger_mode_changed(self):
        """Trigger game_mode_changed event if event manager is available."""
        if self.event_manager:
            self.event_manager.trigger_event('game_mode_changed', self.game_mode)