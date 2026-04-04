import json
import re
from groq import Groq
from flask import current_app


def _client():
    return Groq(api_key=current_app.config["GROQ_API_KEY"])


def analyse_dataset(summary: dict) -> dict:
    """Send dataset summary to Groq, get insights JSON back."""
    col_lines = []
    for c in summary.get("columns", []):
        if "min" in c:
            col_lines.append(f"  - {c['name']} ({c['dtype']}): min={c['min']}, max={c['max']}, mean={c['mean']}, nulls={c['nulls']}")
        else:
            col_lines.append(f"  - {c['name']} ({c['dtype']}): top={c.get('top_values', [])[:3]}, nulls={c['nulls']}, unique={c['unique']}")

    prompt = f"""You are a data analyst. Analyse this dataset summary and return ONLY a raw JSON object — no markdown, no backticks, no explanation.

Dataset stats:
- Rows: {summary['rows']}, Columns: {summary['cols']}
- Total nulls: {summary['null_total']}, Duplicate rows: {summary['duplicate_rows']}
- Memory: {summary['memory_kb']} KB

Columns:
{chr(10).join(col_lines)}

Sample (first 5 rows):
{summary.get('sample_str', '')}

Return this exact JSON shape:
{{
  "key_insights": ["insight 1", "insight 2", "insight 3", "insight 4"],
  "quality_score": 85,
  "dataset_type": "Sales Data",
  "cleaning_steps": ["Drop duplicates", "Fill numeric nulls with mean"]
}}

quality_score is 0-100. Be specific and useful in insights. Return ONLY the JSON."""

    try:
        resp = _client().chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=600,
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
        return json.loads(raw)
    except Exception as e:
        return {
            "key_insights": [f"Analysis partially failed: {str(e)[:120]}"],
            "quality_score": 50,
            "dataset_type": "Unknown",
            "cleaning_steps": [],
        }


def chat_with_data(summary: dict, chat_history: list, user_message: str) -> str:
    """Return AI response for a user chat message about their dataset."""
    col_summary = ", ".join(
        f"{c['name']} ({c['dtype']})"
        for c in summary.get("columns", [])[:20]
    )
    system = f"""You are a helpful data analyst assistant. The user has uploaded a dataset with the following properties:

- Rows: {summary.get('rows')}, Columns: {summary.get('cols')}
- Column types: {col_summary}
- Data quality score: {summary.get('quality_score', 'N/A')}/100
- Total nulls: {summary.get('null_total')}

Answer questions about this dataset clearly and concisely. If asked for calculations or patterns, reason from the column info provided. Keep responses under 200 words."""

    messages = [{"role": "system", "content": system}]
    for msg in (chat_history or [])[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    try:
        resp = _client().chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.5,
            max_tokens=400,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Sorry, I couldn't process that request. ({str(e)[:100]})"
