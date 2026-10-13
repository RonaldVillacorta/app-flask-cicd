"""Módulo para generar datos demo en memoria."""
import random
from datetime import datetime, timedelta

CATEGORIES = ["Infraestructura", "Seguridad", "DevOps", "Backend", "Frontend", "Base de Datos"]
STATUSES = ["Activo", "En Mantenimiento", "Pendiente", "Deprecado"]
ENVIRONMENTS = ["Producción", "Staging", "Desarrollo", "QA"]

def generate_demo_items(count: int = 120) -> list[dict]:
    """Genera una lista representativa de datos simulados."""
    random.seed(42)  # Semilla fija para consistencia en recargas
    items = []
    base_date = datetime.now() - timedelta(days=60)

    for i in range(1, count + 1):
        category = random.choice(CATEGORIES)
        status = random.choice(STATUSES)
        env = random.choice(ENVIRONMENTS)
        created_at = (base_date + timedelta(days=random.randint(0, 60), hours=random.randint(0, 23))).strftime("%Y-%m-%d %H:%M")
        
        items.append({
            "id": f"SRV-{i:04d}",
            "name": f"Servicio-{category[:3].upper()}-{i:03d}",
            "category": category,
            "environment": env,
            "status": status,
            "latency_ms": random.randint(12, 380),
            "cpu_usage": f"{random.randint(5, 95)}%",
            "created_at": created_at,
        })
    return items

DEMO_ITEMS = generate_demo_items()
