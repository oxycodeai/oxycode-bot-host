import os
import json
import psutil
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
from config import (
    APP_NAME, APP_VERSION, PORT, HOST, PROJECTS_DIR, LOGS_DIR,
    TELEGRAM_LINK, MAX_BOTS, ALLOWED_EDIT_EXT, ENV_FILE
)
from database import (
    create_project, get_all_projects, get_project, update_project,
    delete_project, get_setting, set_setting
)
from process_manager import start_bot, stop_bot, restart_bot, get_bot_status
from github_handler import clone_repo, detect_runtime, detect_dependencies
from auto_installer import auto_install

app = Flask(__name__)
app.secret_key = os.urandom(24)


@app.route("/")
def dashboard():
    projects = get_all_projects()
    for p in projects:
        status = get_bot_status(p["id"])
        p["status_info"] = status
    return render_template("dashboard.html", projects=projects, app_name=APP_NAME)


@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        repo_url = request.form.get("repo_url", "").strip()

        if not name:
            return render_template("create.html", error="Project name is required")

        if not all(c.isalnum() or c in "-_" for c in name):
            return render_template("create.html", error="Name can only contain letters, numbers, - and _")

        if len(get_all_projects()) >= MAX_BOTS:
            return render_template("create.html", error=f"Maximum {MAX_BOTS} bots reached")

        project_dir = os.path.join(PROJECTS_DIR, name)
        if os.path.exists(project_dir):
            return render_template("create.html", error="Project with this name already exists")

        if repo_url:
            success, msg = clone_repo(repo_url, name)
            if not success:
                return render_template("create.html", error=msg)

            runtime, main_file = detect_runtime(name)
            project_id = create_project(name, repo_url, runtime, main_file)

            deps = detect_dependencies(name)
            if deps[runtime]:
                auto_install(name, runtime)

            return redirect(url_for("dashboard"))
        else:
            os.makedirs(project_dir, exist_ok=True)
            main_file = "main.py"
            create_project(name, "", "python", main_file)

            with open(os.path.join(project_dir, main_file), "w") as f:
                f.write("# Your bot code here\n")

            with open(os.path.join(project_dir, "requirements.txt"), "w") as f:
                f.write("# Add your Python dependencies here\n")

            return redirect(url_for("dashboard"))

    return render_template("create.html")


@app.route("/bot/<int:project_id>/start", methods=["POST"])
def bot_start(project_id):
    success, msg = start_bot(project_id)
    return jsonify({"success": success, "message": msg})


@app.route("/bot/<int:project_id>/stop", methods=["POST"])
def bot_stop(project_id):
    success, msg = stop_bot(project_id)
    return jsonify({"success": success, "message": msg})


@app.route("/bot/<int:project_id>/restart", methods=["POST"])
def bot_restart(project_id):
    success, msg = restart_bot(project_id)
    return jsonify({"success": success, "message": msg})


@app.route("/bot/<int:project_id>/status")
def bot_status(project_id):
    status = get_bot_status(project_id)
    if status is None:
        return jsonify({"error": "Project not found"}), 404
    return jsonify(status)


@app.route("/bot/<int:project_id>/delete", methods=["POST"])
def bot_delete(project_id):
    project = get_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    if project["status"] == "running":
        stop_bot(project_id)

    project_dir = os.path.join(PROJECTS_DIR, project["name"])
    if os.path.exists(project_dir):
        import shutil
        shutil.rmtree(project_dir, ignore_errors=True)

    log_dir = os.path.join(LOGS_DIR, project["name"])
    if os.path.exists(log_dir):
        import shutil
        shutil.rmtree(log_dir, ignore_errors=True)

    delete_project(project_id)
    return jsonify({"success": True, "message": "Project deleted"})


@app.route("/bot/<int:project_id>/edit", methods=["GET", "POST"])
def bot_edit(project_id):
    project = get_project(project_id)
    if not project:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        main_file = request.form.get("main_file", "").strip()
        if name and main_file:
            update_project(project_id, name=name, main_file=main_file)
        return redirect(url_for("dashboard"))

    return render_template("create.html", project=project, editing=True)


