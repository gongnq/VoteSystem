# ============================================================================
# CONFIGURATION GUIDE
# ============================================================================
# 1. JUDGE NAMES (line ~20): Change the JUDGES list.
# 2. GROUP NAMES (line ~25): Each entry is (group_id, display_name, category).
#    Change category to "NPI" or "NTI" once decided.
# 3. VOTE OPTIONS (line ~55): Words shown per category.
# 4. ADMIN PIN (line ~70): Set via ADMIN_PIN env var, defaults to "2026".
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
JUDGES = ["Rob", "Adam", "Volker", "Toby", "Leticia", "Prasad", "Amit", "Regien", "Richard", "Albert", "Yongzhi"]

# ---------------------------------------------------------------------------
# GROUPS — (id, display_name, category)
# "NPI_PRE" = NPI groups with the extra PRE-ORDER option (displayed as "NPI")
# ---------------------------------------------------------------------------
GROUPS = [
    # (id, full_name_for_voting, category, card_name_for_homepage)
    ("G-1",  "1. Echo Frames Reimagined: Your Private AI Assistant for Work, Life & Shopping", "NPI",
             "Echo Frames Reimagined"),
    ("G-2",  "2. Alexa UI Plus - Fire TV Smart Scene Analysis", "NPI",
             "Alexa UI Plus"),
    ("G-3",  "3. Pulse ID", "NPI_PRE",
             "Pulse ID badge"),
    ("G-4",  "4. Re-imagined Wireless Charging for Metal Cover Devices", "NPI",
             "Re-imagined Wireless Charging"),
    ("G-5",  "5. Story Pal: The AI-Plush That Brings Multilingual Stories to Life", "NPI_PRE",
             "Amazon Unveils Story Pal"),
    ("G-6",  "6. AI Powered Multimodal E-commerce Product Shooting Camera", "NPI_PRE",
             "AI Powered Multimodal Camera"),
    ("G-7",  "7. AI Vision Mate Glasses - Second Sight for the Visually Impaired", "NPI",
             "AI Vision Mate Glasses"),
    ("G-8",  "8. Detachable Flip Camera Module with 360-degree Field for Echo Show Devices", "NPI",
             "Detachable Flip 360 Camera"),
    ("G-9",  "9. Smart Necklace Transforms Daily Life With AI-Powered Personal Assistant", "NPI_PRE",
             "Smart Necklace"),
    ("G-10", "10. Chroma Mirror: The AI Stylist That Unlocks Your Most Confident Look", "NPI",
             "Chroma Mirror"),
    ("G-11", "11. An Inner Spider Speaker Construction for Full Range", "NTI",
             "Inner Spider Design"),
    ("G-12", "12. Edge to Edge Display Cover Lens", "NTI",
             "Edge to Edge display cover lens"),
    ("G-13", "13. BOBArtender - AI-Powered Bubble Tea Generation", "NTI",
             "BOBArtender"),
    ("G-14", "14. The Family AI Cinema Butler: A TV That Knows You and Brings You Together", "NTI",
             "The Family AI Cinema Butler"),
    ("G-15", "15. Stratos", "NTI",
             "Stratos: AI Platform"),
    ("G-16", "16. Multi-Modal Competitive Intelligence AI Agent", "NTI",
             "Multi-Modal AI Agent"),
    ("G-17", "17. Hercules: A Cloud-based AI/ML Platform", "NTI",
             "Hercules: A Cloud-based AI/ML Platform"),
    ("G-18", "18. Manufacturing Smart Assistant", "NTI",
             "Manufacturing Smart Assistant"),
    ("G-19", "19. Intelligent Quality: AI-Powered Battery Manufacturing at Scale", "NTI",
             "Intelligent Quality: AI-Powered"),
    ("G-20", "20. Green Design 1", "NTI",
             "Green Technology for Sustainablity"),
    ("G-21", "21. Green Design 2: New-to-Industry PCB Technologies of Recyclable Substrate & Additive Manufacturing", "NTI",
             "Recyclable Substrate PCB Technologies"),
]

# Maps internal category to the display label shown in badges and admin tabs
DISPLAY_CATEGORY = {"NPI": "NPI", "NPI_PRE": "NPI", "NTI": "NTI"}

