import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import base64
from io import BytesIO


# ── Design tokens (matches CSS) ───────────────────────────────────────────────
SIENNA  = "#C2571A"
SIENNA_LT = "#E8845A"
SAND    = "#E8DDD0"
SAND_DK = "#D9CEBC"
INK     = "#1C1712"
MUTED   = "#8A7F74"

PALETTE = [SIENNA, "#E8A87C", "#A0522D", "#D4874E", "#7B3F1F", "#F0C9A0"]

def _apply_style(fig, ax):
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FAF7F2")
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.xaxis.label.set_color(INK)
    ax.yaxis.label.set_color(INK)
    ax.title.set_color(INK)
    for spine in ax.spines.values():
        spine.set_edgecolor(SAND)
    ax.grid(axis="y", color=SAND, linewidth=0.8, linestyle="--")
    ax.grid(axis="x", visible=False)

def _fig_to_b64(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=110, facecolor="#FFFFFF")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")

def _numpy_to_native(obj):
    """Recursively convert numpy types to Python-native types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: _numpy_to_native(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_numpy_to_native(v) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return _numpy_to_native(obj.tolist())
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    return obj


def _base_layout(title, showlegend=False):
    """Return a Plotly layout dict with the app's sienna/sand design tokens."""
    return {
        "title": {
            "text": title,
            "y": 0.95,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top"
        },
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"family": "Epilogue, sans-serif", "color": INK, "size": 11},
        "margin": {"t": 60, "b": 60, "l": 60, "r": 30, "pad": 4},
        "showlegend": showlegend,
        "xaxis": {"gridcolor": SAND, "linecolor": SAND_DK, "automargin": True},
        "yaxis": {"gridcolor": SAND, "linecolor": SAND_DK, "automargin": True},
    }


