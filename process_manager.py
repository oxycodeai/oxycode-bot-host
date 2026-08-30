import subprocess
import os
import signal
import threading
import time
import logging
from datetime import datetime
from config import PROJECTS_DIR, LOGS_DIR, RUNTIME_PYTHON, RUNTIME_NODE, ENV_FILE, MAX_CONCURRENT_BOTS, MAX_LOG_SIZE_KB
from database import update_project_status, get_project, get_all_projects

logger = logging.getLogger(__name__)

running_processes = {}
_log_locks = {}
_restart_counts = {}
MAX_RESTARTS = 3
RESTART_DELAY = 2


def _pid_exists(pid):
    if not pid or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False
    except PermissionError:
        return True


def _kill_pid(pid):
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(0.5)
        if _pid_exists(pid):
            os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except PermissionError:
        try:
            subprocess.run(["kill", "-9", str(pid)], capture_output=True, timeout=5)
        except:
            pass


def _get_child_pids(pid):
    children = []
    try:
        result = subprocess.run(
            ["pgrep", "-P", str(pid)],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if line and line.isdigit():
                children.append(int(line))
    except:
        pass
    return children


def _get_process_stats(pid):
    """Get CPU and memory for a process. Returns (cpu_percent, memory_mb)."""
    cpu = 0.0
    mem_mb = 0.0

    # Try psutil first (cross-platform)
    try:
        import psutil
        proc = psutil.Process(pid)
        cpu = proc.cpu_percent(interval=0.1)
        mem_mb = proc.memory_info().rss / (1024 * 1024)
        return round(cpu, 1), round(mem_mb, 2)
    except ImportError:
        pass
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return 0.0, 0.0

    # Fallback: /proc on Linux
    try:
        with open(f"/proc/{pid}/stat") as f:
            parts = f.read().split()
            utime = int(parts[13])
            stime = int(parts[14])
            total_ticks = utime + stime
            uptime = 0.0
            with open("/proc/uptime") as f2:
                uptime = float(f2.read().split()[0])
            clk_tck = os.sysconf("SC_CLK_TCK")
            total_time = total_ticks / clk_tck
            seconds = max(uptime - total_time / os.cpu_count() or 1, 0.1)
            cpu = round((total_time / max(seconds, 0.1)) * 100, 1) if seconds > 0 else 0.0
    except:
        pass

    try:
        with open(f"/proc/{pid}/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    mem_mb = int(line.split()[1]) / 1024
                    break
    except:
        pass

    return cpu, round(mem_mb, 2)


def _load_env_file(project_dir):
    env_path = os.path.join(project_dir, ENV_FILE)
    env_vars = dict(os.environ)
    env_vars["PYTHONUNBUFFERED"] = "1"
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
                try:
                    line = process.stdout.readline()
                    if line:
                        log_f.write(line)
                        log_f.flush()
                    else:
                        time.sleep(0.05)
                except:
                    break
            _rotate_log(log_file)
    except:
        pass

    try:
        remaining = process.stdout.read()
        if remaining:
            with open(log_file, "a") as log_f:
                log_f.write(remaining.decode("utf-8", errors="replace"))
                log_f.flush()
    except:
        pass

    return_code = process.poll()

    # Immediately update status based on exit code
    if return_code is not None and return_code != 0:
        logger.warning(f"Bot {project_name} (PID {process.pid}) crashed with exit code {return_code}")
        update_project_status(project_id, "error")

        # Auto-restart on crash
        restart_count = _restart_counts.get(project_id, 0)
        if restart_count < MAX_RESTARTS:
            _restart_counts[project_id] = restart_count + 1
            logger.info(f"Auto-restarting bot {project_name} (attempt {restart_count + 1}/{MAX_RESTARTS})")
            time.sleep(RESTART_DELAY)
            success, msg = start_bot(project_id)
            if success:
                logger.info(f"Bot {project_name} restarted successfully")
            else:
                logger.error(f"Failed to restart bot {project_name}: {msg}")
        else:
            logger.error(f"Bot {project_name} exceeded max restarts ({MAX_RESTARTS}), not restarting")
            _restart_counts.pop(project_id, None)
    else:
        _restart_counts.pop(project_id, None)
        update_project_status(project_id, "stopped")

    running_processes.pop(project_id, None)


def start_bot(project_id):
    project = get_project(project_id)
    if not project:
        return False, "Project not found"

    # Verify PID is actually alive before saying "already running"
    if project["status"] == "running" and _pid_exists(project.get("pid", 0)):
        return False, "Bot is already running"

    # If status says running but PID is dead, fix the status first
    if project["status"] == "running" and not _pid_exists(project.get("pid", 0)):
        update_project_status(project_id, "stopped", 0)

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

    try:
        with open(log_file, "a") as log_f:
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
        _restart_counts.pop(project_id, None)
        update_project_status(project_id, "running", process.pid)

        thread = threading.Thread(
            target=_capture_output,
            args=(process, project_id, project["name"]),
            daemon=True
        )
        thread.start()

        # Quick check: did the process crash immediately?
        time.sleep(0.3)
        if process.poll() is not None:
            exit_code = process.poll()
            update_project_status(project_id, "error")
            running_processes.pop(project_id, None)
            error_msg = f"Bot crashed immediately with exit code {exit_code}"
            try:
                with open(log_file, "r") as f:
                    last_lines = f.readlines()[-5:]
                    if last_lines:
                        error_msg = "".join(last_lines).strip()
            except:
                pass
            return False, error_msg

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
        # Force clean stale status
        if project["pid"] and _pid_exists(project["pid"]):
            _kill_pid(project["pid"])
        update_project_status(project_id, "stopped", 0)
        return True, "Bot was not running"

    pid = project.get("pid", 0)
    if not pid or not _pid_exists(pid):
        update_project_status(project_id, "stopped", 0)
        return True, "Bot was not running (stale PID cleared)"

    try:
        # Kill children first
        for child in _get_child_pids(pid):
            _kill_pid(child)
        # Kill the main process
        _kill_pid(pid)
        running_processes.pop(project_id, None)
        _restart_counts.pop(project_id, None)
        update_project_status(project_id, "stopped", 0)
        return True, "Bot stopped"
    except Exception as e:
        return False, str(e)


def restart_bot(project_id):
    success, msg = stop_bot(project_id)
    if not success:
        return False, msg

    # Wait for process to actually die
    project = get_project(project_id)
    if project and project.get("pid"):
        for _ in range(10):
            if not _pid_exists(project["pid"]):
                break
            time.sleep(0.2)

    time.sleep(0.5)
    return start_bot(project_id)


def get_bot_status(project_id):
    project = get_project(project_id)
    if not project:
        return None

    pid = project.get("pid", 0)
    status = project["status"]

    if status == "running" and pid:
        if _pid_exists(pid):
            cpu, mem_mb = _get_process_stats(pid)
            return {
                "status": "running",
                "pid": pid,
                "cpu": cpu,
                "memory_mb": mem_mb,
            }
        else:
            # PID is dead but status says running - fix it
            update_project_status(project_id, "stopped", 0)
            return {"status": "stopped", "pid": 0, "cpu": 0, "memory_mb": 0}

    return {"status": status, "pid": 0, "cpu": 0, "memory_mb": 0}


def cleanup_stale_processes():
    projects = get_all_projects()
    for project in projects:
        if project["status"] == "running" and project.get("pid"):
            if not _pid_exists(project["pid"]):
                logger.info(f"Cleaning stale PID {project['pid']} for bot {project['name']}")
                update_project_status(project["id"], "stopped", 0)
