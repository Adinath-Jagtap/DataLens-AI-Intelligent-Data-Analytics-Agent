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
        tag = c.get("tag", "unknown")
        anomaly_str = "; ".join(c.get("anomalies", [])[:2]) or "none"
        if "min" in c:
            col_lines.append(f"  - {c['name']} [{tag}] ({c['dtype']}): min={c['min']}, max={c['max']}, mean={c['mean']}, nulls={c['nulls']}, anomalies: {anomaly_str}")
        else:
            col_lines.append(f"  - {c['name']} [{tag}] ({c['dtype']}): top={c.get('top_values', [])[:3]}, nulls={c['nulls']}, unique={c['unique']}, anomalies: {anomaly_str}")

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


def _build_system_prompt(summary: dict, ai_result: dict) -> str:
    rows      = summary.get("rows", 0)
    cols      = summary.get("cols", 0)
    nulls     = summary.get("null_total", 0)
    dupes     = summary.get("duplicate_rows", 0)
    mem_kb    = summary.get("memory_kb", 0)
    score     = ai_result.get("quality_score", "N/A")
    ds_type   = ai_result.get("dataset_type", "General dataset")
    file_name = summary.get("file_name", "uploaded dataset")

    # Column profiles
    col_lines = []
    for c in summary.get("columns", []):
        tag = c.get("tag", c["dtype"])
        if "min" in c:
            line = (
                f"- {c['name']} [{tag}]: "
                f"range {c['min']}–{c['max']}, "
                f"mean {c['mean']:.2f}, "
                f"nulls {c['nulls']}/{rows}"
            )
        else:
            top = ", ".join(str(v) for v in c.get("top_values", [])[:5])
            line = (
                f"- {c['name']} [{tag}]: "
                f"{c['unique']} unique values, "
                f"top: {top}, "
                f"nulls {c['nulls']}/{rows}"
            )
        anomalies = c.get("anomalies", [])
        if anomalies:
            line += f" — WARNING: {anomalies[0]}"
        col_lines.append(line)

    cols_text = "\n".join(col_lines) if col_lines else "No column info available."

    # AI insights already generated
    insights = ai_result.get("key_insights", [])
    insights_text = (
        "\n".join(f"- {i}" for i in insights)
        if insights else "None generated yet."
    )

    cleaning = ai_result.get("cleaning_steps", [])
    cleaning_text = (
        "\n".join(f"- {s}" for s in cleaning)
        if cleaning else "None."
    )

    return f"""You are DataLens AI, an expert data analyst assistant.
The user has uploaded a dataset and you have FULL ACCESS to run code on it.
A pandas DataFrame called `df` is pre-loaded with ALL the data.
You also have `pd` (pandas) and `np` (numpy) available.

## Dataset overview
File: {file_name}
Type: {ds_type}
Rows: {rows:,} | Columns: {cols} | Memory: {mem_kb:.1f} KB
Missing values: {nulls} | Duplicate rows: {dupes}
Data quality score: {score}/100

## Column profiles
{cols_text}

## Previously generated AI insights
{insights_text}

## Recommended cleaning steps
{cleaning_text}

## How to answer data questions
When the user asks a question that requires looking at the actual data (filtering, grouping, counting, correlations, averages, etc.), write a Python code block that computes the answer and prints it.

Example:
User: "What is the average salary by department?"
```python
result = df.groupby('Department')['Salary'].mean().round(2).sort_values(ascending=False)
print(result.to_string())
```

Rules for code blocks:
- Always use `print()` to output results
- The DataFrame is called `df` — do NOT load data from files
- Use `pd` and `np` freely — they are pre-imported
- Do NOT use import statements — everything you need is already available
- Format output nicely with .round(), .to_string(), f-strings
- For large results, limit output (e.g. .head(20))
- If a column name has spaces, use bracket notation: df['Column Name']

## When NOT to write code
- General data science questions → answer in plain text
- Questions answerable from the column profiles above → answer directly
- Advice, explanations, methodology questions → answer in plain text

## Behavioural rules
- Use the exact column names from the profiles above — never guess.
- Format numbers with commas for readability (e.g. 1,234,567).
- Keep responses concise. Aim for under 200 words unless genuinely needed.
- Never fabricate column names, values, or statistics not present in the profiles.
- If the user asks what columns exist, list them all with their tags.
- If the user asks general questions, help them regardless."""

def chat_with_data(
    summary: dict,
    ai_result: dict,
    chat_history: list,
    user_message: str,
) -> str:
    system   = _build_system_prompt(summary, ai_result)
    messages = [{"role": "system", "content": system}]
    for msg in (chat_history or [])[-20:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    try:
        resp = _client().chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.4,
            max_tokens=1000,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Sorry, I couldn't process that request. ({str(e)[:100]})"

def chat_with_data_stream(
    summary: dict,
    ai_result: dict,
    chat_history: list,
    user_message: str,
):
    """Generator that yields text chunks from a streaming Groq response."""
    system   = _build_system_prompt(summary, ai_result)
    messages = [{"role": "system", "content": system}]
    for msg in (chat_history or [])[-20:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    stream = _client().chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.4,
        max_tokens=1000,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta

def generate_suggested_questions(summary: dict, ai_result: dict) -> list:
    """Generate 5 contextual starter questions. Falls back to rule-based on failure."""
    col_names = [c["name"] for c in summary.get("columns", [])[:15]]
    tags      = [c.get("tag", c["dtype"]) for c in summary.get("columns", [])[:15]]
    dtype_str = ", ".join(f"{n} ({t})" for n, t in zip(col_names, tags))
    ds_type   = ai_result.get("dataset_type", "dataset")
    rows      = summary.get("rows", 0)

    prompt = f"""Dataset columns: {dtype_str}
Dataset type: {ds_type}
Rows: {rows:,}

Generate exactly 5 short, specific questions a user might ask about this dataset.
Rules:
- Each question must reference actual column names listed above
- Mix types: summary stats, distributions, comparisons, anomalies, recommendations
- Each question must be under 12 words
- Return ONLY a JSON array of 5 strings — no explanation, no markdown backticks

Example: ["What is the average revenue?", "Which category has the most entries?"]"""

    try:
        resp = _client().chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=200,
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
        import json as _json
        result = _json.loads(raw)
        if isinstance(result, list):
            return [str(q) for q in result[:5]]
    except Exception:
        pass

    # Rule-based fallback
    num_cols = [c["name"] for c in summary.get("columns", []) if "min" in c]
    cat_cols = [c["name"] for c in summary.get("columns", []) if c.get("tag") == "category"]
    questions = []
    if num_cols:
        questions.append(f"What is the average {num_cols[0]}?")
    if len(num_cols) >= 2:
        questions.append(f"Is there a correlation between {num_cols[0]} and {num_cols[1]}?")
    if cat_cols:
        questions.append(f"What are the most common values in {cat_cols[0]}?")
    questions.append("What data quality issues should I be aware of?")
    questions.append("What analysis would you recommend for this dataset?")
    return questions[:5]


def extract_code_blocks(text: str) -> list:
    """Extract ```python code blocks from an AI response."""
    blocks = []
    pattern = re.compile(r"```python\s*\n(.*?)```", re.DOTALL)
    for match in pattern.finditer(text):
        code = match.group(1).strip()
        if code:
            blocks.append(code)
    return blocks
