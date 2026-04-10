from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import httpx
import os
from datetime import datetime

app = FastAPI(title="Data Processor", version="1.0.0", root_path=os.getenv("ROOT_PATH", "/python-processor"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_start_time = datetime.utcnow()
_request_count = 0


@app.middleware("http")
async def count_requests(request: Request, call_next):
    global _request_count
    _request_count += 1
    return await call_next(request)

JAVA_API_URL = os.getenv("JAVA_API_URL", "http://localhost:8080")


class ProcessingRequest(BaseModel):
    action: str
    department: Optional[str] = None
    format: Optional[str] = "json"


class ReportRequest(BaseModel):
    report_type: str
    filters: Optional[dict] = None


@app.get("/health")
def health():
    return {"status": "healthy", "service": "python-processor", "timestamp": datetime.utcnow().isoformat()}


@app.get("/healthz")
def healthz():
    return {"status": "healthy"}


@app.get("/readyz")
def readyz():
    return {"status": "ready"}

@app.post("/api/process/users")
def process_users(request: ProcessingRequest):
    """Fetch users from Java API and process them."""
    try:
        response = httpx.get(f"{JAVA_API_URL}/api/users", timeout=10.0)
        data = response.json()
        users = data["users"]

        if request.action == "count_by_department":
            result = {}
            for user in users:
                dept = user.get("department", "Unknown")
                result[dept] = result.get(dept, 0) + 1
            return {"action": "count_by_department", "result": result}

        elif request.action == "count_by_role":
            result = {}
            for user in users:
                role = user.get("role", "Unknown")
                result[role] = result.get(role, 0) + 1
            return {"action": "count_by_role", "result": result}

        elif request.action == "active_ratio":
            total = len(users)
            active = sum(1 for u in users if u.get("active", False))
            ratio = round(active / total, 2) if total > 0 else 0
            return {"action": "active_ratio", "total": total, "active": active, "ratio": ratio}

        elif request.action == "export":
            if request.format == "csv":
                lines = ["name,email,department,role,active"]
                for u in users:
                    lines.append(",".join([
                        u.get("name", ""),
                        u.get("email", ""),
                        u.get("department", ""),
                        u.get("role", ""),
                        str(u.get("active", False)),
                    ]))
                return {"action": "export", "format": "csv", "data": "\n".join(lines)}
            return {"action": "export", "format": "json", "data": users}

        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")

    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Java API unavailable: {e}")
    except HTTPException:
        raise
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Error processing users: {e}")


@app.post("/api/reports/generate")
def generate_report(request: ReportRequest):
    """Generate various reports from user data."""
    try:
        resp = httpx.get(f"{JAVA_API_URL}/api/users", timeout=10.0)
        users = resp.json()["users"]

        if request.report_type == "summary":
            departments = set()
            roles = set()
            for u in users:
                departments.add(u.get("department", "Unknown"))
                roles.add(u.get("role", "Unknown"))
            return {
                "report_type": "summary",
                "generated_at": datetime.utcnow().isoformat(),
                "total_users": len(users),
                "departments": list(departments),
                "roles": list(roles),
                "active_count": sum(1 for u in users if u.get("active")),
                "inactive_count": sum(1 for u in users if not u.get("active")),
            }

        elif request.report_type == "department_detail":
            dept_data = {}
            for u in users:
                dept = u.get("department", "Unassigned")
                if dept not in dept_data:
                    dept_data[dept] = {"count": 0, "active": 0, "roles": set()}
                dept_data[dept]["count"] += 1
                if u.get("active"):
                    dept_data[dept]["active"] += 1
                dept_data[dept]["roles"].add(u.get("role", "Unknown"))
            for dept in dept_data:
                dept_data[dept]["roles"] = list(dept_data[dept]["roles"])
            return {
                "report_type": "department_detail",
                "generated_at": datetime.utcnow().isoformat(),
                "departments": dept_data,
            }

        else:
            raise HTTPException(status_code=400, detail=f"Unknown report type: {request.report_type}")

    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Cannot reach user service")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Report generation failed")


@app.get("/api/metrics")
def metrics():
    """Return service metrics for the monitoring dashboard."""
    now = datetime.utcnow()
    uptime = now - _start_time

    try:
        health_resp = httpx.get(f"http://localhost:{os.getenv('PORT', '8000')}{app.root_path}/health", timeout=3.0)
        health_status = health_resp.json().get("status", "unknown")
    except Exception:
        health_status = "unreachable"

    return {
        "total_requests_processed": _request_count,
        "uptime_seconds": int(uptime.total_seconds()),
        "uptime_human": str(uptime),
        "health_status": health_status,
        "started_at": _start_time.isoformat(),
        "checked_at": now.isoformat(),
    }
