# LibAR — Mobile AR & 3D Library Navigation

**LibAR** is an intelligent indoor augmented reality navigation and book discovery application for academic and research libraries. It enables users on mobile phones (Android & iOS) and desktop to search library collections, view availability, calculate indoor shortest paths, and navigate directly to destination bookshelves using real-time motion-responsive 3D virtual guidance and live camera spatial AR.

---

## 🌟 Key Features

1. **Intelligent Book Discovery & Recommendations**
   - Fast tokenized search with abbreviation expansion (e.g. `ML` → Machine Learning, `DBMS` → Database, `OS` → Operating Systems).
   - Real-time autocomplete suggestions as you type.
   - Content-based recommendation engine matching subjects, categories, and keywords.
   - Category filtering (AI/ML, Databases, Systems, Algorithms, Networks) and stock availability toggle.

2. **Movement-Responsive AR / VR Navigation**
   - **📱 Spatial Compass AR (Camera Feed Overlay)**:
     - Real rear camera feed with HUD overlays.
     - Live 3D direction arrow calibrated to phone's gyroscope and magnetometer compass heading.
     - Real-time angular heading guidance (*"Turn Left 45°"*, *"Head Straight 8m"*, *"Turn Right 90°"*).
     - Optical marker detection (Hiro marker) with automatic fallback to spatial compass guidance when marker tracking is lost.
   - **🌐 3D Digital Twin (Virtual 3D Library)**:
     - A-Frame 3D library scene with aisles, bookshelves, help desk, entrance, and exit.
     - Gyroscopic look-controls: Turning your phone physically turns the virtual viewpoint in real time.
     - Virtual touch joystick and *"Step Forward"* button for natural mobile locomotion.
     - Glowing destination beacon and animated 3D floor pathway connecting waypoints.
   - **🔊 Voice Guidance & Haptic Chimes**:
     - Web Speech Synthesis API voice directions.
     - Haptic vibration patterns on arrival at destination shelf.

3. **Mobile-First Progressive Web App (PWA)**
   - Installable on iPhone (Add to Home Screen) and Android.
   - Service Worker caching for instant load times.
   - QR code sharing modal to open on mobile phones instantly.

---

## 🚀 Quick Start

### 1. Installation

Ensure Python 3.9+ is installed:

```bash
cd LibAR_Patent_Oriented
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

### 2. Running Locally (Desktop & Local Wi-Fi)

```bash
.\.venv\Scripts\python run_production.py
```
This starts the Waitress WSGI production server, discovers your local network IP address (e.g., `http://192.168.x.x:5000`), and prints a QR code in the terminal.

### 3. Running with Public HTTPS Tunnel (for Mobile Camera & Sensors)

Mobile browsers require HTTPS to access camera and orientation sensors. To start with a public HTTPS tunnel:

```bash
.\.venv\Scripts\python run_tunnel.py
```
This generates a secure HTTPS URL (e.g. `https://xxxx.loca.lt`) and prints an ASCII QR code in your terminal. Scan it with your phone's camera app to launch LibAR immediately!

---

## 🧪 Testing & Verification

Run the automated unit test suite:

```bash
python -m unittest discover tests
```

Evaluate search and Dijkstra shortest-path route latency:

```bash
python evaluate.py
```

---

## 📡 API Endpoints

- `GET /health` — Service health and AR engine status.
- `GET /api/stats` — Library catalogue statistics.
- `GET /api/suggest?q=<query>` — Live autocomplete suggestions.
- `GET /api/books?q=<query>&category=<cat>&available_only=<bool>` — Book search.
- `GET /api/books/<id>` — Detailed book metadata and shelf coordinates.
- `GET /api/recommendations?q=<query>` — Content-matched title recommendations.
- `GET /api/route?target=<shelf>&start=<node>` — Shortest path with step-by-step turn maneuvers.
- `GET /api/shelves` — List of all bookshelves and 3D coordinates.
- `GET /api/markers` — Optical marker mappings for AR anchors.
