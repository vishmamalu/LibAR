from __future__ import annotations

import math
import os
import re
import sqlite3
import time
from heapq import heappop, heappush
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "library.db"

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config["JSON_SORT_KEYS"] = False

# ---------------------------------------------------------------------------
# Library data model & 3D Spatial Geometry
# ---------------------------------------------------------------------------
BOOKS = [
    (1, "Introduction to Algorithms", "Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, Clifford Stein", "Algorithms", "Algorithms", "A1", 1, 2, "algorithm, algorithms, data structures, sorting, graph theory"),
    (2, "Computer Vision: Algorithms and Applications", "Richard Szeliski", "Computer Vision", "Artificial Intelligence", "AI_SHELF", 1, 1, "computer vision, image processing, visual recognition, AI"),
    (3, "Computer Architecture: A Quantitative Approach", "John L. Hennessy, David A. Patterson", "Computer Architecture", "Computer Science", "DB_SHELF", 1, 1, "architecture, processors, hardware, performance, organization"),
    (4, "Computer Networks", "Andrew S. Tanenbaum, David J. Wetherall", "Computer Networks", "Networking", "NETWORK_SHELF", 1, 2, "networks, networking, protocols, TCP, internet"),
    (5, "Database System Concepts", "Abraham Silberschatz, Henry F. Korth, S. Sudarshan", "Database Systems", "Database", "DB_SHELF", 1, 2, "database, DBMS, SQL, transactions, relational"),
    (6, "Fundamentals of Database Systems", "Ramez Elmasri, Shamkant Navathe", "Database Systems", "Database", "DB_SHELF", 1, 1, "database, DBMS, SQL, relational model"),
    (7, "Hands-On Machine Learning", "Aurélien Géron", "Machine Learning", "Artificial Intelligence", "AI_SHELF", 1, 2, "machine learning, ML, neural networks, deep learning, Python"),
    (8, "Deep Learning", "Ian Goodfellow, Yoshua Bengio, Aaron Courville", "Artificial Intelligence", "Artificial Intelligence", "AI_SHELF", 1, 2, "deep learning, neural networks, representation learning, AI"),
    (9, "Artificial Intelligence: A Modern Approach", "Stuart Russell, Peter Norvig", "Artificial Intelligence", "Artificial Intelligence", "AI_SHELF", 1, 2, "AI, artificial intelligence, intelligent agents, search"),
    (10, "Pattern Recognition and Machine Learning", "Christopher M. Bishop", "Machine Learning", "Artificial Intelligence", "AI_SHELF", 1, 1, "machine learning, pattern recognition, probabilistic models, ML"),
    (11, "Reinforcement Learning: An Introduction", "Richard S. Sutton, Andrew G. Barto", "Artificial Intelligence", "Artificial Intelligence", "AI_SHELF", 1, 1, "reinforcement learning, RL, agents, machine learning"),
    (12, "Operating System Concepts", "Abraham Silberschatz, Peter B. Galvin, Greg Gagne", "Operating Systems", "Systems", "CS_SHELF", 1, 1, "operating systems, processes, memory, scheduling"),
    (13, "Modern Operating Systems", "Andrew S. Tanenbaum, Herbert Bos", "Operating Systems", "Systems", "CS_SHELF", 1, 1, "operating systems, processes, virtualization"),
    (14, "Clean Code", "Robert C. Martin", "Software Engineering", "Software Engineering", "CS_SHELF", 1, 1, "software engineering, clean code, refactoring, programming"),
    (15, "Design Patterns", "Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides", "Software Engineering", "Software Engineering", "CS_SHELF", 1, 1, "design patterns, object oriented, software engineering"),
    (16, "Artificial Intelligence for Dummies", "John Paul Mueller, Luca Massaron", "Artificial Intelligence", "Artificial Intelligence", "AI_SHELF", 1, 1, "AI, machine learning, artificial intelligence"),
    (17, "Data Mining: Concepts and Techniques", "Jiawei Han, Micheline Kamber, Jian Pei", "Data Mining", "Data Science", "AI_SHELF", 1, 1, "data mining, classification, clustering, association rules"),
    (18, "Computer Graphics with OpenGL", "Donald D. Hearn, M. Pauline Baker", "Computer Graphics", "Computer Science", "CS_SHELF", 1, 1, "computer graphics, OpenGL, rendering, visualization"),
    (19, "Distributed Systems", "Maarten van Steen, Andrew S. Tanenbaum", "Distributed Systems", "Systems", "NETWORK_SHELF", 1, 1, "distributed systems, distributed computing, networks"),
    (20, "Cloud Computing", "Rajkumar Buyya, James Broberg, Andrzej Goscinski", "Cloud Computing", "Cloud", "NETWORK_SHELF", 1, 1, "cloud computing, virtualization, distributed systems"),
]

