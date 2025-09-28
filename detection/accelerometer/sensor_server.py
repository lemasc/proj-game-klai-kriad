import threading
import time
import queue
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import os


class SensorServer:
    """Flask-SocketIO server for receiving sensor data from smartphone via WebSocket"""

    def __init__(self, sensor_data_callback, game_state_provider, config):
        """
        Initialize sensor server

        Args:
            sensor_data_callback: Function to call when sensor data is received
            game_state_provider: Function that returns current game state dict
            config: Configuration object with server settings
        """
        self.sensor_data_callback = sensor_data_callback
        self.game_state_provider = game_state_provider
        self.config = config

        # Flask app setup
        self.app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '../../templates'))
        self.app.config['SECRET_KEY'] = config.FLASK_SECRET_KEY
        self.app.logger.disabled = True  # Disable Flask logs

        # SocketIO setup
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", logger=False, engineio_logger=False)

        # Setup routes and handlers
        self._setup_routes()
        self._setup_socket_handlers()

        # Server thread
        self.server_thread = None

    def _setup_routes(self):
        """Setup Flask routes"""
        @self.app.route('/')
        def index():
            return render_template('index.html')

    def _setup_socket_handlers(self):
        """Setup SocketIO event handlers"""

        @self.socketio.on('connect')
        def handle_connect():
            print(f"Client connected: {request.sid}")
            game_state = self.game_state_provider()
            emit('status', {
                'connected': True,
                'score': game_state.get('score', 0),
                'punches': game_state.get('punch_count', 0),
                'combo': game_state.get('combo_count', 0)
            })

        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f"Client disconnected: {request.sid}")

        @self.socketio.on('sensor_data')
        def handle_sensor_data(data):
            try:
                if data:
                    # Add timestamp if not present
                    if 'timestamp' not in data:
                        data['timestamp'] = time.time() * 1000

                    # Pass data to callback
                    queue_size = self.sensor_data_callback(data)
                    emit('sensor_ack', {'status': 'ok', 'queue_size': queue_size})
            except Exception as e:
                print(f"Error receiving sensor data: {e}")
                emit('sensor_ack', {'status': 'error'})

        @self.socketio.on('get_status')
        def handle_get_status():
            game_state = self.game_state_provider()
            emit('status', {
                'connected': True,
                'score': game_state.get('score', 0),
                'punches': game_state.get('punch_count', 0),
                'combo': game_state.get('combo_count', 0)
            })

    def start(self):
        """Start the sensor server in a background thread"""
        def run_server():
            self.socketio.run(
                self.app,
                host=self.config.SERVER_HOST,
                port=self.config.SERVER_PORT,
                debug=False
            )

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        print(f"Sensor server started on {self.config.SERVER_HOST}:{self.config.SERVER_PORT}")

    def emit_game_update(self, game_state):
        """Emit game state update to all connected clients"""
        self.socketio.emit('game_update', {
            'score': game_state.get('score', 0),
            'punches': game_state.get('punch_count', 0),
            'combo': game_state.get('combo_count', 0),
            'last_punch_score': game_state.get('last_punch_score', 0)
        })

    def is_running(self):
        """Check if server thread is running"""
        return self.server_thread is not None and self.server_thread.is_alive()