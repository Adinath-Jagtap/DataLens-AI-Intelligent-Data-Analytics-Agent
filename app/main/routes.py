import os
import tempfile
import math
from flask import (Blueprint, render_template, redirect, url_for,
                   request, flash, current_app, make_response)
from flask_login import login_required, current_user
from app.models import (
    create_analysis, get_analysis, update_analysis,
    get_user_analyses, delete_analysis, append_chat_message,
    get_all_users, get_all_analyses_admin, get_user_by_id,
    delete_user_and_data, increment_analysis_count,
)
from app.services.data_service import parse_and_analyse
from app.services.ai_service import analyse_dataset, chat_with_data

main_bp = Blueprint("main", __name__)

ALLOWED = {".csv", ".xls", ".xlsx"}


@main_bp.route("/")
def landing():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    return render_template("landing.html")


@main_bp.route("/home")
@login_required
def home():
    analyses = get_user_analyses(current_user.id)
    return render_template("main/home.html", analyses=analyses[:5])


# ── Upload ────────────────────────────────────────────────────────────────────

@main_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "GET":
        return render_template("main/upload.html")

    file = request.files.get("dataset")
    if not file or not file.filename:
        flash("Please select a file.", "error")
        return render_template("main/upload.html")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED:
        flash("Only CSV and Excel (.xls, .xlsx) files are supported.", "error")
        return render_template("main/upload.html")

    max_bytes = current_app.config["MAX_UPLOAD_MB"] * 1024 * 1024
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > max_bytes:
        flash(f"File too large. Max {current_app.config['MAX_UPLOAD_MB']} MB.", "error")
        return render_template("main/upload.html")

    # Create placeholder
    analysis_id = create_analysis(current_user.id, file.filename, size)

    # Save temp file
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    file.save(tmp.name)
    tmp.close()

    try:
        summary, cleaned_rows, charts_b64 = parse_and_analyse(tmp.name, file.filename)
    except Exception as e:
        update_analysis(analysis_id, {"status": "error", "error_msg": str(e)})
        flash(f"Failed to process file: {e}", "error")
        return redirect(url_for("main.upload"))
    finally:
        os.unlink(tmp.name)

    # AI analysis
    ai_result = analyse_dataset(summary)

    update_analysis(analysis_id, {
        "status":       "done",
        "summary":      summary,
        "ai_result":    ai_result,
        "charts_b64":   charts_b64,
        "cleaned_rows": cleaned_rows,
    })
    increment_analysis_count(current_user.id)

    flash("Analysis complete!", "success")
    return redirect(url_for("main.analysis", analysis_id=analysis_id))


# ── Analysis ──────────────────────────────────────────────────────────────────

@main_bp.route("/analysis/<analysis_id>")
@login_required
def analysis(analysis_id):
    doc = get_analysis(analysis_id, current_user.id)
    if not doc:
        flash("Analysis not found.", "error")
        return redirect(url_for("main.history"))

    page     = request.args.get("page", 1, type=int)
    per_page = 50
    rows     = doc.get("cleaned_rows", [])
    total_pages = max(1, math.ceil(len(rows) / per_page))
    page     = max(1, min(page, total_pages))
    rows_slice = rows[(page - 1) * per_page: page * per_page]

    return render_template("main/analysis.html",
        doc=doc,
        summary=doc.get("summary", {}),
        ai_result=doc.get("ai_result", {}),
        charts_b64=doc.get("charts_b64", {}),
        rows=rows_slice,
        page=page,
        total_pages=total_pages,
        total_rows=len(rows),
    )


# ── Chat ──────────────────────────────────────────────────────────────────────

@main_bp.route("/analysis/<analysis_id>/chat", methods=["GET", "POST"])
@login_required
def chat(analysis_id):
    doc = get_analysis(analysis_id, current_user.id)
    if not doc:
        flash("Analysis not found.", "error")
        return redirect(url_for("main.history"))

    if request.method == "POST":
        message = request.form.get("message", "").strip()
        if message:
            append_chat_message(analysis_id, "user", message)
            response = chat_with_data(
                doc.get("summary", {}),
                doc.get("chat_history", []),
                message,
            )
            append_chat_message(analysis_id, "assistant", response)
        return redirect(url_for("main.chat", analysis_id=analysis_id))

    doc = get_analysis(analysis_id, current_user.id)
    return render_template("main/chat.html", doc=doc)


# ── Export CSV ────────────────────────────────────────────────────────────────

@main_bp.route("/analysis/<analysis_id>/export")
@login_required
def export_csv(analysis_id):
    doc = get_analysis(analysis_id, current_user.id)
    if not doc:
        flash("Analysis not found.", "error")
        return redirect(url_for("main.history"))

    rows = doc.get("cleaned_rows", [])
    if not rows:
        flash("No data to export.", "error")
        return redirect(url_for("main.analysis", analysis_id=analysis_id))

    cols = list(rows[0].keys())
    lines = [",".join(cols)]
    for row in rows:
        lines.append(",".join(
            f'"{str(row.get(c, "")).replace(chr(34), chr(39))}"' for c in cols
        ))
    csv_data = "\n".join(lines)

    safe_name = doc.get("file_name", "export").rsplit(".", 1)[0]
    resp = make_response(csv_data)
    resp.headers["Content-Type"] = "text/csv"
    resp.headers["Content-Disposition"] = f'attachment; filename="{safe_name}_cleaned.csv"'
    return resp


# ── History ───────────────────────────────────────────────────────────────────

@main_bp.route("/history")
@login_required
def history():
    analyses = get_user_analyses(current_user.id)
    return render_template("main/history.html", analyses=analyses)


@main_bp.route("/analysis/<analysis_id>/delete", methods=["POST"])
@login_required
def delete(analysis_id):
    delete_analysis(analysis_id, current_user.id)
    flash("Analysis deleted.", "success")
    return redirect(url_for("main.history"))


# ── Profile ───────────────────────────────────────────────────────────────────

@main_bp.route("/profile")
@login_required
def profile():
    analyses  = get_user_analyses(current_user.id)
    total_charts = sum(len(a.get("charts_b64", {})) for a in analyses)
    total_chats  = sum(len(a.get("chat_history", [])) for a in analyses)
    return render_template("main/profile.html",
        analyses=analyses,
        total_charts=total_charts,
        total_chats=total_chats,
    )


# ── Admin ─────────────────────────────────────────────────────────────────────

@main_bp.route("/admin")
@login_required
def admin():
    if not current_user.is_admin:
        flash("Access denied.", "error")
        return redirect(url_for("main.home"))
    users    = get_all_users()
    analyses = get_all_analyses_admin()
    return render_template("main/admin.html", users=users, analyses=analyses)


@main_bp.route("/admin/delete-user/<user_id>", methods=["POST"])
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin:
        flash("Access denied.", "error")
        return redirect(url_for("main.home"))
    delete_user_and_data(user_id)
    flash("User deleted.", "success")
    return redirect(url_for("main.admin"))
