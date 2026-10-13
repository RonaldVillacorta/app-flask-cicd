import os
import platform
import sys
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from demo_data import DEMO_ITEMS, CATEGORIES, STATUSES

app = Flask(__name__)
APP_START_TIME = time.time()

def get_runtime_info():
    """Recopila telemetría y metadatos del entorno de ejecución."""
    uptime_seconds = int(time.time() - APP_START_TIME)
    uptime_formatted = f"{uptime_seconds // 3600}h {(uptime_seconds % 3600) // 60}m {uptime_seconds % 60}s"
    
    # Filtrar variables de entorno públicas y relevantes, evitando tokens/secrets
    allowed_env_prefixes = ("PYTHON", "FLASK", "PORT", "OS", "PATH", "LANG", "HOSTNAME", "WEBSITE_", "APP_")
    safe_env = {
        k: v for k, v in os.environ.items()
        if any(k.startswith(prefix) for prefix in allowed_env_prefixes) or k in {"USER", "USERNAME", "COMPUTERNAME"}
    }

    return {
        "hostname": platform.node(),
        "os_name": platform.system(),
        "os_release": platform.release(),
        "architecture": platform.machine(),
        "python_version": sys.version.split()[0],
        "python_path": sys.executable,
        "process_id": os.getpid(),
        "uptime": uptime_formatted,
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "env_vars": safe_env,
    }

@app.route("/")
def index():
    total_items = len(DEMO_ITEMS)
    active_count = sum(1 for item in DEMO_ITEMS if item["status"] == "Activo")
    maintenance_count = sum(1 for item in DEMO_ITEMS if item["status"] == "En Mantenimiento")
    avg_latency = round(sum(item["latency_ms"] for item in DEMO_ITEMS) / total_items, 1)

    metrics = {
        "total": total_items,
        "active": active_count,
        "maintenance": maintenance_count,
        "avg_latency": avg_latency,
        "categories_count": len(CATEGORIES),
    }
    return render_template("index.html", metrics=metrics, recent_items=DEMO_ITEMS[:6])

@app.route("/items")
def items():
    query = request.args.get("q", "").strip().lower()
    selected_category = request.args.get("category", "").strip()

    filtered = DEMO_ITEMS
    if selected_category:
        filtered = [item for item in filtered if item["category"] == selected_category]
    if query:
        filtered = [
            item for item in filtered
            if query in item["name"].lower() or query in item["id"].lower() or query in item["environment"].lower()
        ]

    return render_template(
        "items.html",
        items=filtered,
        categories=CATEGORIES,
        selected_category=selected_category,
        query=query,
        total_found=len(filtered)
    )

@app.route("/runtime")
def runtime():
    info = get_runtime_info()
    return render_template("runtime.html", runtime=info)

@app.route("/health")
def health():
    return jsonify({
        "status": "UP",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": int(time.time() - APP_START_TIME),
        "hostname": platform.node()
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