def tag_columns(df, col_info):
    for col in col_info:
        name = col["name"]
        name_lower = name.lower()
        dtype = col["dtype"]
        unique = col["unique"]
        nulls = col["nulls"]
        
        tag = "unknown"
        conf = 0.0
        
        # Boolean check
        if unique == 2:
            vals = df[name].dropna().unique()
            bool_set = {0, 1, True, False, "true", "false", "yes", "no", "y", "n"}
            if all(str(v).lower() in [str(b).lower() for b in bool_set] for v in vals):
                tag = "boolean"
                conf = 0.97
        
        # ID check
        if tag == "unknown":
            if any(s in name_lower for s in ["id", "_id", "uuid", "key", "code", "ref", "num", "no"]):
                if unique / max(len(df), 1) > 0.9:
                    tag = "id"
                    conf = 0.92
                    
        # Date check
        if tag == "unknown":
            if "datetime64" in dtype:
                tag = "date"
                conf = 1.0
            elif dtype == "object":
                sample = df[name].dropna().head(50)
                if not sample.empty:
                    parsed = pd.to_datetime(sample, format="mixed", errors="coerce")
                    success_rate = parsed.notnull().mean()
                    if success_rate > 0.8:
                        tag = "date"
                        conf = float(success_rate)
                        
        # Currency check
        if tag == "unknown":
            if "int" in dtype or "float" in dtype:
                if any(s in name_lower for s in ["price", "cost", "revenue", "salary", "amount", "fee", "charge", "total", "gross", "net", "spend", "budget", "payment", "earnings"]):
                    tag = "currency"
                    conf = 0.88
            elif dtype == "object":
                sample = df[name].dropna().head(50)
                if not sample.empty:
                    regex = r"^[\$\€\£\₹]?[\d,]+\.?\d*$"
                    matches = sample.astype(str).str.match(regex).mean()
                    if matches > 0.6:
                        tag = "currency"
                        conf = 0.82
                        
        # Category check
        if tag == "unknown":
            if dtype in ["object", "category"]:
                if unique <= 50 and unique / max(len(df), 1) < 0.05:
                    tag = "category"
                    conf = 1.0 - (unique / 50.0)
                    
        # Text check
        if tag == "unknown":
            if dtype == "object":
                sample = df[name].dropna().head(100)
                if not sample.empty:
                    avg_len = sample.astype(str).str.len().mean()
                    if avg_len > 40:
                        tag = "text"
                        conf = 0.80
                        
        # Numeric check
        if tag == "unknown":
            if "int" in dtype or "float" in dtype:
                tag = "numeric"
                conf = 0.95
                
        col["tag"] = tag
        col["tag_confidence"] = float(conf)
        col["tag_color"] = f"tag-{tag}"
        
        # Anomalies
        anomalies = []
        valid_data = df[name].dropna()
        n_valid = len(valid_data)
        
        if n_valid > 1 and ("int" in dtype or "float" in dtype):
            # Skewness
            skew = valid_data.skew()
            if pd.notnull(skew) and abs(skew) > 2:
                anomalies.append(f"High skew ({skew:.2f}) — distribution is heavily skewed")
            
            # Zeros
            zero_rate = (valid_data == 0).mean()
            if zero_rate > 0.3:
                anomalies.append(f"{zero_rate*100:.0f}% zero values — possible data gap")
                
            # Negatives
            if tag in ["currency", "numeric"]:
                negs = (valid_data < 0).sum()
                if negs > 0:
                    anomalies.append(f"{negs} negative values in a numeric column")
                    
            # Outliers
            q1 = valid_data.quantile(0.25)
            q3 = valid_data.quantile(0.75)
            iqr = q3 - q1
            outliers = (valid_data > q3 + 3*iqr).sum() + (valid_data < q1 - 3*iqr).sum()
            if outliers > 0:
                anomalies.append(f"{outliers} extreme outliers (>3× IQR from quartiles)")
                
        if unique == 1 and len(df) > 0:
            anomalies.append("Column has only one unique value — no analytical value")
            
        if nulls / max(len(df), 1) > 0.3:
            anomalies.append(f"{nulls/len(df)*100:.0f}% missing values")
            
        if dtype == "object" and n_valid > 0:
            sample = valid_data.head(100)
            numeric_parseable = pd.to_numeric(sample, errors="coerce").notnull().mean()
            if 0.2 < numeric_parseable < 0.8:
                anomalies.append("Mixed numeric and text values detected")
                
        if tag == "id" and unique < len(df):
            anomalies.append(f"{len(df) - unique} duplicate ID values")
            
        col["anomalies"] = anomalies

    return col_info

