# ============================================================================
# CONFIGURATION GUIDE
# ============================================================================
# 1. JUDGE NAMES (line ~30): Change the JUDGES list.
# 2. GROUP NAMES (line ~35): Each entry is (group_id, display_name, category).
# 3. VOTE OPTIONS (line ~50): Words shown per category. Judge picks one.
# 4. ADMIN PIN (line ~60): Set via ADMIN_PIN env var, defaults to "2026".
# ============================================================================

import os
import sqlite3
import time
import json as json_mod
from flask import Flask, request, jsonify, render_template, g, Response

app = Flask(__name__)

# ---------------------------------------------------------------------------
# JUDGES
# ---------------------------------------------------------------------------
JUDGES = ["Rob", "Regien", "Adam", "Amit", "Alok", "Prasad", "Volker", "Toby", "Chien"]

# ---------------------------------------------------------------------------
# GROUPS — (id, display_name, category)
# ---------------------------------------------------------------------------
GROUPS = (
    [("NTI-1", "1. An Inner Spider Speaker Construction", "NTI"),
     ("NTI-2", "2. Edge to Edge Display Cover Lens", "NTI"),
     ("NTI-3", "3. BOBArtender - AI-Powered Bubble Tea", "NTI")]
    + [("NPI-1", "4. Echo Frames Reimagined", "NPI"),
       ("NPI-2", "5. Alexa UI Plus - Fire TV Smart Scene", "NPI"),
       ("NPI-3", "6. Pulse ID", "NPI")]
    + [("AI-1", "7. Stratos", "AI"),
       ("AI-2", "8. Multi-Modal Competitive Intelligence", "AI"),
       ("AI-3", "9. Hercules: Cloud-based AI/ML Platform", "AI"),
       ("AI-4", "10. Manufacturing Smart Assistant", "AI"),
       ("AI-5", "11. Intelligent Quality: AI Battery Mfg", "AI")]
)

# ---------------------------------------------------------------------------
# VOTE OPTIONS per category — judge can select multiple per group
# Each option: {"label": "...", "subtitle": "..."} or just {"label": "..."}
# ---------------------------------------------------------------------------
VOTE_OPTIONS_BY_CATEGORY = {
    "NPI": [
        {"label": "PRFAQ", "subtitle": "(Product Maker)"},
        {"label": "PRE-ORDER"},
        {"label": "Customer Delight"},
    ],
    "NTI": [
        {"label": "Product Concept"},
        {"label": "Accelerator"},
        {"label": "Think Big"},
    ],
    "AI": [
        {"label": "PRFAQ", "subtitle": "(Product Maker)"},
        {"label": "PRE-ORDER"},
        {"label": "Customer Delight"},
    ],
}

# ---------------------------------------------------------------------------
# CATEGORY DESCRIPTIONS — shown on the vote page above the options
# ---------------------------------------------------------------------------
CATEGORY_DESCRIPTIONS = {
    "NPI": "New Product Concepts: Customer-facing innovations that address unmet market needs, driving new revenue streams through differentiated design and user experience",
    "NTI": "New Innovation Pipeline: Core technology, AI-enabled manufacturing and product development, and sustainable solutions that strengthen capabilities, drive operational efficiency, and power next-generation products",
    "AI":  "AI & Automation: AI-enabled solutions driving operational efficiency and intelligent automation",
}

# ---------------------------------------------------------------------------
# ADMIN PIN
# ---------------------------------------------------------------------------
ADMIN_PIN = os.environ.get("ADMIN_PIN", "2026")

SESSION_TIMEOUT = 300
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "votes.db")


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA busy_timeout=5000")
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)

    # Migrate from old schema (c1/c2/c3) to new (vote_choice) if needed
    cursor = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='votes'"
    )
    if cursor.fetchone():
        cols = [row[1] for row in db.execute("PRAGMA table_info(votes)").fetchall()]
        if "vote_choice" not in cols:
            db.execute("DROP TABLE votes")

    db.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            judge TEXT NOT NULL,
            group_id TEXT NOT NULL,
            vote_choice TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(judge, group_id)
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS judge_sessions (
            judge TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            last_heartbeat REAL NOT NULL
        )
    """)
    db.commit()
    db.close()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/manifest.json")
def manifest():
    m = {
        "name": "2026 Asia Demo Crawl",
        "short_name": "Demo Crawl",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0f1117",
        "theme_color": "#0f1117",
        "icons": [
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"},
        ],
    }
    return Response(json_mod.dumps(m), mimetype="application/manifest+json")


@app.route("/sw.js")
def service_worker():
    sw = """
