import subprocess
import os
import re
import shutil
from urllib.parse import urlparse
from config import PROJECTS_DIR, CLONE_TIMEOUT

ALLOWED_GIT_HOSTS = {"github.com"}
BLOCKED_SCHEMES = {"file", "ssh", "ftp", "ftps"}


def validate_git_url(url):
    if not url or not url.strip():
        return False, "URL is required"
    url = url.strip()
    if any(url.lower().startswith(s + "://") for s in BLOCKED_SCHEMES):
        return False, f"URL scheme not allowed"
    if url.startswith("git@github.com:"):
        return True, "OK"
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https", ""):
        return False, "Only HTTPS URLs are supported"
    if parsed.hostname and parsed.hostname not in ALLOWED_GIT_HOSTS:
        return False, f"Only {', '.join(ALLOWED_GIT_HOSTS)} repositories are supported"
    if not parsed.hostname and not url.startswith("git@"):
        return False, "Invalid URL format"
    return True, "OK"


def clone_repo(url, project_name):
    project_dir = os.path.join(PROJECTS_DIR, project_name)
    if os.path.exists(project_dir):
        shutil.rmtree(project_dir)

    valid, msg = validate_git_url(url)
    if not valid:
        return False, msg

    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", url, project_dir],
            capture_output=True, text=True, timeout=CLONE_TIMEOUT
        )
        if result.returncode != 0:
            return False, f"Clone failed: {result.stderr.strip()}"

        shutil.rmtree(os.path.join(project_dir, ".git"), ignore_errors=True)
        return True, "Repository cloned successfully"

    except subprocess.TimeoutExpired:
        return False, "Clone timed out (120s limit)"
    except FileNotFoundError:
        return False, "Git is not installed. Run: pkg install git"
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
        main_file = "index.js" if has_index_js else find_main_node(project_dir)
        return "node", main_file

    if has_requirements or has_main_py or has_bot_py or has_app_py:
        main_file = "main.py" if has_main_py else find_main_python(project_dir)
        return "python", main_file

    if has_package_json:
        main_file = "index.js" if has_index_js else find_main_node(project_dir)
        return "node", main_file

    return "python", "main.py"


def find_main_python(project_dir):
    candidates = ["main.py", "bot.py", "app.py", "run.py", "start.py"]
    for c in candidates:
        if os.path.exists(os.path.join(project_dir, c)):
            return c

    py_files = [f for f in os.listdir(project_dir) if f.endswith(".py")]
    if py_files:
        for f in py_files:
            path = os.path.join(project_dir, f)
            try:
                with open(path, "r", errors="ignore") as fh:
                    content = fh.read(2000)
                    if "__main__" in content or "bot.run" in content or "app.run" in content:
                        return f
            except:
                pass
        return py_files[0]

    return "main.py"


def find_main_node(project_dir):
    candidates = ["index.js", "bot.js", "app.js", "main.js", "start.js"]
    for c in candidates:
        if os.path.exists(os.path.join(project_dir, c)):
            return c

    pkg_path = os.path.join(project_dir, "package.json")
    if os.path.exists(pkg_path):
        try:
            import json
            with open(pkg_path) as f:
                pkg = json.load(f)
                if "main" in pkg:
                    return pkg["main"]
        except:
            pass

    js_files = [f for f in os.listdir(project_dir) if f.endswith(".js")]
    if js_files:
        return js_files[0]

    return "index.js"


def detect_dependencies(project_name):
    project_dir = os.path.join(PROJECTS_DIR, project_name)
    deps = {"python": [], "node": []}

    req_path = os.path.join(project_dir, "requirements.txt")
    if os.path.exists(req_path):
        with open(req_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    pkg = re.split(r"[>=<!\[]", line)[0].strip()
                    if pkg:
                        deps["python"].append(pkg)

    pkg_path = os.path.join(project_dir, "package.json")
    if os.path.exists(pkg_path):
        try:
            import json
            with open(pkg_path) as f:
                pkg = json.load(f)
                for dep_type in ["dependencies", "devDependencies"]:
                    if dep_type in pkg:
                        deps["node"].extend(list(pkg[dep_type].keys()))
        except:
            pass

    return deps
