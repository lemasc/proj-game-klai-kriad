# Punch Detection Game - Complete Setup Guide

## 🎯 What This Does

This punch detection game combines smartphone accelerometer data with computer vision to detect and score punches. It uses your webcam to track body pose and your smartphone's sensors to measure punch force and speed.

## 📋 Requirements

- Computer with webcam
- Smartphone (Android/iOS)
- A stable network connection.

## 🚀 Setup Instructions

This project uses `uv`, a fast Python package manager with venv support out of the box. To install, visit [the official installation guide here](https://docs.astral.sh/uv/getting-started/installation/).

### Install dependencies

Simply clone this repo (or download ZIP), then run this command in your terminal.

```bash
uv sync
```

### Decide how your phone talk to your computer

You can actually run this without a companion device, but it's highly recommended for better precision.

To send accelerometer sensor data to your computer, this prototype starts a web server for your phone to connect. That said, you must know how to connect between the two.

#### 1. Use Computer IP Address

> [!WARNING]
>
> On iOS, this won't work because the website requires HTTPS. See section 2.

Ensure your phone and your computer is running on the same Wi-Fi, if not, see section 2.

Find your computer IP address by running this in your terminal.

**Windows:**

```cmd
ipconfig
```

Look for "IPv4 Address" under your WiFi adapter (usually starts with 192.168.x.x)

**Mac/Linux:**

```bash
ifconfig
```

Look for "inet" under your WiFi interface (usually starts with 192.168.x.x)

#### 2. Use an HTTPS tunnel (Workaround on iOS)

If you are not on the same Wi-Fi, or facing with the "permission denied" on iOS, you can use an HTTPS tunnel software. `ngrok` is an easy one. Search for how to install and use it. The port to expose is `5000`.

### Start the Game

```bash
uv run main.py
```

You should see:

```
Starting sensor server...
Sensor server started on port 5000
Open the smartphone web interface to connect accelerometer
Starting Punch Detection Game...
```

### Connect Your Smartphone

1. Visit the web page on your phone's browser.
   - For example, if your IP address is `192.168.1.100`, then visit Usually `http://192.168.100:5000`.
   - If running with ngrok, then your URL will be something like `https://some-random-name.ngrok-free.app`.
2. Tap "Start Tracking"
3. Grant motion sensor permissions when prompted

## 🎮 How to Play

### Basic Controls

- **Space Bar**: Manual punch trigger (for testing)
- **R Key**: Reset score
- **Q Key**: Quit game

### Gameplay

1. Stand 3-6 feet from your webcam
2. Hold your smartphone in your dominant hand
3. Face the camera so your full upper body is visible
4. Start punching! The game detects:
   - Punch speed (from accelerometer)
   - Arm extension (from camera)
   - Combo sequences
   - Punch accuracy

### Scoring System

- **Base Points**: 0-100 per punch (based on force/speed)
- **Combo Bonus**: +10 points per combo hit
- **Combo Timer**: 2 seconds to maintain combo

## 🔧 Troubleshooting

### Common Issues

**"Sensor: Disconnected" appears on game screen:**

- Check that both devices are on same WiFi
- Verify IP address is correct
- Make sure smartphone interface shows "Connected & Tracking"

**Smartphone can't connect:**

- Disable firewall temporarily
- Try different browser on phone
- Check if port 5000 is blocked

**Low punch detection accuracy:**

- Ensure good lighting for camera
- Stand closer/farther from camera
- Hold phone more firmly
- Adjust thresholds in code if needed

### Real-time Metrics

- **Acceleration**: Current movement intensity
- **Punches Sent**: Number of data packets sent
- **Game Score**: Live score from the game
- **Connected**: Connection status indicator

## 🎯 Game Features

### Visual Elements

- **Pose tracking**: Real-time skeleton overlay
- **Punch effects**: Screen flash on successful punches
- **Score display**: Live score, combo counter, punch count
- **Connection status**: Shows if smartphone is connected

### Scoring Mechanics

- **Punch Quality**: Based on acceleration magnitude and pose
- **Combo System**: Consecutive punches within 2 seconds
- **Cooldown**: 0.5 seconds between punch detections
- **Weighted Scoring**: 70% accelerometer, 30% visual pose