self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', e => e.respondWith(fetch(e.request)));
"""
    return Response(sw.strip(), mimetype="application/javascript")


@app.route("/icon-192.png")
@app.route("/icon-512.png")
def pwa_icon():
    size = 512 if "512" in request.path else 192
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">
      <rect width="{size}" height="{size}" rx="40" fill="#6c5ce7"/>
      <text x="50%" y="42%" dominant-baseline="middle" text-anchor="middle"
            font-family="sans-serif" font-weight="bold" font-size="{size//6}" fill="#fff">DEMO</text>
      <text x="50%" y="62%" dominant-baseline="middle" text-anchor="middle"
            font-family="sans-serif" font-weight="bold" font-size="{size//6}" fill="#fff">CRAWL</text>
    </svg>"""
    return Response(svg, mimetype="image/svg+xml")


@app.route("/api/config")
def api_config():
    group_list = []
    for gid, name, cat in GROUPS:
        group_list.append({
            "id": gid,
            "name": name,
            "category": cat,
            "vote_options": VOTE_OPTIONS_BY_CATEGORY[cat],
        })
    return jsonify({
        "judges": JUDGES,
        "groups": group_list,
        "category_descriptions": CATEGORY_DESCRIPTIONS,
        "vote_options_by_category": {
            cat: opts for cat, opts in VOTE_OPTIONS_BY_CATEGORY.items()
        },
    })


@app.route("/api/judge/lock", methods=["POST"])
def api_judge_lock():
    data = request.get_json(force=True)
    judge = data.get("judge", "").strip()
    session_id = data.get("session_id", "").strip()

    if judge not in JUDGES or not session_id:
        return jsonify({"error": "Invalid judge or session"}), 400

    db = get_db()
    now = time.time()

    row = db.execute(
        "SELECT session_id, last_heartbeat FROM judge_sessions WHERE judge = ?",
        (judge,),
    ).fetchone()

    if row and row["session_id"] != session_id:
        if now - row["last_heartbeat"] < SESSION_TIMEOUT:
            return jsonify({"error": "This judge is already in use on another device"}), 409

    db.execute("""
        INSERT INTO judge_sessions (judge, session_id, last_heartbeat)
        VALUES (?, ?, ?)
        ON CONFLICT(judge)
        DO UPDATE SET session_id=excluded.session_id, last_heartbeat=excluded.last_heartbeat
    """, (judge, session_id, now))
    db.commit()
    return jsonify({"ok": True})


@app.route("/api/judge/heartbeat", methods=["POST"])
def api_judge_heartbeat():
    data = request.get_json(force=True)
    judge = data.get("judge", "").strip()
    session_id = data.get("session_id", "").strip()

    if judge not in JUDGES or not session_id:
        return jsonify({"error": "Invalid"}), 400

    db = get_db()
    result = db.execute("""
        UPDATE judge_sessions SET last_heartbeat = ?
        WHERE judge = ? AND session_id = ?
    """, (time.time(), judge, session_id))
    db.commit()

    if result.rowcount == 0:
        return jsonify({"error": "Session expired"}), 410
    return jsonify({"ok": True})


@app.route("/api/judge/unlock", methods=["POST"])
def api_judge_unlock():
    data = request.get_json(force=True)
    judge = data.get("judge", "").strip()
    session_id = data.get("session_id", "").strip()

    db = get_db()
    db.execute(
        "DELETE FROM judge_sessions WHERE judge = ? AND session_id = ?",
        (judge, session_id),
    )
    db.commit()
    return jsonify({"ok": True})


@app.route("/api/judge/locked")
def api_judge_locked():
    db = get_db()
    now = time.time()
    rows = db.execute(
        "SELECT judge FROM judge_sessions WHERE last_heartbeat > ?",
        (now - SESSION_TIMEOUT,),
    ).fetchall()
    return jsonify([r["judge"] for r in rows])


