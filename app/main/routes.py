import os
import tempfile
import math
from datetime import datetime, timezone
from flask import (Blueprint, render_template, redirect, url_for,
                   request, flash, current_app, make_response, session,
                   stream_with_context, Response, json as flask_json)
from flask_login import login_required, current_user
from app.models import (
    create_analysis, get_analysis, update_analysis,
    get_user_analyses, delete_analysis, append_chat_message,
    get_all_users, get_all_analyses_admin, get_user_by_id,
    delete_user_and_data, increment_analysis_count,
    enable_sharing, disable_sharing, get_analysis_by_token
)
import bcrypt
from app.services.data_service import parse_and_analyse
from app.services.ai_service import (
    analyse_dataset, chat_with_data, chat_with_data_stream,
    generate_suggested_questions, extract_code_blocks
)
from app.services.code_executor import build_dataframe, execute_code
from app.services.export_service import export_excel, export_json, export_parquet, export_pdf
from app.services.profile_service import generate_profile
from app.services.dashboard_service import build_dashboard, generate_pbix, detect_dashboard_columns
import pandas as pd
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
        summary, cleaned_rows, chart_configs, charts_b64 = parse_and_analyse(tmp.name, file.filename)
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
        "chart_configs": chart_configs,
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

    summary = doc.get("summary", {})
    total_anomalies = sum(len(c.get("anomalies", [])) for c in summary.get("columns", []))

    return render_template("main/analysis.html",
        doc=doc,
        summary=summary,
        ai_result=doc.get("ai_result", {}),
        chart_configs=doc.get("chart_configs", {}),
        rows=rows_slice,
        page=page,
        total_pages=total_pages,
        total_rows=len(rows),
        total_anomalies=total_anomalies,
    )

@main_bp.route("/analysis/<analysis_id>/profile")
@login_required
def data_profile(analysis_id):
    doc = get_analysis(analysis_id, current_user.id)
    if not doc:
        flash("Analysis not found.", "error")
        return redirect(url_for("main.history"))

    rows = doc.get("cleaned_rows", [])
    if not rows:
        flash("No data available for profiling.", "error")
        return redirect(url_for("main.analysis", analysis_id=analysis_id))

    if len(rows) > current_app.config["PROFILE_MAX_ROWS"]:
        flash(f"Dataset has {len(rows)} rows. Profiling is limited to {current_app.config['PROFILE_MAX_ROWS']} rows for performance. Showing a random sample.", "success")
        import random
        rows = random.sample(rows, current_app.config["PROFILE_MAX_ROWS"])

    minimal = len(rows) > 5000

    try:
        html_report = generate_profile(rows, doc.get("file_name", "dataset"), minimal=minimal)
    except MemoryError:
        flash("Dataset too large to profile. Try exporting and profiling locally.", "error")
        return redirect(url_for("main.analysis", analysis_id=analysis_id))
    except Exception as e:
        flash(f"Profiling failed: {str(e)[:120]}", "error")
        return redirect(url_for("main.analysis", analysis_id=analysis_id))

    return render_template(
        "main/profile_report.html",
        doc=doc,
        html_report=html_report,
        minimal=minimal,
        analysis_id=analysis_id,
    )

