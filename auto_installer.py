import subprocess
import os
import json
from config import PROJECTS_DIR, RUNTIME_PYTHON, RUNTIME_NODE


def auto_install(project_name):
    project_dir = os.path.join(PROJECTS_DIR, project_name)
    if not os.path.isdir(project_dir):
        return False, "Project directory not found"

    has_requirements = os.path.exists(os.path.join(project_dir, "requirements.txt"))
    has_package_json = os.path.exists(os.path.join(project_dir, "package.json"))

    if has_requirements:
        return _install_python(project_dir)
    elif has_package_json:
        return _install_node(project_dir)

    return True, "No dependencies to install"


def _install_python(project_dir):
    req_path = os.path.join(project_dir, "requirements.txt")
    libs_dir = os.path.join(project_dir, "libs")

    with open(req_path) as f:
        content = f.read().strip()
    if not content or all(l.startswith("#") or not l.strip() for l in content.split("\n")):
        return True, "No Python dependencies to install"

    try:
        os.makedirs(libs_dir, exist_ok=True)
        result = subprocess.run(
            [RUNTIME_PYTHON, "-m", "pip", "install", "-r", req_path,
             "--target", libs_dir, "--quiet", "--disable-pip-version-check"],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode != 0:
            return False, f"Pip install failed: {result.stderr[:500]}"
        return True, "Python dependencies installed"
    except subprocess.TimeoutExpired:
        return False, "Install timed out (5 min limit)"
    except FileNotFoundError:
        return False, "Python/pip not found. Run: pkg install python"
    except Exception as e:
        return False, str(e)


def _install_node(project_dir):
    try:
        result = subprocess.run(
            ["npm", "install", "--production", "--quiet"],
            cwd=project_dir,
            capture_output=True, text=True, timeout=300
        )
        if result.returncode != 0:
            return False, f"npm install failed: {result.stderr[:500]}"
        return True, "Node dependencies installed"
    except subprocess.TimeoutExpired:
        return False, "Install timed out (5 min limit)"
    except FileNotFoundError:
        return False, "Node/npm not found. Run: pkg install nodejs"
    except Exception as e:
        return False, str(e)


def detect_runtime(project_name):
    project_dir = os.path.join(PROJECTS_DIR, project_name)
    if not os.path.isdir(project_dir):
        return "python", "main.py"

    has_package_json = os.path.exists(os.path.join(project_dir, "package.json"))
    has_requirements = os.path.exists(os.path.join(project_dir, "requirements.txt"))
    has_main_py = os.path.exists(os.path.join(project_dir, "main.py"))
    has_index_js = os.path.exists(os.path.join(project_dir, "index.js"))
    has_bot_py = os.path.exists(os.path.join(project_dir, "bot.py"))
    has_app_py = os.path.exists(os.path.join(project_dir, "app.py"))

    if has_package_json and not has_requirements:
        main_file = "index.js" if has_index_js else "main.js"
        return "node", main_file

    if has_requirements or has_main_py or has_bot_py or has_app_py:
        main_file = "main.py" if has_main_py else "main.py"
        return "python", main_file

    if has_package_json:
        main_file = "index.js" if has_index_js else "main.js"
        return "node", main_file

    return "python", "main.py"