# ---------------------------------------------------------------------------
# VOTE OPTIONS per category — judge can select multiple per group
# NPI = 2 options, NPI_PRE = 3 options (adds PRE-ORDER), NTI = 3 options
# ---------------------------------------------------------------------------
VOTE_OPTIONS_BY_CATEGORY = {
    "NPI": [
        {"label": "PRFAQ", "subtitle": "(Product / Feature Maker)"},
        {"label": "Customer Delight", "subtitle": "(Customer Pain Points / <br>Customer Will Love)"},
    ],
    "NPI_PRE": [
        {"label": "PRFAQ", "subtitle": "(Product / Feature Maker)"},
        {"label": "PRE-ORDER", "subtitle": "(Order Now & Pay Later 😊)"},
        {"label": "Customer Delight", "subtitle": "(Customer Pain Points / <br>Customer Will Love)"},
    ],
    "NTI": [

        {"label": "Product Concept", "subtitle": "(Technology Enabler)"},
        {"label": "Accelerator", "subtitle": "(Operational Excellence /<br>AI Implementation /<br>Sustainable Energy)"},
        {"label": "Think Big", "subtitle": "(Design for Long Term & Scalability)"},
    ],
}

# ---------------------------------------------------------------------------
# CATEGORY DESCRIPTIONS — shown on the vote page above the options
# ---------------------------------------------------------------------------
CATEGORY_DESCRIPTIONS = {
    "NPI": "New Product Concepts: Customer-facing innovations that address unmet market needs, driving new revenue streams through differentiated design and user experience",
    "NPI_PRE": "New Product Concepts: Customer-facing innovations that address unmet market needs, driving new revenue streams through differentiated design and user experience",
    "NTI": "New Innovation Pipeline: Core technology, AI-enabled manufacturing and product development, and sustainable solutions that strengthen capabilities, drive operational efficiency, and power next-generation products",
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
    cursor = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='votes'"
    )
    if cursor.fetchone():
        cols = [row[1] for row in db.execute("PRAGMA table_info(votes)").fetchall()]
        if "vote_choice" not in cols:
            db.execute("DROP TABLE votes")

    # Add comment column if missing
    cols = [row[1] for row in db.execute("PRAGMA table_info(votes)").fetchall()]
    if "comment" not in cols and "votes" in [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
        db.execute("ALTER TABLE votes ADD COLUMN comment TEXT DEFAULT ''")

    db.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            judge TEXT NOT NULL,
            group_id TEXT NOT NULL,
            vote_choice TEXT NOT NULL,
            comment TEXT DEFAULT '',
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
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
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
    import os
    fname = "icon-512.png" if "512" in request.path else "icon-192.png"
    fpath = os.path.join(os.path.dirname(__file__), fname)
    with open(fpath, "rb") as f:
        return Response(f.read(), mimetype="image/png")


@app.route("/api/config")
def api_config():
    group_list = []
    for gid, name, cat, *_rest in GROUPS:
        card_name = _rest[0] if _rest else name
        group_list.append({
            "id": gid,
            "name": name,
            "card_name": card_name,
            "category": cat,
            "display_category": DISPLAY_CATEGORY[cat],
            "vote_options": VOTE_OPTIONS_BY_CATEGORY[cat],
        })
    return jsonify({
        "judges": JUDGES,
        "groups": group_list,
        "category_descriptions": CATEGORY_DESCRIPTIONS,
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
    for gid, name, cat, *_rest in GROUPS:
        if gid == group_id:
            group_info = (gid, name, cat)
            break
    if not group_info:
        return jsonify({"error": "Invalid group"}), 400

    if not isinstance(vote_choices, list):
        return jsonify({"error": "vote_choices must be a list"}), 400

    # Empty selection: still counts as voted (judge reviewed but chose nothing)
    if len(vote_choices) == 0:
        vote_choices = []

    valid_labels = {opt["label"] for opt in VOTE_OPTIONS_BY_CATEGORY[group_info[2]]}
    for choice in vote_choices:
        if choice not in valid_labels:
            return jsonify({"error": f"Invalid vote choice: {choice}"}), 400

    # Enforce max 4 PRFAQ selections per judge
    if "PRFAQ" in vote_choices:
        db = get_db()
        rows = db.execute(
            "SELECT group_id, vote_choice FROM votes WHERE judge = ? AND group_id != ?",
            (judge, group_id),
        ).fetchall()
        prfaq_count = 0
        for r in rows:
            try:
                choices = json_mod.loads(r["vote_choice"])
            except (json_mod.JSONDecodeError, TypeError):
                choices = [r["vote_choice"]]
            if "PRFAQ" in choices:
                prfaq_count += 1
        if prfaq_count >= 4:
            return jsonify({"error": "You can only select PRFAQ for up to 4 groups"}), 400

    comment = data.get("comment", "").strip()

    vote_json = json_mod.dumps(vote_choices)
    db = get_db()
    db.execute("""
        INSERT INTO votes (judge, group_id, vote_choice, comment, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(judge, group_id)
        DO UPDATE SET vote_choice=excluded.vote_choice, comment=excluded.comment, updated_at=CURRENT_TIMESTAMP
    """, (judge, group_id, vote_json, comment))
    db.commit()
    return jsonify({"ok": True})


@app.route("/api/votes/<judge>")
def api_judge_votes(judge):
    if judge not in JUDGES:
        return jsonify({"error": "Invalid judge"}), 400
    db = get_db()
    rows = db.execute(
        "SELECT group_id, vote_choice, comment FROM votes WHERE judge = ?",
        (judge,),
    ).fetchall()
    votes = {}
    for r in rows:
        raw = r["vote_choice"]
        try:
            choices = json_mod.loads(raw)
        except (json_mod.JSONDecodeError, TypeError):
            choices = [raw]
        votes[r["group_id"]] = {"vote_choices": choices, "comment": r["comment"] or ""}
    return jsonify(votes)


@app.route("/api/results")
def api_results():
    db = get_db()
    rows = db.execute("SELECT group_id, vote_choice FROM votes").fetchall()

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
    for gid, name, cat, *_rest in GROUPS:
        dcat = DISPLAY_CATEGORY[cat]
        if dcat not in cat_groups:
            cat_groups[dcat] = []
            categories_order.append(dcat)
        vote_counts = tallies.get(gid, {})
        total_votes = sum(vote_counts.values())
        cat_groups[dcat].append({
            "group_id": gid,
            "name": name,
            "category": dcat,
            "original_category": cat,
            "votes": vote_counts,
            "total_votes": total_votes,
            "judge_count": judge_counts.get(gid, 0),
        })

    # Collect all unique option labels across sub-categories for each display category
    display_cat_options = {}
    for cat_key, opts in VOTE_OPTIONS_BY_CATEGORY.items():
        dcat = DISPLAY_CATEGORY[cat_key]
        if dcat not in display_cat_options:
            display_cat_options[dcat] = []
        for opt in opts:
            if opt["label"] not in display_cat_options[dcat]:
                display_cat_options[dcat].append(opt["label"])

    for cat in categories_order:
        option_labels = display_cat_options.get(cat, [])
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


@app.route("/api/comments")
def api_comments():
    db = get_db()
    rows = db.execute(
        "SELECT judge, group_id, comment FROM votes WHERE comment IS NOT NULL AND comment != ''"
    ).fetchall()
    # Group by group_id
    comments = {}
    for r in rows:
        gid = r["group_id"]
        if gid not in comments:
            comments[gid] = []
        comments[gid].append({"judge": r["judge"], "comment": r["comment"]})
    return jsonify(comments)


@app.route("/api/admin/verify", methods=["POST"])
def api_admin_verify():
    data = request.get_json(force=True)
    pin = data.get("pin", "")
    if pin == ADMIN_PIN:
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 403


@app.route("/api/admin/reset", methods=["POST"])
def api_admin_reset():
    data = request.get_json(force=True)
    pin = data.get("pin", "")
    if pin != ADMIN_PIN:
        return jsonify({"error": "Invalid PIN"}), 403
    db = get_db()
    db.execute("DELETE FROM votes")
    db.execute("DELETE FROM judge_sessions")
    db.commit()
    return jsonify({"ok": True, "message": "All votes and sessions have been cleared"})


# ---------------------------------------------------------------------------
# Init & run
# ---------------------------------------------------------------------------
init_db()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
