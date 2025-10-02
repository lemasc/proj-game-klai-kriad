import threading
import time
import logging
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import os
from pyngrok import ngrok
import qrcode


class SensorServer:
    """Flask-SocketIO server for receiving sensor data from smartphone via WebSocket"""

    def __init__(self, sensor_data_callback, game_state_provider, config, recording_manager=None):
        """
        Initialize sensor server

        Args:
            sensor_data_callback: Function to call when sensor data is received
            game_state_provider: Function that returns current game state dict
            config: Configuration object with server settings
            recording_manager: Optional RecordingManager instance for ground truth logging
        """
        self.sensor_data_callback = sensor_data_callback
        self.game_state_provider = game_state_provider
        self.config = config
        self.recording_manager = recording_manager

        # Flask app setup
        self.app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '../../templates'))
        # Set a higher logging level to suppress lower-severity messages
        werkzeug_logger = logging.getLogger('werkzeug')
        werkzeug_logger.setLevel(logging.ERROR)
        
        self.app.config['SECRET_KEY'] = config.FLASK_SECRET_KEY
        self.app.logger.disabled = True  # Disable Flask logs

        # SocketIO setup
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", logger=False, engineio_logger=False)

        # Track connected clients
        self.connected_clients = set()

        # Setup routes and handlers
        self._setup_routes()
        self._setup_socket_handlers()

        # Server thread and ngrok tunnel
        self.server_thread = None
        self.ngrok_tunnel = None
        self.public_url = None

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
            self.connected_clients.add(request.sid)
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
            self.connected_clients.discard(request.sid)

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

        @self.socketio.on('ground_truth')
        def handle_ground_truth(data):
            try:
                if data and 'hand' in data:
                    # Capture server-side timestamp
                    server_timestamp = time.time()

                    # Forward to recording manager if available
                    if self.recording_manager:
                        self.recording_manager.record_ground_truth(
                            hand=data['hand'],
                            server_timestamp=server_timestamp
                        )
                        emit('ground_truth_ack', {'status': 'ok'})
                    else:
                        emit('ground_truth_ack', {'status': 'error', 'message': 'Recording not available'})
                else:
                    emit('ground_truth_ack', {'status': 'error', 'message': 'Invalid data'})
            except Exception as e:
                print(f"Error receiving ground truth: {e}")
                emit('ground_truth_ack', {'status': 'error', 'message': str(e)})

        @self.socketio.on('get_status')
        def handle_get_status():
            game_state = self.game_state_provider()
            emit('status', {
                'connected': True,
                'score': game_state.get('score', 0),
                'punches': game_state.get('punch_count', 0),
                'combo': game_state.get('combo_count', 0)
            })

    def _setup_ngrok(self):
        """Setup ngrok tunnel if enabled and auth token is available"""
        if not getattr(self.config, 'ENABLE_NGROK', True):
            return None

        auth_token = getattr(self.config, 'NGROK_AUTH_TOKEN', None)
        if not auth_token:
            print("Warning: NGROK_AUTH_TOKEN not found in configuration. Ngrok tunneling disabled.")
            print("To enable ngrok, add your auth token to .env file:")
            print("NGROK_AUTH_TOKEN=your_token_here")
            return None

        try:
            # Set auth token
            ngrok.set_auth_token(auth_token)

            # Create tunnel
            tunnel = ngrok.connect(self.config.SERVER_PORT)
            self.public_url = tunnel.public_url
            print(f"Ngrok tunnel established: {self.public_url}")

            # Generate and display QR code
            self._display_qr_code(self.public_url)

            return tunnel

        except Exception as e:
            print(f"Failed to setup ngrok tunnel: {e}")
            print("Continuing with local server only...")
            return None

    def _display_qr_code(self, url):
        """Generate and display QR code for the URL"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)

            # Print QR code to console
            qr.print_ascii(invert=True)
            print(f"\nScan the QR code above with your smartphone to connect!")
            print(f"Or visit: {url}")

        except Exception as e:
            print(f"Failed to generate QR code: {e}")

    def start(self):
        """Start the sensor server in a background thread"""
        def run_server():
            self.socketio.run(
                self.app,
                host=self.config.SERVER_HOST,
                port=self.config.SERVER_PORT,
                debug=False
            )

        self.ngrok_tunnel = self._setup_ngrok()

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()

        local_url = f"http://{self.config.SERVER_HOST}:{self.config.SERVER_PORT}"
        print(f"Sensor server started on {local_url}")

        if self.public_url:
            print(f"Public URL (via ngrok): {self.public_url}")
        else:
            print(f"Local access only: {local_url}")

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

    def stop(self):
        """Stop the server and cleanup ngrok tunnel"""
        if self.ngrok_tunnel:
            try:
                ngrok.disconnect(self.ngrok_tunnel.public_url)
                print("Ngrok tunnel closed")
            except Exception as e:
                print(f"Error closing ngrok tunnel: {e}")

        if self.server_thread and self.server_thread.is_alive():
            print("Stopping sensor server...")

    def get_public_url(self):
        """Get the public URL if ngrok is enabled, otherwise return local URL"""
        if self.public_url:
            return self.public_url
        return f"http://{self.config.SERVER_HOST}:{self.config.SERVER_PORT}"

    def has_connected_clients(self):
        """Check if there are any connected WebSocket clients"""
        return len(self.connected_clients) > 0

    def get_connected_client_count(self):
        """Get the number of connected WebSocket clients"""
        return len(self.connected_clients)