@main_bp.route("/analysis/<analysis_id>/profile/download")
@login_required
def download_profile(analysis_id):
    doc = get_analysis(analysis_id, current_user.id)
    if not doc:
        flash("Analysis not found.", "error")
        return redirect(url_for("main.history"))

    rows = doc.get("cleaned_rows", [])
    if not rows:
        flash("No data available.", "error")
        return redirect(url_for("main.analysis", analysis_id=analysis_id))

    if len(rows) > current_app.config["PROFILE_MAX_ROWS"]:
        import random
        rows = random.sample(rows, current_app.config["PROFILE_MAX_ROWS"])

    minimal = len(rows) > 5000

    try:
        html_report = generate_profile(rows, doc.get("file_name", "dataset"), minimal=minimal)
    except Exception as e:
        flash(f"Profiling failed: {str(e)[:120]}", "error")
        return redirect(url_for("main.analysis", analysis_id=analysis_id))

    file_stem = doc.get("file_name", "report").rsplit(".", 1)[0]
    resp = make_response(html_report)
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    resp.headers["Content-Disposition"] = f'attachment; filename="{file_stem}_profile.html"'
    return resp


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
                doc.get("ai_result", {}),
                doc.get("chat_history", []),
                message,
            )
            # Execute any code blocks the AI generated
            code_blocks = extract_code_blocks(response)
            if code_blocks:
                cleaned_rows = doc.get("cleaned_rows", [])
                if cleaned_rows:
                    df = build_dataframe(cleaned_rows)
                    for code in code_blocks:
                        result = execute_code(code, df)
                        if result["success"] and result["output"]:
                            response += f"\n\n**📊 Result:**\n```\n{result['output']}\n```"
                        elif result["error"]:
                            response += f"\n\n**⚠ Code execution error:** `{result['error']}`"
            append_chat_message(analysis_id, "assistant", response)
        return redirect(url_for("main.chat", analysis_id=analysis_id))

    doc       = get_analysis(analysis_id, current_user.id)
    suggested = []
    if not doc.get("chat_history"):
        try:
            suggested = generate_suggested_questions(
                doc.get("summary", {}),
                doc.get("ai_result", {}),
            )
        except Exception:
            pass

    return render_template("main/chat.html", doc=doc, suggested=suggested)


@main_bp.route("/analysis/<analysis_id>/chat/stream", methods=["POST"])
@login_required
def chat_stream(analysis_id):
    doc = get_analysis(analysis_id, current_user.id)
    if not doc:
        return {"error": "Not found"}, 404

    data    = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    if not message:
        return {"error": "Empty message"}, 400

    append_chat_message(analysis_id, "user", message)
    doc = get_analysis(analysis_id, current_user.id)

    def generate():
        full = []
        try:
            for chunk in chat_with_data_stream(
                doc.get("summary", {}),
                doc.get("ai_result", {}),
                doc.get("chat_history", []),
                message,
            ):
                full.append(chunk)
                yield f"data: {flask_json.dumps({'chunk': chunk})}\n\n"
        except Exception as e:
            yield f"data: {flask_json.dumps({'error': str(e)[:120]})}\n\n"
            return

        ai_text = "".join(full)

        # Check if the AI generated code blocks to execute
        code_blocks = extract_code_blocks(ai_text)
        if code_blocks:
            cleaned_rows = doc.get("cleaned_rows", [])
            if cleaned_rows:
                df = build_dataframe(cleaned_rows)
                for i, code in enumerate(code_blocks):
                    result = execute_code(code, df)
                    if result["success"] and result["output"]:
                        exec_output = f"\n\n**📊 Result:**\n```\n{result['output']}\n```"
                    elif result["error"]:
                        exec_output = f"\n\n**⚠ Code execution error:** `{result['error']}`"
                    else:
                        exec_output = "\n\n*(No output produced)*"

                    # Stream the execution result
                    yield f"data: {flask_json.dumps({'chunk': exec_output})}\n\n"
                    ai_text += exec_output

        append_chat_message(analysis_id, "assistant", ai_text)
        yield f"data: {flask_json.dumps({'done': True})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

@main_bp.route("/analysis/<analysis_id>/chat/clear", methods=["POST"])
@login_required
def clear_chat(analysis_id):
    doc = get_analysis(analysis_id, current_user.id)
    if not doc:
        flash("Analysis not found.", "error")
        return redirect(url_for("main.history"))
    update_analysis(analysis_id, {"chat_history": []})
    flash("Chat history cleared.", "success")
    return redirect(url_for("main.chat", analysis_id=analysis_id))


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


@main_bp.route("/analysis/<analysis_id>/export/excel")
@login_required
def export_excel_route(analysis_id):
    doc = get_analysis(analysis_id, current_user.id)
    if not doc:
        flash("Analysis not found.", "error")
        return redirect(url_for("main.history"))
    rows = doc.get("cleaned_rows", [])
    if not rows:
        flash("No data to export.", "error")
        return redirect(url_for("main.analysis", analysis_id=analysis_id))
    file_stem = doc.get("file_name", "export").rsplit(".", 1)[0]
    data, filename = export_excel(rows, file_stem)
    resp = make_response(data)
    resp.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp

