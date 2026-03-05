# ============================================================================
# CONFIGURATION GUIDE
# ============================================================================
# To customize this voting system, edit the following sections:
#
# 1. JUDGE NAMES (line ~35):
#    Change the JUDGES list to your actual judge names.
#    Example: JUDGES = ["Alice", "Bob", "Charlie"]
#
# 2. GROUP NAMES (line ~40):
#    Change the GROUPS list. Each entry is (group_id, display_name, category).
#    Categories must be one of: "NPI", "NTI", "AI"
#    Example: ("NPI-1", "Team Alpha", "NPI")
#
# 3. ADMIN PIN (line ~70):
#    Set via ADMIN_PIN environment variable, or defaults to "2025".
#    On Render, set it in the envVars section of render.yaml.
#
# 4. CRITERIA LABELS (line ~55):
#    The third criterion label changes by category:
#    - NPI/NTI groups see "Feasibility/Practicality"
#    - AI groups see "AI Practicality"
#    Modify CRITERIA_BY_CATEGORY to change labels.
#
# 5. AWARDS (line ~60):
#    Modify AWARDS to change award names, eligible categories, and weights.
# ============================================================================

import os
import sqlite3
import json as json_mod
from flask import Flask, request, jsonify, render_template, g, Response

app = Flask(__name__)

# ---------------------------------------------------------------------------
# JUDGES — edit this list to use real names
# ---------------------------------------------------------------------------
JUDGES = [f"Judge {i}" for i in range(1, 16)]

# ---------------------------------------------------------------------------
# GROUPS — (id, display_name, category)
# ---------------------------------------------------------------------------
GROUPS = (
    [("NPI-1", "Group NPI-1", "NPI"), ("NPI-2", "Group NPI-2", "NPI"),
     ("NPI-3", "Group NPI-3", "NPI"), ("NPI-4", "Group NPI-4", "NPI"),
     ("NPI-5", "Group NPI-5", "NPI"), ("NPI-6", "Group NPI-6", "NPI")]
    + [("NTI-1", "Group NTI-1", "NTI"), ("NTI-2", "Group NTI-2", "NTI"),
       ("NTI-3", "Group NTI-3", "NTI"), ("NTI-4", "Group NTI-4", "NTI"),
       ("NTI-5", "Group NTI-5", "NTI"), ("NTI-6", "Group NTI-6", "NTI")]
    + [("AI-1", "Group AI-1", "AI"), ("AI-2", "Group AI-2", "AI"),
       ("AI-3", "Group AI-3", "AI"), ("AI-4", "Group AI-4", "AI"),
       ("AI-5", "Group AI-5", "AI"), ("AI-6", "Group AI-6", "AI")]
)

# ---------------------------------------------------------------------------
# CRITERIA per category — the 4 slider labels shown in the UI
# ---------------------------------------------------------------------------
CRITERIA_BY_CATEGORY = {
    "NPI": ["Innovation/Originality", "Customer Delight",
            "Feasibility/Practicality", "Market Opportunity"],
    "NTI": ["Innovation/Originality", "Customer Delight",
            "Feasibility/Practicality", "Market Opportunity"],
    "AI":  ["Innovation/Originality", "Customer Delight",
            "AI Practicality", "Market Opportunity"],
}

# ---------------------------------------------------------------------------
# AWARDS — name, eligible_categories (None = all), criteria indices & weights
# Criteria indices map to the 4 stored score columns (c1–c4) in order.
# ---------------------------------------------------------------------------
AWARDS = [
    {
        "name": "Product Breakthrough Award",
        "categories": ["NPI"],
        "weights": {0: 1, 1: 1, 2: 1, 3: 1},
    },
    {
        "name": "Technology Frontier Award",
        "categories": ["NTI"],
        "weights": {0: 1, 1: 1, 2: 1, 3: 1},
    },
    {
        "name": "Customer Delight Award",
        "categories": None,  # all 18 groups
        "weights": {1: 1},   # only Customer Delight (index 1)
    },
    {
        "name": "AI Excellence Award",
        "categories": ["AI"],
        "weights": {0: 1, 1: 1, 2: 1, 3: 1},
    },
]

