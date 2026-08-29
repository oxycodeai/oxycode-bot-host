import subprocess
import os
import signal
import threading
import time
from datetime import datetime
from config import PROJECTS_DIR, LOGS_DIR, RUNTIME_PYTHON, RUNTIME_NODE, ENV_FILE, MAX_CONCURRENT_BOTS, MAX_LOG_SIZE_KB
from database import update_project_status, get_project, get_all_projects

running_processes = {}
_log_locks = {}


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


def _load_env_file(project_dir):
    env_path = os.path.join(project_dir, ENV_FILE)
    env_vars = dict(os.environ)
    if os.path.exists(env_path):
        try:
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, _, value = line.partition("=")
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        env_vars[key] = value
        except:
            pass
    return env_vars


def _rotate_log(log_file):
    try:
        if os.path.exists(log_file):
            size_kb = os.path.getsize(log_file) / 1024
            if size_kb > MAX_LOG_SIZE_KB:
                with open(log_file, "r") as f:
                    lines = f.readlines()
                keep = lines[-500:]
                with open(log_file, "w") as f:
                    f.writelines(keep)
    except:
        pass


def _capture_output(process, project_id, project_name):
    log_dir = os.path.join(LOGS_DIR, project_name)
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "output.log")

    try:
        with open(log_file, "a") as log_f:
            while process.poll() is None:
                line = process.stdout.readline()
                if line:
                    log_f.write(line)
                    log_f.flush()
                    _rotate_log(log_file)
                else:
                    time.sleep(0.1)
    except:
        pass

    try:
        remaining = process.stdout.read()
        if remaining:
            with open(log_file, "a") as log_f:
                log_f.write(remaining)
                log_f.flush()
    except:
        pass

    return_code = process.poll()
    if return_code and return_code != 0:
        update_project_status(project_id, "error")
    else:
        update_project_status(project_id, "stopped")

    running_processes.pop(project_id, None)


def start_bot(project_id):
    project = get_project(project_id)
    if not project:
        return False, "Project not found"

    if project["status"] == "running" and _pid_exists(project["pid"]):
        return False, "Bot is already running"

    running_count = sum(1 for p in get_all_projects() if p["status"] == "running")
    if running_count >= MAX_CONCURRENT_BOTS:
        return False, f"Maximum {MAX_CONCURRENT_BOTS} concurrent bots reached"

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
    _rotate_log(log_file)

    runtime = RUNTIME_PYTHON if project["runtime"] == "python" else RUNTIME_NODE
    cmd = [runtime, main_file]

    env_vars = _load_env_file(project_dir)
    if project["runtime"] == "python":
        env_vars["PYTHONUNBUFFERED"] = "1"
    env_vars["NODE_ENV"] = "production"

    try:
        with open(log_file, "a") as f:
            process = subprocess.Popen(
                cmd,
                cwd=project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
                env=env_vars,
                bufsize=1,
            )

        running_processes[project_id] = process
        update_project_status(project_id, "running", process.pid)

        thread = threading.Thread(
            target=_capture_output,
            args=(process, project_id, project["name"]),
            daemon=True
        )
        thread.start()

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
        running_processes.pop(project_id, None)
        update_project_status(project_id, "stopped", 0)
        return True, "Bot stopped"
    except Exception as e:
        return False, str(e)


def restart_bot(project_id):
    stop_bot(project_id)
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