@main_bp.route("/analysis/<analysis_id>/export/json")
@login_required
def export_json_route(analysis_id):
    doc = get_analysis(analysis_id, current_user.id)
    if not doc:
        flash("Analysis not found.", "error")
        return redirect(url_for("main.history"))
    rows = doc.get("cleaned_rows", [])
    if not rows:
        flash("No data to export.", "error")
        return redirect(url_for("main.analysis", analysis_id=analysis_id))
    file_stem = doc.get("file_name", "export").rsplit(".", 1)[0]
    data, filename = export_json(rows, file_stem)
    resp = make_response(data)
    resp.headers["Content-Type"] = "application/json"
    resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp

@main_bp.route("/analysis/<analysis_id>/export/parquet")
@login_required
def export_parquet_route(analysis_id):
    doc = get_analysis(analysis_id, current_user.id)
    if not doc:
        flash("Analysis not found.", "error")
        return redirect(url_for("main.history"))
    rows = doc.get("cleaned_rows", [])
    if not rows:
        flash("No data to export.", "error")
        return redirect(url_for("main.analysis", analysis_id=analysis_id))
    file_stem = doc.get("file_name", "export").rsplit(".", 1)[0]
    try:
        data, filename = export_parquet(rows, file_stem)
    except ImportError:
        flash("Parquet export is not supported on this server.", "error")
        return redirect(url_for("main.analysis", analysis_id=analysis_id))
    resp = make_response(data)
    resp.headers["Content-Type"] = "application/octet-stream"
    resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp

@main_bp.route("/analysis/<analysis_id>/export/pdf")
@login_required
def export_pdf_route(analysis_id):
    doc = get_analysis(analysis_id, current_user.id)
    if not doc:
        flash("Analysis not found.", "error")
        return redirect(url_for("main.history"))
    rows = doc.get("cleaned_rows", [])
    if not rows:
        flash("No data to export.", "error")
        return redirect(url_for("main.analysis", analysis_id=analysis_id))
    file_stem = doc.get("file_name", "export").rsplit(".", 1)[0]
    summary = doc.get("summary", {})
    ai_result = doc.get("ai_result", {})
    charts_b64 = doc.get("charts_b64", {})
    data, filename = export_pdf(rows, summary, ai_result, charts_b64, file_stem)
    resp = make_response(data)
    resp.headers["Content-Type"] = "application/pdf"
    resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
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


# ── Sharing ───────────────────────────────────────────────────────────────────

@main_bp.route("/analysis/<analysis_id>/share", methods=["POST"])
@login_required
def toggle_share(analysis_id):
    doc = get_analysis(analysis_id, current_user.id)
    if not doc:
        return {"error": "Not found"}, 404

    action   = request.form.get("action", "")
    password = request.form.get("password", "").strip() or None

    if action == "enable":
        token     = enable_sharing(analysis_id, password)
        share_url = url_for("main.shared_view", token=token, _external=True)
        return {
            "token":              token,
            "url":                share_url,
            "password_protected": password is not None,
        }

    if action == "disable":
        disable_sharing(analysis_id)
        return {"disabled": True}

    return {"error": "Invalid action"}, 400


@main_bp.route("/analysis/<analysis_id>/share/password", methods=["POST"])
@login_required
def update_share_password(analysis_id):
    doc = get_analysis(analysis_id, current_user.id)
    if not doc or not doc.get("share_token"):
        return {"error": "Not found or sharing not enabled"}, 404

    new_pw = request.form.get("password", "").strip() or None
    hashed = (
        bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode()
        if new_pw else None
    )
    from bson import ObjectId
    from app import db
    db.analyses.update_one(
        {"_id": ObjectId(analysis_id)},
        {"$set": {"share_password": hashed, "updated_at": datetime.now(timezone.utc)}}
    )
    return {"updated": True, "password_protected": new_pw is not None}


