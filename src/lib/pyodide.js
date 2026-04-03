// src/lib/pyodide.js
// Runs pandas/numpy/scikit-learn fully in the browser via WebAssembly

let pyodideInstance = null;
let loading = false;
const listeners = [];

export async function getPyodide(onProgress) {
  if (pyodideInstance) return pyodideInstance;

  if (loading) {
    return new Promise(resolve => listeners.push(resolve));
  }

  loading = true;
  onProgress?.("Loading Python runtime… (first time only, ~5s)");

  pyodideInstance = await window.loadPyodide({
    indexURL: "https://cdn.jsdelivr.net/pyodide/v0.25.1/full/",
  });

  onProgress?.("Installing pandas & numpy…");
  await pyodideInstance.loadPackage(["pandas", "numpy", "scikit-learn"]);

  onProgress?.("Python ready ✓");
  loading = false;
  listeners.forEach(r => r(pyodideInstance));
  listeners.length = 0;

  return pyodideInstance;
}

/**
 * Parse CSV/Excel file → returns { columns, rows, summary }
 */
export async function parseDataset(file, onProgress) {
  const py = await getPyodide(onProgress);

  // Read file as ArrayBuffer
  const buffer = await file.arrayBuffer();
  const bytes   = new Uint8Array(buffer);

  const isExcel = file.name.match(/\.xlsx?$/i);

  py.globals.set("file_bytes", bytes);
  py.globals.set("is_excel",   isExcel ? 1 : 0);
  py.globals.set("file_name",  file.name);

  onProgress?.("Parsing file…");

  const result = await py.runPythonAsync(`
import pandas as pd
import numpy as np
import json
import io

raw = bytes(file_bytes)

if is_excel:
    df = pd.read_excel(io.BytesIO(raw))
else:
    # Try multiple encodings
    for enc in ['utf-8', 'latin-1', 'cp1252']:
        try:
            df = pd.read_csv(io.BytesIO(raw), encoding=enc)
            break
        except:
            pass

# Basic cleaning: strip column names
df.columns = df.columns.str.strip()

# Column analysis
col_info = []
for col in df.columns:
    dtype = str(df[col].dtype)
    nulls = int(df[col].isnull().sum())
    unique = int(df[col].nunique())
    info = {"name": col, "dtype": dtype, "nulls": nulls, "unique": unique}
    if pd.api.types.is_numeric_dtype(df[col]):
        info["min"]  = float(df[col].min()) if not df[col].isnull().all() else None
        info["max"]  = float(df[col].max()) if not df[col].isnull().all() else None
        info["mean"] = float(df[col].mean()) if not df[col].isnull().all() else None
        info["std"]  = float(df[col].std())  if not df[col].isnull().all() else None
    else:
        top = df[col].value_counts().head(5)
        info["top_values"] = top.index.tolist()
    col_info.append(info)

# Sample rows (for AI)
sample = df.head(5).replace({np.nan: None}).to_dict(orient="records")

# Full data for charts
all_rows = df.head(2000).replace({np.nan: None}).to_dict(orient="records")

summary = {
    "rows":        int(len(df)),
    "cols":        int(len(df.columns)),
    "columns":     col_info,
    "sample":      sample,
    "null_total":  int(df.isnull().sum().sum()),
    "duplicate_rows": int(df.duplicated().sum()),
    "memory_kb":   round(df.memory_usage(deep=True).sum() / 1024, 1),
}

json.dumps({"summary": summary, "rows": all_rows})
`);

  return JSON.parse(result);
}

/**
 * Clean dataset based on AI instructions
 */
