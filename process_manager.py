import subprocess
import os
import signal
import psutil
from datetime import datetime
from config import PROJECTS_DIR, LOGS_DIR, RUNTIME_PYTHON, RUNTIME_NODE
from database import update_project_status, get_project


def start_bot(project_id):
    project = get_project(project_id)
    if not project:
        return False, "Project not found"

    if project["status"] == "running":
        return False, "Bot is already running"

    project_dir = os.path.join(PROJECTS_DIR, project["name"])
    if not os.path.exists(project_dir):
        return False, "Project directory not found"

    main_file = project["main_file"]
    main_path = os.path.join(project_dir, main_file)
    if not os.path.exists(main_path):
        return False, f"Main file '{main_file}' not found"

    log_dir = os.path.join(LOGS_DIR, project["name"])
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "output.log")

    runtime = RUNTIME_PYTHON if project["runtime"] == "python" else RUNTIME_NODE
    cmd = [runtime, main_file]

    try:
        with open(log_file, "a") as f:
            process = subprocess.Popen(
                cmd,
                cwd=project_dir,
                stdout=f,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                creationflags=getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0),
            )

        update_project_status(project_id, "running", process.pid)
        return True, f"Bot started with PID {process.pid}"

    except FileNotFoundError:
        return False, f"Runtime '{runtime}' not found. Install it first."
    except Exception as e:
        return False, str(e)


def stop_bot(project_id):
    project = get_project(project_id)
    if not project:
        return False, "Project not found"

    if project["status"] != "running":
        return False, "Bot is not running"

    pid = project["pid"]
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            child.kill()
        parent.kill()
        update_project_status(project_id, "stopped", 0)
        return True, "Bot stopped"
    except psutil.NoSuchProcess:
        update_project_status(project_id, "stopped", 0)
        return True, "Bot was not running (stale PID cleared)"
    except Exception as e:
        return False, str(e)


def restart_bot(project_id):
    stop_result, stop_msg = stop_bot(project_id)
    import time
    time.sleep(1)
    return start_bot(project_id)


def get_bot_status(project_id):
    project = get_project(project_id)
    if not project:
        return None

    pid = project["pid"]
    if pid and project["status"] == "running":
        try:
            p = psutil.Process(pid)
            if p.is_running():
                cpu = p.cpu_percent(interval=0.1)
                mem = p.memory_info().rss / 1024 / 1024
                return {
                    "status": "running",
                    "pid": pid,
                    "cpu": round(cpu, 1),
                    "memory_mb": round(mem, 2),
                    "uptime": datetime.fromtimestamp(p.create_time()).isoformat()
                }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

        update_project_status(project_id, "stopped", 0)
        return {"status": "stopped", "pid": 0, "cpu": 0, "memory_mb": 0}

    return {"status": "stopped", "pid": 0, "cpu": 0, "memory_mb": 0}


def cleanup_stale_processes():
    projects = get_all_projects_stale()
    for project in projects:
        if project["status"] == "running" and project["pid"]:
            try:
                p = psutil.Process(project["pid"])
                if not p.is_running():
                    update_project_status(project["id"], "stopped", 0)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                update_project_status(project["id"], "stopped", 0)


def get_all_projects_stale():
    from database import get_all_projects
    return get_all_projects()