@main_bp.route("/s/<token>", methods=["GET", "POST"])
def shared_view(token):
    doc = get_analysis_by_token(token)
    if not doc:
        return render_template("main/shared_404.html"), 404

    pw_hash = doc.get("share_password")
    if pw_hash:
        session_key = f"share_auth_{token}"
        if not session.get(session_key):
            error = None
            if request.method == "POST":
                entered = request.form.get("password", "")
                if bcrypt.checkpw(entered.encode(), pw_hash.encode()):
                    session[session_key] = True
                    return redirect(url_for("main.shared_view", token=token))
                error = "Incorrect password."
            return render_template(
                "main/shared_password.html", token=token, error=error
            )

    return render_template(
        "main/shared_analysis.html",
        doc=doc,
        summary=doc.get("summary", {}),
        ai_result=doc.get("ai_result", {}),
        chart_configs=doc.get("chart_configs", {}),
        token=token,
    )


# ── Profile ───────────────────────────────────────────────────────────────────

@main_bp.route("/profile")
@login_required
def profile():
    analyses  = get_user_analyses(current_user.id)
    total_charts = sum(len(a.get("chart_configs", {})) for a in analyses)
    total_chats  = sum(len(a.get("chat_history", [])) for a in analyses)
    from bson import ObjectId
    from app import db
    raw_doc = db.users.find_one(
        {"_id": ObjectId(current_user.id)},
        {"oauth_providers": 1}
    )
    oauth_providers = [
        p["provider"] for p in (raw_doc or {}).get("oauth_providers", [])
    ]
    return render_template("main/profile.html",
        analyses=analyses,
        total_charts=total_charts,
        total_chats=total_chats,
        oauth_providers=oauth_providers,
    )
# ── Dashboard & Power BI Export ───────────────────────────────────────────────

@main_bp.route("/analysis/<analysis_id>/dashboard")
@login_required
def dashboard(analysis_id):
    doc = get_analysis(analysis_id, current_user.id)
    if not doc:
        flash("Analysis not found.", "error")
        return redirect(url_for("main.history"))

    rows = doc.get("cleaned_rows", [])
    if not rows:
        flash("No data available for dashboard.", "error")
        return redirect(url_for("main.analysis", analysis_id=analysis_id))

    try:
        dashboard_data = build_dashboard(rows, doc.get("file_name", "dataset"))
    except Exception as e:
        flash(f"Dashboard generation failed: {str(e)[:120]}", "error")
        return redirect(url_for("main.analysis", analysis_id=analysis_id))

    return render_template(
        "main/dashboard.html",
        doc=doc,
        kpis=dashboard_data["kpis"],
        charts=dashboard_data["charts"],
        detected_cols=dashboard_data["detected_cols"],
        analysis_id=analysis_id,
    )


@main_bp.route("/analysis/<analysis_id>/dashboard/export-pbix")
@login_required
def export_pbix(analysis_id):
    doc = get_analysis(analysis_id, current_user.id)
    if not doc:
        flash("Analysis not found.", "error")
        return redirect(url_for("main.history"))

    rows = doc.get("cleaned_rows", [])
    if not rows:
        flash("No data to export.", "error")
        return redirect(url_for("main.dashboard", analysis_id=analysis_id))

    df   = pd.DataFrame(rows)
    cols = detect_dashboard_columns(df)

    try:
        pbix_bytes = generate_pbix(rows, doc.get("file_name", "dataset"), cols)
    except Exception as e:
        flash(f"Power BI export failed: {str(e)[:120]}", "error")
        return redirect(url_for("main.dashboard", analysis_id=analysis_id))

    file_stem = doc.get("file_name", "report").rsplit(".", 1)[0]
    resp = make_response(pbix_bytes)
    resp.headers["Content-Type"]        = "application/octet-stream"
    resp.headers["Content-Disposition"] = f'attachment; filename="{file_stem}_dashboard.pbix"'
    return resp



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