@app.route("/api/vote", methods=["POST"])
def api_vote():
    data = request.get_json(force=True)
    judge = data.get("judge", "").strip()
    group_id = data.get("group_id", "").strip()
    vote_choices = data.get("vote_choices", [])

    if judge not in JUDGES:
        return jsonify({"error": "Invalid judge"}), 400

    group_info = None
    for gid, name, cat in GROUPS:
        if gid == group_id:
            group_info = (gid, name, cat)
            break
    if not group_info:
        return jsonify({"error": "Invalid group"}), 400

    if not isinstance(vote_choices, list) or len(vote_choices) == 0:
        return jsonify({"error": "Select at least one option"}), 400

    valid_labels = {opt["label"] for opt in VOTE_OPTIONS_BY_CATEGORY[group_info[2]]}
    for choice in vote_choices:
        if choice not in valid_labels:
            return jsonify({"error": f"Invalid vote choice: {choice}"}), 400

    vote_json = json_mod.dumps(vote_choices)
    db = get_db()
    db.execute("""
        INSERT INTO votes (judge, group_id, vote_choice, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(judge, group_id)
        DO UPDATE SET vote_choice=excluded.vote_choice, updated_at=CURRENT_TIMESTAMP
    """, (judge, group_id, vote_json))
    db.commit()
    return jsonify({"ok": True})


@app.route("/api/votes/<judge>")
def api_judge_votes(judge):
    if judge not in JUDGES:
        return jsonify({"error": "Invalid judge"}), 400
    db = get_db()
    rows = db.execute(
        "SELECT group_id, vote_choice FROM votes WHERE judge = ?",
        (judge,),
    ).fetchall()
    votes = {}
    for r in rows:
        raw = r["vote_choice"]
        try:
            choices = json_mod.loads(raw)
        except (json_mod.JSONDecodeError, TypeError):
            choices = [raw]
        votes[r["group_id"]] = {"vote_choices": choices}
    return jsonify(votes)


@app.route("/api/results")
def api_results():
    db = get_db()
    rows = db.execute("SELECT group_id, vote_choice FROM votes").fetchall()

    # Tally: for each group, count how many judges selected each option
    tallies = {}
    judge_counts = {}
    for r in rows:
        gid = r["group_id"]
        raw = r["vote_choice"]
        try:
            choices = json_mod.loads(raw)
        except (json_mod.JSONDecodeError, TypeError):
            choices = [raw]

        if gid not in tallies:
            tallies[gid] = {}
            judge_counts[gid] = 0
        judge_counts[gid] += 1
        for choice in choices:
            tallies[gid][choice] = tallies[gid].get(choice, 0) + 1

    results = []
    categories_order = []
    cat_groups = {}
    for gid, name, cat in GROUPS:
        if cat not in cat_groups:
            cat_groups[cat] = []
            categories_order.append(cat)
        vote_counts = tallies.get(gid, {})
        total_votes = sum(vote_counts.values())
        cat_groups[cat].append({
            "group_id": gid,
            "name": name,
            "category": cat,
            "votes": vote_counts,
            "total_votes": total_votes,
            "judge_count": judge_counts.get(gid, 0),
        })

    for cat in categories_order:
        option_labels = [opt["label"] for opt in VOTE_OPTIONS_BY_CATEGORY[cat]]
        groups = sorted(cat_groups[cat], key=lambda x: x["total_votes"], reverse=True)
        results.append({
            "category": cat,
            "vote_options": option_labels,
            "groups": groups,
        })

    return jsonify(results)


@app.route("/api/progress")
def api_progress():
    db = get_db()
    rows = db.execute(
        "SELECT judge, COUNT(*) as cnt FROM votes GROUP BY judge"
    ).fetchall()
    total_groups = len(GROUPS)
    progress = {}
    for j in JUDGES:
        progress[j] = {"completed": 0, "total": total_groups}
    for r in rows:
        if r["judge"] in progress:
            progress[r["judge"]]["completed"] = r["cnt"]
    return jsonify(progress)


@app.route("/api/admin/verify", methods=["POST"])
def api_admin_verify():
    data = request.get_json(force=True)
    pin = data.get("pin", "")
    if pin == ADMIN_PIN:
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 403


# ---------------------------------------------------------------------------
# Init & run
# ---------------------------------------------------------------------------
init_db()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
