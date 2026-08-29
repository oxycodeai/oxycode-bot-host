import subprocess
import os
import signal
from datetime import datetime
from config import PROJECTS_DIR, LOGS_DIR, RUNTIME_PYTHON, RUNTIME_NODE
from database import update_project_status, get_project, get_all_projects


def _pid_exists(pid):
    return os.path.isdir(f"/proc/{pid}")


def _kill_pid(pid):
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except PermissionError:
        try:
            subprocess.run(["kill", "-9", str(pid)], capture_output=True)
        except:
            pass


def _get_child_pids(pid):
    children = []
    try:
        result = subprocess.run(
            ["pgrep", "-P", str(pid)],
            capture_output=True, text=True
        )
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                children.append(int(line.strip()))
    except:
        pass
    return children


def _get_process_memory_kb(pid):
    try:
        with open(f"/proc/{pid}/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1])
    except:
        pass
    return 0


def start_bot(project_id):
    project = get_project(project_id)
    if not project:
        return False, "Project not found"

    if project["status"] == "running" and _pid_exists(project["pid"]):
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
                start_new_session=True,
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
    if not _pid_exists(pid):
        update_project_status(project_id, "stopped", 0)
        return True, "Bot was not running (stale PID cleared)"

    try:
        for child in _get_child_pids(pid):
            _kill_pid(child)
        _kill_pid(pid)
        update_project_status(project_id, "stopped", 0)
        return True, "Bot stopped"
    except Exception as e:
        return False, str(e)


def restart_bot(project_id):
    stop_bot(project_id)
    import time
    time.sleep(1)
    return start_bot(project_id)


def get_bot_status(project_id):
    project = get_project(project_id)
    if not project:
        return None

    pid = project["pid"]
    if pid and project["status"] == "running":
        if _pid_exists(pid):
            mem_kb = _get_process_memory_kb(pid)
            return {
                "status": "running",
                "pid": pid,
                "cpu": 0,
                "memory_mb": round(mem_kb / 1024, 2),
            }
        else:
            update_project_status(project_id, "stopped", 0)
            return {"status": "stopped", "pid": 0, "cpu": 0, "memory_mb": 0}

    return {"status": "stopped", "pid": 0, "cpu": 0, "memory_mb": 0}


def cleanup_stale_processes():
    projects = get_all_projects()
    for project in projects:
        if project["status"] == "running" and project["pid"]:
            if not _pid_exists(project["pid"]):
                update_project_status(project["id"], "stopped", 0)