def parse_and_analyse(file_path, file_name):
    """Parse CSV/Excel, return summary dict + cleaned rows + chart_configs."""
    # Load
    if file_name.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(file_path)
    else:
        for enc in ["utf-8", "latin-1", "cp1252"]:
            try:
                df = pd.read_csv(file_path, encoding=enc)
                break
            except Exception:
                pass

    df.columns = df.columns.str.strip()

    # ── Summary ──────────────────────────────────────────────────────────────
    col_info = []
    for col in df.columns:
        dtype  = str(df[col].dtype)
        nulls  = int(df[col].isnull().sum())
        unique = int(df[col].nunique())
        info   = {"name": col, "dtype": dtype, "nulls": nulls, "unique": unique}
        if pd.api.types.is_numeric_dtype(df[col]) and not df[col].isnull().all():
            info["min"]  = round(float(df[col].min()), 4)
            info["max"]  = round(float(df[col].max()), 4)
            info["mean"] = round(float(df[col].mean()), 4)
        else:
            info["top_values"] = df[col].value_counts().head(5).index.astype(str).tolist()
        col_info.append(info)

    sample = df.head(5).replace({np.nan: None}).to_dict(orient="records")
    sample_str = str(sample)[:3000]

    col_info = tag_columns(df, col_info)

    summary = {
        "rows":           int(len(df)),
        "cols":           int(len(df.columns)),
        "columns":        col_info,
        "sample_str":     sample_str,
        "null_total":     int(df.isnull().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "memory_kb":      round(df.memory_usage(deep=True).sum() / 1024, 1),
    }

    # ── Cleaning ──────────────────────────────────────────────────────────────
    df = df.drop_duplicates()
    num_cols = df.select_dtypes(include=[np.number]).columns
    df[num_cols] = df[num_cols].fillna(df[num_cols].mean())
    cat_cols = df.select_dtypes(exclude=[np.number]).columns
    for col in cat_cols:
        if df[col].isnull().any():
            mode = df[col].mode()
            df[col] = df[col].fillna(mode[0] if not mode.empty else "Unknown")

    cleaned_rows = df.head(2000).replace({np.nan: None}).to_dict(orient="records")

    # ── Chart configs (Plotly dicts) ──────────────────────────────────────────
    chart_configs = {}
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()

    # 1. Bar chart
    if cat_cols and num_cols:
        try:
            grp = df.groupby(cat_cols[0])[num_cols[0]].mean().nlargest(12).reset_index()
            x_vals = [s[:16] for s in grp[cat_cols[0]].astype(str).tolist()]
            y_vals = grp[num_cols[0]].tolist()
            layout = _base_layout(f"Avg {num_cols[0]} by {cat_cols[0]}")
            layout["xaxis"]["title"] = cat_cols[0]
            layout["yaxis"]["title"] = num_cols[0]
            layout["xaxis"]["tickangle"] = -35
            chart_configs["bar"] = _numpy_to_native({
                "data": [{
                    "type": "bar",
                    "x": x_vals,
                    "y": y_vals,
                    "marker": {
                        "color": PALETTE[:len(x_vals)],
                        "line": {"color": "#FFFFFF", "width": 0.5},
                    },
                }],
                "layout": layout,
            })
        except Exception:
            pass

    # 2. Histogram
    if num_cols:
        try:
            values = df[num_cols[0]].dropna().tolist()
            layout = _base_layout(f"Distribution of {num_cols[0]}")
            layout["xaxis"]["title"] = num_cols[0]
            layout["yaxis"]["title"] = "Count"
            chart_configs["histogram"] = _numpy_to_native({
                "data": [{
                    "type": "histogram",
                    "x": values,
                    "nbinsx": 25,
                    "marker": {
                        "color": SIENNA,
                        "line": {"color": "#FFFFFF", "width": 0.4},
                    },
                    "opacity": 0.9,
                }],
                "layout": layout,
            })
        except Exception:
            pass

    # 3. Scatter
    if len(num_cols) >= 2:
        try:
            sub = df[[num_cols[0], num_cols[1]]].dropna().head(500)
            layout = _base_layout(f"{num_cols[0]} vs {num_cols[1]}")
            layout["xaxis"]["title"] = num_cols[0]
            layout["yaxis"]["title"] = num_cols[1]
            chart_configs["scatter"] = _numpy_to_native({
                "data": [{
                    "type": "scatter",
                    "mode": "markers",
                    "x": sub[num_cols[0]].tolist(),
                    "y": sub[num_cols[1]].tolist(),
                    "marker": {
                        "color": SIENNA,
                        "opacity": 0.6,
                        "size": 6,
                        "line": {"color": "#FFFFFF", "width": 0.3},
                    },
                }],
                "layout": layout,
            })
        except Exception:
            pass

    # 4. Line
    if num_cols:
        try:
            date_col = next((c for c in df.columns if "date" in c.lower() or "time" in c.lower()), None)
            if date_col:
                sub = df[[date_col, num_cols[0]]].dropna().head(200)
                x_vals = sub[date_col].astype(str).tolist()
                y_vals = sub[num_cols[0]].tolist()
            else:
                sub = df[num_cols[0]].dropna().head(200)
                x_vals = list(range(len(sub)))
                y_vals = sub.tolist()
            x_label = date_col if date_col else "Index"
            layout = _base_layout(f"{num_cols[0]} over {'time' if date_col else 'index'}")
            layout["xaxis"]["title"] = x_label
            layout["yaxis"]["title"] = num_cols[0]
            layout["xaxis"]["nticks"] = 10
            layout["xaxis"]["tickangle"] = -35
            chart_configs["line"] = _numpy_to_native({
                "data": [{
                    "type": "scatter",
                    "mode": "lines+markers",
                    "x": x_vals,
                    "y": y_vals,
                    "fill": "tozeroy",
                    "fillcolor": "rgba(194,87,26,0.10)",
                    "line": {"color": SIENNA, "width": 2},
                    "marker": {"color": "#FFFFFF", "size": 3,
                               "line": {"color": SIENNA, "width": 1.5}},
                }],
                "layout": layout,
            })
        except Exception:
            pass

    # 5. Pie
    if cat_cols:
        try:
            vc = df[cat_cols[0]].value_counts().head(6)
            layout = _base_layout(f"Breakdown of {cat_cols[0]}", showlegend=True)
            # Pie charts don't use xaxis/yaxis
            layout.pop("xaxis", None)
            layout.pop("yaxis", None)
            layout["legend"] = {"orientation": "h", "yanchor": "top", "y": -0.1, "xanchor": "center", "x": 0.5}
            chart_configs["pie"] = _numpy_to_native({
                "data": [{
                    "type": "pie",
                    "labels": vc.index.astype(str).tolist(),
                    "values": vc.values.tolist(),
                    "marker": {
                        "colors": PALETTE[:len(vc)],
                        "line": {"color": "#FFFFFF", "width": 1.5},
                    },
                    "textinfo": "percent",
                    "textposition": "inside",
                    "hole": 0.0,
                }],
                "layout": layout,
            })
        except Exception:
            pass

    # 6. Correlation heatmap
    if len(num_cols) >= 2:
        try:
            corr_cols = num_cols[:10]
            corr = df[corr_cols].corr().round(2)
            z_vals = corr.values.tolist()
            col_names = [c[:12] for c in corr.columns.tolist()]
            n = len(col_names)
            annot_size = 10 if n <= 5 else (8 if n <= 8 else 7)
            layout = _base_layout("Correlation Matrix")
            layout["xaxis"]["tickangle"] = -45
            layout["xaxis"]["tickfont"] = {"size": 9}
            layout["yaxis"]["tickfont"] = {"size": 9}
            layout["margin"] = {"t": 60, "b": 80, "l": 80, "r": 40, "pad": 4}
            chart_configs["heatmap"] = _numpy_to_native({
                "data": [{
                    "type": "heatmap",
                    "z": z_vals,
                    "x": col_names,
                    "y": col_names,
                    "colorscale": "RdBu",
                    "zmid": 0,
                    "text": z_vals,
                    "texttemplate": "%{text:.2f}",
                    "textfont": {"size": annot_size, "color": INK},
                    "showscale": True,
                    "colorbar": {"thickness": 12, "len": 0.6},
                }],
                "layout": layout,
            })
        except Exception:
            pass

    # ── Matplotlib Charts (for PDF export) ────────────────────────────────────
    charts_b64 = {}
    
    plt.rcParams.update({
        "font.family":    "sans-serif",
        "font.size":      9,
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
    })

    if cat_cols and num_cols:
        try:
            grp = df.groupby(cat_cols[0])[num_cols[0]].mean().nlargest(12).reset_index()
            fig, ax = plt.subplots(figsize=(6, 3.5))
            ax.bar(grp[cat_cols[0]].astype(str), grp[num_cols[0]], color=PALETTE, edgecolor="white", linewidth=0.5)
            ax.set_title(f"Avg {num_cols[0]} by {cat_cols[0]}")
            ax.set_xlabel(cat_cols[0])
            ax.set_ylabel(num_cols[0])
            plt.xticks(rotation=30, ha="right")
            _apply_style(fig, ax)
            charts_b64["bar"] = _fig_to_b64(fig)
        except Exception:
            pass

    if num_cols:
        try:
            fig, ax = plt.subplots(figsize=(6, 3.5))
            ax.hist(df[num_cols[0]].dropna(), bins=25, color=SIENNA, edgecolor="white", linewidth=0.4, alpha=0.9)
            ax.set_title(f"Distribution of {num_cols[0]}")
            ax.set_xlabel(num_cols[0])
            ax.set_ylabel("Count")
            _apply_style(fig, ax)
            charts_b64["histogram"] = _fig_to_b64(fig)
        except Exception:
            pass

    if len(num_cols) >= 2:
        try:
            sub = df[[num_cols[0], num_cols[1]]].dropna().head(500)
            fig, ax = plt.subplots(figsize=(6, 3.5))
            ax.scatter(sub[num_cols[0]], sub[num_cols[1]], color=SIENNA, alpha=0.55, s=18, edgecolors="white", linewidths=0.3)
            ax.set_title(f"{num_cols[0]} vs {num_cols[1]}")
            ax.set_xlabel(num_cols[0])
            ax.set_ylabel(num_cols[1])
            _apply_style(fig, ax)
            charts_b64["scatter"] = _fig_to_b64(fig)
        except Exception:
            pass

    if num_cols:
        try:
            date_col = next((c for c in df.columns if "date" in c.lower() or "time" in c.lower()), None)
            if date_col:
                sub = df[[date_col, num_cols[0]]].dropna().head(200)
                x_vals = sub[date_col].astype(str)
            else:
                sub = df[num_cols[0]].dropna().head(200)
                x_vals = range(len(sub))
            fig, ax = plt.subplots(figsize=(6, 3.5))
            ax.plot(x_vals, sub[num_cols[0]] if date_col else sub, color=SIENNA, linewidth=1.8, marker="o", markersize=3, markerfacecolor="white", markeredgecolor=SIENNA)
            ax.fill_between(list(x_vals), list(sub[num_cols[0]] if date_col else sub), alpha=0.12, color=SIENNA)
            ax.set_title(f"{num_cols[0]} over {'time' if date_col else 'index'}")
            plt.xticks(rotation=30, ha="right")
            _apply_style(fig, ax)
            charts_b64["line"] = _fig_to_b64(fig)
        except Exception:
            pass

    if cat_cols:
        try:
            vc = df[cat_cols[0]].value_counts().head(6)
            fig, ax = plt.subplots(figsize=(5, 4))
            fig.patch.set_facecolor("#FFFFFF")
            wedges, texts, autotexts = ax.pie(
                vc.values, labels=vc.index.astype(str),
                colors=PALETTE[:len(vc)],
                autopct="%1.1f%%", startangle=140,
                wedgeprops={"edgecolor": "white", "linewidth": 1.5}
            )
            for t in texts + autotexts:
                t.set_color(INK)
                t.set_fontsize(8)
            ax.set_title(f"Breakdown of {cat_cols[0]}", color=INK, fontweight="bold", fontsize=11)
            charts_b64["pie"] = _fig_to_b64(fig)
        except Exception:
            pass

    if len(num_cols) >= 2:
        try:
            corr_cols = num_cols[:10]
            corr = df[corr_cols].corr().round(2)
            fig, ax = plt.subplots(figsize=(6, 4.5))
            fig.patch.set_facecolor("#FFFFFF")
            cmap = sns.color_palette("YlOrBr", as_cmap=True)
            sns.heatmap(
                corr, ax=ax, cmap=cmap, annot=True, fmt=".2f",
                linewidths=0.5, linecolor="white",
                annot_kws={"size": 8, "color": INK},
                cbar_kws={"shrink": 0.8}
            )
            ax.set_facecolor("#FAF7F2")
            ax.set_title("Correlation Matrix", color=INK, fontweight="bold", fontsize=11)
            ax.tick_params(colors=MUTED, labelsize=8)
            charts_b64["heatmap"] = _fig_to_b64(fig)
        except Exception:
            pass

    return summary, cleaned_rows, chart_configs, charts_b64