# 3D spatial node coordinates (x, y, z) in meters (VR world units: -Z is North, +X is East)
NODE_COORDINATES = {
    "ENTRANCE": {"x": 0.0, "y": 0.0, "z": 7.0, "label": "Library Entrance"},
    "MAIN_DESK": {"x": 0.0, "y": 0.0, "z": 4.0, "label": "Information & Help Desk"},
    "A1": {"x": -7.0, "y": 0.0, "z": -1.0, "label": "A1 · Algorithms Shelf"},
    "A2": {"x": 7.0, "y": 0.0, "z": -1.0, "label": "A2 · AI & ML Section"},
    "CS_SHELF": {"x": -7.0, "y": 0.0, "z": -9.0, "label": "CS · Computer Science Shelf"},
    "AI_SHELF": {"x": 7.0, "y": 0.0, "z": -9.0, "label": "AI · Artificial Intelligence Shelf"},
    "DB_SHELF": {"x": 0.0, "y": 0.0, "z": -12.0, "label": "DB · Database & Architecture Shelf"},
    "NETWORK_SHELF": {"x": 7.0, "y": 0.0, "z": -15.0, "label": "NETWORK · Networks & Cloud Shelf"},
    "EXIT": {"x": 7.0, "y": 0.0, "z": -19.0, "label": "Library Exit Gate"},
}

# Weighted indoor graph.
GRAPH = {
    "ENTRANCE": {"MAIN_DESK": 3, "A1": 4},
    "MAIN_DESK": {"ENTRANCE": 3, "A1": 2, "A2": 3},
    "A1": {"ENTRANCE": 4, "MAIN_DESK": 2, "CS_SHELF": 5, "DB_SHELF": 8},
    "A2": {"MAIN_DESK": 3, "AI_SHELF": 7, "DB_SHELF": 6},
    "CS_SHELF": {"A1": 5, "DB_SHELF": 4},
    "AI_SHELF": {"A2": 7},
    "DB_SHELF": {"A1": 8, "A2": 6, "CS_SHELF": 4, "NETWORK_SHELF": 3},
    "NETWORK_SHELF": {"DB_SHELF": 3, "EXIT": 4},
    "EXIT": {"NETWORK_SHELF": 4},
}

SHELVES = {
    "A1": {"name": "A1", "label": "Algorithms Shelf", "floor": 1, "category": "Algorithms", "color": "#7568df", "position": [-7.0, 0.0, -1.0]},
    "A2": {"name": "A2", "label": "AI / ML Section", "floor": 1, "category": "Artificial Intelligence", "color": "#7568df", "position": [7.0, 0.0, -1.0]},
    "CS_SHELF": {"name": "CS_SHELF", "label": "Computer Science Shelf", "floor": 1, "category": "Computer Science", "color": "#4c6a91", "position": [-7.0, 0.0, -9.0]},
    "AI_SHELF": {"name": "AI_SHELF", "label": "Artificial Intelligence Shelf", "floor": 1, "category": "Artificial Intelligence", "color": "#4c6a91", "position": [7.0, 0.0, -9.0]},
    "DB_SHELF": {"name": "DB_SHELF", "label": "Database & Architecture Shelf", "floor": 1, "category": "Database", "color": "#4c6a91", "position": [0.0, 0.0, -12.0]},
    "NETWORK_SHELF": {"name": "NETWORK_SHELF", "label": "Networks & Cloud Shelf", "floor": 1, "category": "Networking", "color": "#4c6a91", "position": [7.0, 0.0, -15.0]},
}