export async function cleanDataset(rawRows, cleaningSteps, onProgress) {
  const py = await getPyodide(onProgress);

  py.globals.set("raw_json", JSON.stringify(rawRows));
  py.globals.set("steps",    JSON.stringify(cleaningSteps));

  onProgress?.("Cleaning data…");

  const result = await py.runPythonAsync(`
import pandas as pd
import numpy as np
import json

data  = json.loads(raw_json)
steps = json.loads(steps)

df = pd.DataFrame(data)

for step in steps:
    step_lower = step.lower()
    try:
        if "drop duplicate" in step_lower:
            df = df.drop_duplicates()

        elif "fill" in step_lower and "mean" in step_lower:
            num_cols = df.select_dtypes(include=[np.number]).columns
            df[num_cols] = df[num_cols].fillna(df[num_cols].mean())

        elif "fill" in step_lower and ("mode" in step_lower or "categorical" in step_lower):
            cat_cols = df.select_dtypes(exclude=[np.number]).columns
            for col in cat_cols:
                if df[col].isnull().any():
                    df[col] = df[col].fillna(df[col].mode()[0] if not df[col].mode().empty else "Unknown")

        elif "drop" in step_lower and "null" in step_lower:
            threshold = 0.5
            df = df.dropna(thresh=int(len(df.columns) * threshold))

        elif "strip" in step_lower or "trim" in step_lower:
            str_cols = df.select_dtypes(include=["object"]).columns
            df[str_cols] = df[str_cols].apply(lambda x: x.str.strip() if x.dtype == "object" else x)

        elif "lowercase" in step_lower:
            str_cols = df.select_dtypes(include=["object"]).columns
            df[str_cols] = df[str_cols].apply(lambda x: x.str.lower() if x.dtype == "object" else x)

        elif "outlier" in step_lower or "cap" in step_lower:
            num_cols = df.select_dtypes(include=[np.number]).columns
            for col in num_cols:
                q_low  = df[col].quantile(0.01)
                q_high = df[col].quantile(0.99)
                df[col] = df[col].clip(lower=q_low, upper=q_high)

        elif "convert" in step_lower and "date" in step_lower:
            for col in df.columns:
                if "date" in col.lower() or "time" in col.lower():
                    try:
                        df[col] = pd.to_datetime(df[col], errors="coerce").astype(str)
                    except:
                        pass

    except Exception as e:
        pass  # Skip failed steps, don't crash

cleaned = df.replace({np.nan: None}).to_dict(orient="records")
json.dumps({"rows": cleaned, "final_shape": [int(len(df)), int(len(df.columns))]})
`);

  return JSON.parse(result);
}

/**
 * Build data for a specific chart config
 */
export async function buildChartData(rows, chartConfig) {
  const py = await getPyodide();

  py.globals.set("rows_json",   JSON.stringify(rows));
  py.globals.set("chart_json",  JSON.stringify(chartConfig));

  const result = await py.runPythonAsync(`
import pandas as pd
import numpy as np
import json

rows   = json.loads(rows_json)
config = json.loads(chart_json)

df     = pd.DataFrame(rows)
ctype  = config.get("type", "bar")
x_col  = config.get("xCol")
y_col  = config.get("yCol")
color  = config.get("color", "#22d3ee")

out = {"type": ctype, "title": config.get("title","Chart"), "color": color}

try:
    if ctype == "bar" and x_col and y_col:
        grp = df.groupby(x_col)[y_col].mean().reset_index().head(20)
        out["x"] = grp[x_col].astype(str).tolist()
        out["y"] = grp[y_col].round(2).tolist()

    elif ctype == "line" and x_col and y_col:
        sub = df[[x_col, y_col]].dropna().head(200)
        out["x"] = sub[x_col].astype(str).tolist()
        out["y"] = sub[y_col].round(2).tolist()

    elif ctype == "scatter" and x_col and y_col:
        sub = df[[x_col, y_col]].dropna().head(500)
        out["x"] = sub[x_col].tolist()
        out["y"] = sub[y_col].tolist()

    elif ctype == "pie" and x_col:
        vc = df[x_col].value_counts().head(8)
        out["labels"] = vc.index.astype(str).tolist()
        out["values"] = vc.values.tolist()

    elif ctype == "histogram" and x_col:
        col_data = df[x_col].dropna()
        out["values"] = col_data.tolist()

    elif ctype == "box" and y_col:
        col_data = df[y_col].dropna()
        out["values"] = col_data.tolist()
        out["label"]  = y_col

    elif ctype == "heatmap":
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()[:10]
        corr = df[num_cols].corr().round(2)
        out["z"]    = corr.values.tolist()
        out["x"]    = corr.columns.tolist()
        out["y"]    = corr.index.tolist()

    elif ctype == "area" and x_col and y_col:
        sub = df[[x_col, y_col]].dropna().head(200)
        out["x"] = sub[x_col].astype(str).tolist()
        out["y"] = sub[y_col].round(2).tolist()

except Exception as e:
    out["error"] = str(e)

json.dumps(out)
`);

  return JSON.parse(result);
}