# ---------------------------------------------------------------------------
# ADMIN PIN
# ---------------------------------------------------------------------------
ADMIN_PIN = os.environ.get("ADMIN_PIN", "2026")

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
    db.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            judge TEXT NOT NULL,
            group_id TEXT NOT NULL,
            c1 INTEGER NOT NULL CHECK(c1 BETWEEN 1 AND 5),
            c2 INTEGER NOT NULL CHECK(c2 BETWEEN 1 AND 5),
            c3 INTEGER NOT NULL CHECK(c3 BETWEEN 1 AND 5),
            c4 INTEGER NOT NULL CHECK(c4 BETWEEN 1 AND 5),
            comment TEXT DEFAULT '',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(judge, group_id)
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
    """Generate a simple SVG-based PNG placeholder icon."""
    size = 512 if "512" in request.path else 192
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}">
      <rect width="{size}" height="{size}" rx="40" fill="#6c5ce7"/>
      <text x="50%" y="52%" dominant-baseline="middle" text-anchor="middle"
            font-family="sans-serif" font-weight="bold" font-size="{size//6}" fill="#fff">DemoCrawl</text>
    </svg>"""
    return Response(svg, mimetype="image/svg+xml")


@app.route("/api/config")
def api_config():
    group_list = []
    for gid, name, cat in GROUPS:
        group_list.append({
            "id": gid, "name": name, "category": cat,
            "criteria": CRITERIA_BY_CATEGORY[cat],
        })
    return jsonify({
        "judges": JUDGES,
        "groups": group_list,
        "awards": [{"name": a["name"],
                     "categories": a["categories"],
                     "weights": {str(k): v for k, v in a["weights"].items()}}
                    for a in AWARDS],
    })


@app.route("/api/vote", methods=["POST"])
def api_vote():
    data = request.get_json(force=True)
    judge = data.get("judge", "").strip()
    group_id = data.get("group_id", "").strip()
    scores = data.get("scores", [])
    comment = data.get("comment", "").strip()

    if judge not in JUDGES:
        return jsonify({"error": "Invalid judge"}), 400

    valid_ids = {g[0] for g in GROUPS}
    if group_id not in valid_ids:
        return jsonify({"error": "Invalid group"}), 400

    if not isinstance(scores, list) or len(scores) != 4:
        return jsonify({"error": "Scores must be a list of 4 integers"}), 400
    for s in scores:
        if not isinstance(s, int) or s < 1 or s > 5:
            return jsonify({"error": "Each score must be 1-5"}), 400

    db = get_db()
    db.execute("""
        INSERT INTO votes (judge, group_id, c1, c2, c3, c4, comment, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(judge, group_id)
        DO UPDATE SET c1=excluded.c1, c2=excluded.c2, c3=excluded.c3,
                      c4=excluded.c4, comment=excluded.comment,
                      updated_at=CURRENT_TIMESTAMP
    """, (judge, group_id, scores[0], scores[1], scores[2], scores[3], comment))
    db.commit()
    return jsonify({"ok": True})


@app.route("/api/votes/<judge>")
def api_judge_votes(judge):
    if judge not in JUDGES:
        return jsonify({"error": "Invalid judge"}), 400
    db = get_db()
    rows = db.execute(
        "SELECT group_id, c1, c2, c3, c4, comment FROM votes WHERE judge = ?",
        (judge,),
    ).fetchall()
    votes = {}
    for r in rows:
        votes[r["group_id"]] = {
            "scores": [r["c1"], r["c2"], r["c3"], r["c4"]],
            "comment": r["comment"],
        }
    return jsonify(votes)


@app.route("/api/results")
def api_results():
    db = get_db()
    rows = db.execute("SELECT group_id, c1, c2, c3, c4 FROM votes").fetchall()

    group_scores = {}
    for r in rows:
        gid = r["group_id"]
        if gid not in group_scores:
            group_scores[gid] = {"scores": [[], [], [], []], "count": 0}
        group_scores[gid]["scores"][0].append(r["c1"])
        group_scores[gid]["scores"][1].append(r["c2"])
        group_scores[gid]["scores"][2].append(r["c3"])
        group_scores[gid]["scores"][3].append(r["c4"])
        group_scores[gid]["count"] += 1

    awards_result = []
    for award in AWARDS:
        eligible = []
        for gid, name, cat in GROUPS:
            if award["categories"] is not None and cat not in award["categories"]:
                continue
            if gid not in group_scores:
                eligible.append({
                    "group_id": gid, "name": name, "category": cat,
                    "avg_score": 0, "judge_count": 0,
                })
                continue
            gs = group_scores[gid]
            total_weight = sum(award["weights"].values())
            weighted_sum = 0
            for idx, w in award["weights"].items():
                criterion_scores = gs["scores"][idx]
                if criterion_scores:
                    weighted_sum += w * (sum(criterion_scores) / len(criterion_scores))
            avg = weighted_sum / total_weight if total_weight > 0 else 0
            eligible.append({
                "group_id": gid, "name": name, "category": cat,
                "avg_score": round(avg, 2), "judge_count": gs["count"],
            })
        eligible.sort(key=lambda x: x["avg_score"], reverse=True)
        awards_result.append({"award": award["name"], "groups": eligible})
    return jsonify(awards_result)


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