MARKERS = {
    "hiro": {"id": "hiro", "type": "pattern", "name": "Hiro Marker", "associated_node": "MAIN_DESK", "description": "Main Information Desk anchor"},
    "shelf_a1": {"id": "shelf_a1", "type": "barcode", "value": 1, "associated_node": "A1", "description": "Algorithms Shelf Marker"},
    "shelf_a2": {"id": "shelf_a2", "type": "barcode", "value": 2, "associated_node": "A2", "description": "AI / ML Section Marker"},
    "shelf_cs": {"id": "shelf_cs", "type": "barcode", "value": 3, "associated_node": "CS_SHELF", "description": "Computer Science Shelf Marker"},
    "shelf_ai": {"id": "shelf_ai", "type": "barcode", "value": 4, "associated_node": "AI_SHELF", "description": "Artificial Intelligence Shelf Marker"},
    "shelf_db": {"id": "shelf_db", "type": "barcode", "value": 5, "associated_node": "DB_SHELF", "description": "Database Shelf Marker"},
    "shelf_network": {"id": "shelf_network", "type": "barcode", "value": 6, "associated_node": "NETWORK_SHELF", "description": "Networks Shelf Marker"},
}

ALIASES = {
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "dbms": "database",
    "db": "database",
    "ds": "data structures",
    "os": "operating systems",
    "cn": "computer networks",
    "cv": "computer vision",
    "dl": "deep learning",
    "rl": "reinforcement learning",
    "se": "software engineering",
}


