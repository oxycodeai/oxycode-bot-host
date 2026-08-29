import subprocess
import os
from config import PROJECTS_DIR


def install_python_deps(project_name):
    project_dir = os.path.join(PROJECTS_DIR, project_name)
    req_path = os.path.join(project_dir, "requirements.txt")

    if not os.path.exists(req_path):
        return True, "No requirements.txt found, skipping"

    try:
        result = subprocess.run(
            ["pip", "install", "-r", "requirements.txt"],
            cwd=project_dir,
            capture_output=True, text=True, timeout=300
        )
        if result.returncode != 0:
            return False, f"pip install failed: {result.stderr[-500:]}"
        return True, "Python dependencies installed"

    except subprocess.TimeoutExpired:
        return False, "Installation timed out (5min limit)"
    except Exception as e:
        return False, str(e)


def install_node_deps(project_name):
    project_dir = os.path.join(PROJECTS_DIR, project_name)
    pkg_path = os.path.join(project_dir, "package.json")

    if not os.path.exists(pkg_path):
        return True, "No package.json found, skipping"

    try:
        npm = "npm"
        result = subprocess.run(
            [npm, "install", "--production"],
            cwd=project_dir,
            capture_output=True, text=True, timeout=300
        )
        if result.returncode != 0:
            return False, f"npm install failed: {result.stderr[-500:]}"
        return True, "Node dependencies installed"

    except FileNotFoundError:
        return False, "npm not found. Install Node.js: pkg install nodejs"
    except subprocess.TimeoutExpired:
        return False, "Installation timed out (5min limit)"
    except Exception as e:
        return False, str(e)


def auto_install(project_name, runtime):
    if runtime == "node":
        return install_node_deps(project_name)
    return install_python_deps(project_name)
