from flask import Flask, request, redirect, session, render_template_string
import json, os, uuid

app = Flask(__name__)
app.secret_key = "ticket-secret"
DB_FILE = "db.json"
ADMIN_PASS = "1243"

# ---------- DB ----------
def load_db():
    if not os.path.exists(DB_FILE):
        db = {"concerts": [], "tickets": []}
        save_db(db)
        return db
    with open(DB_FILE, "r") as f:
        content = f.read().strip()
        if not content:
            return {"concerts": [], "tickets": []}
        return json.loads(content)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

# ---------- BASE TEMPLATE ----------
BASE_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }}</title>
<script src="https://cdn.jsdelivr.net/npm/jsbarcode@3.11.5/dist/JsBarcode.all.min.js"></script>
<style>
body {
    margin:0;
    font-family: Arial, sans-serif;
    background:#0b1f3a;
    color:white;
}
header {
    background:#08162b;
    padding:1em;
    text-align:center;
}
.container {
    padding:1em;
    max-width:800px;
    margin:auto;
}
.card {
    background:white;
    color:#0b1f3a;
    padding:1em;
    margin:1em 0;
    border-radius:10px;
}
button {
    background:#0b1f3a;
    color:white;
    border:none;
    padding:12px;
    width:100%;
    border-radius:6px;
    font-size:1em;
}
input {
    width:100%;
    padding:10px;
    margin:0.5em 0;
}
a { color:#0b1f3a; }
@media (max-width:600px){
    body { font-size:18px; }
}
</style>
</head>
<body>
<header><h1>{{ title }}</h1></header>
<div class="container">
{{ body|safe }}
</div>
</body>
</html>
"""

# ---------- ROUTES ----------
@app.route("/")
def home():
    db = load_db()
    body = ""
    for c in db["concerts"]:
        body += f"""
        <div class="card">
            <h2>{c['name']}</h2>
            <p>{c['venue']} — {c['date']}</p>
            <form method="POST" action="/buy/{c['id']}">
                <input name="name" placeholder="Your Name" required>
                <button>Buy Ticket</button>
            </form>
        </div>
        """
    return render_template_string(BASE_HTML, title="Concert Tickets", body=body)

@app.route("/buy/<cid>", methods=["POST"])
def buy(cid):
    db = load_db()
    name = request.form["name"]
    code = str(uuid.uuid4())
    db["tickets"].append({
        "code": code,
        "name": name,
        "concert": cid,
        "checked": False
    })
    save_db(db)
    return redirect(f"/ticket/{code}")

@app.route("/ticket/<code>")
def ticket(code):
    db = load_db()
    t = next((x for x in db["tickets"] if x["code"] == code), None)
    if not t:
        return "INVALID TICKET"
    status = "CHECKED IN" if t["checked"] else "VALID"
    body = f"""
    <div class="card">
        <h2>Your Ticket</h2>
        <p>Name: {t['name']}</p>
        <p>Status: {status}</p>
       
        <script>
            JsBarcode("#barcode", "{code}", {{
                format: "CODE128",
                lineColor: "#0b1f3a",
                width: 3,
                height: 100,
                displayValue: false
            }});
        </script>
        <p>Save this link</p>
    </div>
    """
    return render_template_string(BASE_HTML, title="Your Ticket", body=body)

@app.route("/scan/<code>")
def scan(code):
    db = load_db()
    t = next((x for x in db["tickets"] if x["code"] == code), None)
    if not t:
        return "INVALID"
    if t["checked"]:
        return "ALREADY USED"
    t["checked"] = True
    save_db(db)
    return "CHECK-IN OK"

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASS:
            session["admin"] = True
    if not session.get("admin"):
        body = """
        <form method="POST">
            <input type="password" name="password" placeholder="Admin Password">
            <button>Login</button>
        </form>
        """
        return render_template_string(BASE_HTML, title="Admin Login", body=body)

    db = load_db()
    body = """
    <h2>Create Concert</h2>
    <form method="POST" action="/create">
        <input name="name" placeholder="Concert Name" required>
        <input name="venue" placeholder="Venue" required>
        <input name="date" placeholder="Date" required>
        <button>Create</button>
    </form>
    <h2>Sold Tickets</h2>
    """
    for t in db["tickets"]:
        body += f"<p>{t['name']} — /scan/{t['code']}</p>"
    return render_template_string(BASE_HTML, title="Admin Panel", body=body)

@app.route("/create", methods=["POST"])
def create():
    if not session.get("admin"):
        return redirect("/admin")
    db = load_db()
    db["concerts"].append({
        "id": str(uuid.uuid4()),
        "name": request.form["name"],
        "venue": request.form["venue"],
        "date": request.form["date"]
    })
    save_db(db)
    return redirect("/admin")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