@app.route("/editor/<int:project_id>")
@app.route("/editor/<int:project_id>/<path:filepath>")
def editor(project_id, filepath=None):
    project = get_project(project_id)
    if not project:
        return redirect(url_for("dashboard"))

    project_dir = os.path.join(PROJECTS_DIR, project["name"])
    if not os.path.exists(project_dir):
        os.makedirs(project_dir, exist_ok=True)

    files = []
    for root, dirs, filenames in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in ("node_modules", "__pycache__", ".git", "venv")]
        level = root.replace(project_dir, "").count(os.sep)
        if level > 3:
            continue
        for fn in sorted(filenames):
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, project_dir)
            ext = os.path.splitext(fn)[1].lower()
            if ext in ALLOWED_EDIT_EXT:
                files.append({"path": rel, "name": fn})

    content = ""
    current_file = filepath
    if filepath:
        file_path = os.path.join(project_dir, filepath)
        if os.path.isfile(file_path):
            try:
                with open(file_path, "r", errors="replace") as f:
                    content = f.read()
            except:
                content = ""

    return render_template("editor.html", project=project, files=files,
                           current_file=current_file, content=content)


@app.route("/api/editor/save", methods=["POST"])
def save_file():
    data = request.json
    project_id = data.get("project_id")
    filepath = data.get("filepath")
    content = data.get("content")

    project = get_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    file_path = os.path.join(PROJECTS_DIR, project["name"], filepath)
    project_dir = os.path.join(PROJECTS_DIR, project["name"])

    if not os.path.abspath(file_path).startswith(os.path.abspath(project_dir)):
        return jsonify({"error": "Invalid path"}), 400

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        f.write(content)

    return jsonify({"success": True})


@app.route("/api/editor/read", methods=["POST"])
def read_file():
    data = request.json
    project_id = data.get("project_id")
    filepath = data.get("filepath")

    project = get_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    file_path = os.path.join(PROJECTS_DIR, project["name"], filepath)
    project_dir = os.path.join(PROJECTS_DIR, project["name"])

    if not os.path.abspath(file_path).startswith(os.path.abspath(project_dir)):
        return jsonify({"error": "Invalid path"}), 400

    if not os.path.isfile(file_path):
        return jsonify({"error": "File not found"}), 404

    try:
        with open(file_path, "r", errors="replace") as f:
            content = f.read()
        return jsonify({"content": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/logs/<int:project_id>")
def logs(project_id):
    project = get_project(project_id)
    if not project:
        return redirect(url_for("dashboard"))
    return render_template("logs.html", project=project)


@app.route("/api/logs/<int:project_id>")
def get_logs(project_id):
    project = get_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    log_file = os.path.join(LOGS_DIR, project["name"], "output.log")
    lines = int(request.args.get("lines", 200))

    if not os.path.exists(log_file):
        return jsonify({"logs": ""})

    try:
        with open(log_file, "r", errors="replace") as f:
            all_lines = f.readlines()
            recent = all_lines[-lines:]
            return jsonify({"logs": "".join(recent)})
    except:
        return jsonify({"logs": ""})


@app.route("/api/logs/<int:project_id>/clear", methods=["POST"])
def clear_logs(project_id):
    project = get_project(project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    log_file = os.path.join(LOGS_DIR, project["name"], "output.log")
    if os.path.exists(log_file):
        with open(log_file, "w") as f:
            f.write("")

    return jsonify({"success": True})


@app.route("/env/<int:project_id>", methods=["GET", "POST"])
def env_editor(project_id):
    project = get_project(project_id)
    if not project:
        return redirect(url_for("dashboard"))

    project_dir = os.path.join(PROJECTS_DIR, project["name"])
    env_path = os.path.join(project_dir, ENV_FILE)

    if request.method == "POST":
        content = request.form.get("content", "")
        with open(env_path, "w") as f:
            f.write(content)
        return redirect(url_for("env_editor", project_id=project_id))

    content = ""
    if os.path.exists(env_path):
        with open(env_path, "r", errors="replace") as f:
            content = f.read()

    return render_template("env_editor.html", project=project, content=content)


@app.route("/api/stats")
def system_stats():
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    projects = get_all_projects()
    running = sum(1 for p in projects if p["status"] == "running")

    return jsonify({
        "cpu_percent": cpu,
        "memory_percent": mem.percent,
        "memory_used_mb": round(mem.used / 1024 / 1024),
        "memory_total_mb": round(mem.total / 1024 / 1024),
        "disk_percent": disk.percent,
        "disk_used_gb": round(disk.used / 1024 / 1024 / 1024, 1),
        "disk_total_gb": round(disk.total / 1024 / 1024 / 1024, 1),
        "total_projects": len(projects),
        "running_bots": running
    })


if __name__ == "__main__":
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    print(f"\n  {APP_NAME} v{APP_VERSION}")
    print(f"  http://{HOST}:{PORT}\n")
    app.run(host=HOST, port=PORT, debug=False)