def get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            subject TEXT NOT NULL,
            category TEXT NOT NULL,
            shelf TEXT NOT NULL,
            floor INTEGER NOT NULL DEFAULT 1,
            copies INTEGER NOT NULL DEFAULT 1,
            keywords TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (shelf) REFERENCES shelves(name)
        );

        CREATE TABLE IF NOT EXISTS shelves (
            name TEXT PRIMARY KEY,
            label TEXT NOT NULL,
            floor INTEGER NOT NULL DEFAULT 1,
            description TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS search_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            result_count INTEGER NOT NULL,
            latency_ms REAL NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);
        CREATE INDEX IF NOT EXISTS idx_books_subject ON books(subject);
        CREATE INDEX IF NOT EXISTS idx_books_shelf ON books(shelf);
        """
    )
    for name, meta in SHELVES.items():
        conn.execute(
            "INSERT OR IGNORE INTO shelves(name,label,floor,description) VALUES (?,?,?,?)",
            (name, meta["label"], meta["floor"], f"{meta['label']} on floor {meta['floor']}"),
        )
    if conn.execute("SELECT COUNT(*) FROM books").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO books(id,title,author,subject,category,shelf,floor,copies,keywords) VALUES (?,?,?,?,?,?,?,?,?)",
            BOOKS,
        )
    conn.commit()
    conn.close()


def normalize(text: str) -> str:
    text = (text or "").lower().strip()
    for alias, expansion in ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", text):
            text = re.sub(rf"\b{re.escape(alias)}\b", f"{alias} {expansion}", text)
    return re.sub(r"[^a-z0-9\s]", " ", text)


def tokens(text: str) -> set[str]:
    return {t for t in normalize(text).split() if len(t) > 1}


def score_book(book: sqlite3.Row, query: str) -> float:
    q = normalize(query)
    qt = tokens(q)
    if not qt:
        return 0.0

    title = normalize(book["title"])
    author = normalize(book["author"])
    subject = normalize(book["subject"])
    category = normalize(book["category"])
    keywords = normalize(book["keywords"])
    corpus = f"{title} {author} {subject} {category} {keywords}"
    bt = tokens(corpus)

    overlap = len(qt & bt) / max(1, len(qt))
    title_overlap = len(qt & tokens(title)) / max(1, len(qt))
    subject_overlap = len(qt & tokens(subject)) / max(1, len(qt))
    author_overlap = len(qt & tokens(author)) / max(1, len(qt))
    keyword_overlap = len(qt & tokens(keywords)) / max(1, len(qt))

    phrase = 1.0 if q and q in corpus else 0.0
    starts = 1.0 if title.startswith(q) else 0.0
    availability_bonus = 0.03 if book["copies"] > 0 else 0.0

    raw = (
        0.25 * overlap
        + 0.28 * title_overlap
        + 0.14 * subject_overlap
        + 0.08 * author_overlap
        + 0.18 * keyword_overlap
        + 0.05 * phrase
        + 0.02 * starts
        + availability_bonus
    )
    return round(min(raw, 1.0) * 100, 2)


def book_dict(row: sqlite3.Row, relevance: float | None = None) -> dict[str, Any]:
    shelf_meta = SHELVES.get(row["shelf"], {})
    result = {
        "id": row["id"],
        "title": row["title"],
        "author": row["author"],
        "subject": row["subject"],
        "category": row["category"],
        "shelf": row["shelf"],
        "shelf_label": shelf_meta.get("label", row["shelf"]),
        "floor": row["floor"],
        "copies": row["copies"],
        "available": row["copies"] > 0,
        "availability": f"Available · {row['copies']} {'copy' if row['copies'] == 1 else 'copies'}" if row["copies"] > 0 else "Currently unavailable",
        "keywords": row["keywords"],
    }
    if relevance is not None:
        result["relevance"] = relevance
    return result


def find_books(query: str, limit: int = 20) -> list[dict[str, Any]]:
    conn = get_db()
    rows = conn.execute("SELECT * FROM books").fetchall()
    conn.close()
    scored = [(score_book(r, query), r) for r in rows]
    scored = [(s, r) for s, r in scored if s > 0]
    scored.sort(key=lambda x: (-x[0], -x[1]["copies"], x[1]["title"]))
    return [book_dict(r, s) for s, r in scored[:limit]]


def calculate_bearing(x1: float, z1: float, x2: float, z2: float) -> float:
    """Calculate compass bearing (0-360) from node 1 to node 2 in VR space (-Z is North, +X is East)."""
    dx = x2 - x1
    dz = z2 - z1
    # -dz is Northwards distance
    angle_rad = math.atan2(dx, -dz)
    bearing = math.degrees(angle_rad)
    return round((bearing + 360) % 360, 1)


def generate_maneuvers(path: list[str]) -> list[dict[str, Any]]:
    """Generate rich turn-by-turn navigation instructions with 3D bearings, distance, and maneuvers."""
    if not path or len(path) < 2:
        return []

    maneuvers: list[dict[str, Any]] = []
    prev_bearing: float | None = None

    for i in range(len(path) - 1):
        curr_node = path[i]
        next_node = path[i + 1]

        c_pos = NODE_COORDINATES.get(curr_node, {"x": 0.0, "y": 0.0, "z": 0.0, "label": curr_node})
        n_pos = NODE_COORDINATES.get(next_node, {"x": 0.0, "y": 0.0, "z": 0.0, "label": next_node})

        dist = round(math.sqrt((n_pos["x"] - c_pos["x"]) ** 2 + (n_pos["z"] - c_pos["z"]) ** 2), 1)
        if dist == 0:
            dist = float(GRAPH.get(curr_node, {}).get(next_node, 1.0))

        bearing = calculate_bearing(c_pos["x"], c_pos["z"], n_pos["x"], n_pos["z"])

        is_start = (i == 0)
        is_final = (i == len(path) - 2)

        if is_start:
            action = "start"
            instruction = f"Start at {c_pos['label']} and proceed toward {n_pos['label']}"
            turn_direction = "straight"
        else:
            diff = (bearing - prev_bearing + 180) % 360 - 180
            if abs(diff) < 20:
                action = "straight"
                turn_direction = "straight"
                instruction = f"Continue straight toward {n_pos['label']}"
            elif 20 <= diff < 70:
                action = "slight_right"
                turn_direction = "slight_right"
                instruction = f"Bear slight right toward {n_pos['label']}"
            elif 70 <= diff < 120:
                action = "turn_right"
                turn_direction = "right"
                instruction = f"Turn right toward {n_pos['label']}"
            elif 120 <= diff <= 180:
                action = "sharp_right"
                turn_direction = "sharp_right"
                instruction = f"Sharp right turn toward {n_pos['label']}"
            elif -70 < diff <= -20:
                action = "slight_left"
                turn_direction = "slight_left"
                instruction = f"Bear slight left toward {n_pos['label']}"
            elif -120 < diff <= -70:
                action = "turn_left"
                turn_direction = "left"
                instruction = f"Turn left toward {n_pos['label']}"
            else:
                action = "sharp_left"
                turn_direction = "sharp_left"
                instruction = f"Sharp left turn toward {n_pos['label']}"

        if is_final:
            instruction += f". Destination shelf is on your arrival."

        maneuvers.append({
            "step_index": i,
            "from_node": curr_node,
            "to_node": next_node,
            "from_label": c_pos["label"],
            "to_label": n_pos["label"],
            "action": action,
            "turn_direction": turn_direction,
            "instruction": instruction,
            "distance_meters": dist,
            "bearing_degrees": bearing,
            "from_coordinates": [c_pos["x"], c_pos["y"], c_pos["z"]],
            "to_coordinates": [n_pos["x"], n_pos["y"], n_pos["z"]],
            "is_final_leg": is_final,
        })
        prev_bearing = bearing

    return maneuvers


def shortest_path(start: str, target: str) -> tuple[list[str], float]:
    if start not in GRAPH or target not in GRAPH:
        raise ValueError("Unknown route node")
    distances = {node: math.inf for node in GRAPH}
    previous: dict[str, str | None] = {node: None for node in GRAPH}
    distances[start] = 0
    heap = [(0, start)]
    while heap:
        distance, node = heappop(heap)
        if distance != distances[node]:
            continue
        if node == target:
            break
        for nxt, weight in GRAPH[node].items():
            nd = distance + weight
            if nd < distances[nxt]:
                distances[nxt] = nd
                previous[nxt] = node
                heappush(heap, (nd, nxt))
    if math.isinf(distances[target]):
        raise ValueError("No route available")
    path = []
    cur: str | None = target
    while cur is not None:
        path.append(cur)
        cur = previous[cur]
    path.reverse()
    return path, distances[target]


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/ar")
@app.get("/ar.html")
def ar_view():
    return send_from_directory("static", "ar.html")


@app.get("/manifest.json")
def manifest():
    return send_from_directory("static", "manifest.json", mimetype="application/manifest+json")


@app.get("/sw.js")
def service_worker():
    return send_from_directory("static", "sw.js", mimetype="application/javascript")


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "LibAR", "version": "2.1", "mobile_ready": True, "ar_engine": "A-Frame+AR.js+SpatialCompass"})


@app.get("/api/stats")
def stats():
    conn = get_db()
    titles = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    available = conn.execute("SELECT COUNT(*) FROM books WHERE copies > 0").fetchone()[0]
    subjects = conn.execute("SELECT COUNT(DISTINCT subject) FROM books").fetchone()[0]
    shelves = conn.execute("SELECT COUNT(*) FROM shelves").fetchone()[0]
    copies = conn.execute("SELECT COALESCE(SUM(copies),0) FROM books").fetchone()[0]
    conn.close()
    return jsonify({
        "titles": titles,
        "available_titles": available,
        "subjects": subjects,
        "shelves": shelves,
        "total_copies": copies
    })


@app.get("/api/suggest")
def api_suggest():
    query = request.args.get("q", "").strip().lower()
    if not query or len(query) < 1:
        return jsonify([])
    conn = get_db()
    rows = conn.execute("SELECT title, author, subject, category FROM books").fetchall()
    conn.close()

    suggestions = set()
    for r in rows:
        title = r["title"]
        author = r["author"]
        subject = r["subject"]
        if query in title.lower():
            suggestions.add(title)
        if query in author.lower():
            suggestions.add(author)
        if query in subject.lower():
            suggestions.add(subject)

    return jsonify(sorted(list(suggestions))[:8])


@app.get("/api/books")
def api_books():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    available_only = request.args.get("available_only", "false").lower() == "true"
    limit = min(max(int(request.args.get("limit", 20)), 1), 50)
    started = time.perf_counter()

    if query:
        results = find_books(query, limit * 2)
    else:
        conn = get_db()
        rows = conn.execute("SELECT * FROM books ORDER BY id").fetchall()
        conn.close()
        results = [book_dict(r) for r in rows]

    if category and category.lower() != "all":
        results = [b for b in results if b["category"].lower() == category.lower() or b["subject"].lower() == category.lower()]

    if available_only:
        results = [b for b in results if b["available"]]

    results = results[:limit]
    latency = (time.perf_counter() - started) * 1000

    if query:
        conn = get_db()
        conn.execute("INSERT INTO search_log(query,result_count,latency_ms) VALUES (?,?,?)", (query, len(results), latency))
        conn.commit()
        conn.close()

    return jsonify(results)


@app.get("/api/books/<int:book_id>")
def api_book(book_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Book not found"}), 404
    return jsonify(book_dict(row))


@app.get("/api/recommendations")
def api_recommendations():
    query = request.args.get("q", "").strip()
    results = find_books(query, 10) if query else []
    if not results:
        return jsonify([])
    anchor = results[0]
    conn = get_db()
    rows = conn.execute("SELECT * FROM books WHERE id != ?", (anchor["id"],)).fetchall()
    conn.close()
    anchor_tokens = tokens(f"{anchor['subject']} {anchor['category']} {anchor['keywords']}")
    scored = []
    for row in rows:
        bt = tokens(f"{row['subject']} {row['category']} {row['keywords']}")
        sim = len(anchor_tokens & bt) / max(1, len(anchor_tokens | bt))
        if sim > 0:
            scored.append((sim, row))
    scored.sort(key=lambda x: (-x[0], x[1]["title"]))
    return jsonify([book_dict(row, round(sim * 100, 2)) for sim, row in scored[:6]])


@app.get("/api/route")
def api_route():
    target = request.args.get("target", "").strip().upper()
    start = request.args.get("start", "ENTRANCE").strip().upper()
    if target not in SHELVES:
        return jsonify({"error": "Invalid or unsupported shelf destination"}), 400
    try:
        path, distance = shortest_path(start, target)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    maneuvers = generate_maneuvers(path)
    path_nodes = [{"node": n, "label": NODE_COORDINATES.get(n, {}).get("label", n), "coordinates": [NODE_COORDINATES.get(n, {}).get("x", 0), NODE_COORDINATES.get(n, {}).get("y", 0), NODE_COORDINATES.get(n, {}).get("z", 0)]} for n in path]

    return jsonify({
        "start": start,
        "target": target,
        "path": path,
        "path_nodes": path_nodes,
        "distance_units": distance,
        "distance_meters": round(distance * 1.2, 1),
        "estimated_time_seconds": round(distance * 1.5),
        "waypoints": len(path),
        "maneuvers": maneuvers,
        "floor": SHELVES[target]["floor"],
        "destination_label": SHELVES[target]["label"],
        "destination_coordinates": NODE_COORDINATES.get(target, {}),
    })


@app.get("/api/shelves")
def api_shelves():
    return jsonify(list(SHELVES.values()))


@app.get("/api/markers")
def api_markers():
    return jsonify(list(MARKERS.values()))


@app.get("/api/metrics")
def api_metrics():
    conn = get_db()
    rows = conn.execute(
        "SELECT query, result_count, latency_ms, created_at FROM search_log ORDER BY id DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(500)
def server_error(_):
    return jsonify({"error": "Internal server error"}), 500


init_db()

if __name__ == "__main__":
    print("LibAR running at http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
