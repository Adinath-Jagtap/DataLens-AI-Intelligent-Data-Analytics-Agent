import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import base64
from io import BytesIO

# ΓöÇΓöÇ Design tokens (matches CSS) ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
BG      = "#FAF7F2"
CARD    = "#FFFFFF"
INK     = "#1C1712"
SIENNA  = "#C2571A"
SAND    = "#E8DDD0"
MUTED   = "#8A7F74"

PALETTE = [SIENNA, "#E8A87C", "#A0522D", "#D4874E", "#7B3F1F", "#F0C9A0"]

def _apply_style(fig, ax):
    fig.patch.set_facecolor(CARD)
    ax.set_facecolor(BG)
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
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=110, facecolor=CARD)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def parse_and_analyse(file_path, file_name):
    """Parse CSV/Excel, return summary dict + cleaned rows + charts_b64."""
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

    # ΓöÇΓöÇ Summary ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
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

    summary = {
        "rows":           int(len(df)),
        "cols":           int(len(df.columns)),
        "columns":        col_info,
        "sample_str":     sample_str,
        "null_total":     int(df.isnull().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "memory_kb":      round(df.memory_usage(deep=True).sum() / 1024, 1),
    }

    # ΓöÇΓöÇ Cleaning ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    df = df.drop_duplicates()
    num_cols = df.select_dtypes(include=[np.number]).columns
    df[num_cols] = df[num_cols].fillna(df[num_cols].mean())
    cat_cols = df.select_dtypes(exclude=[np.number]).columns
    for col in cat_cols:
        if df[col].isnull().any():
            mode = df[col].mode()
            df[col] = df[col].fillna(mode[0] if not mode.empty else "Unknown")

    cleaned_rows = df.head(2000).replace({np.nan: None}).to_dict(orient="records")

    # ΓöÇΓöÇ Charts ΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇΓöÇ
    charts_b64 = {}
    num_cols   = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols   = df.select_dtypes(exclude=[np.number]).columns.tolist()

    plt.rcParams.update({
        "font.family":    "sans-serif",
        "font.size":      9,
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
    })

    # 1. Bar chart
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

    # 2. Histogram
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

    # 3. Scatter
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

    # 4. Line
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

    # 5. Pie
    if cat_cols:
        try:
            vc = df[cat_cols[0]].value_counts().head(6)
            fig, ax = plt.subplots(figsize=(5, 4))
            fig.patch.set_facecolor(CARD)
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

    # 6. Correlation heatmap
    if len(num_cols) >= 2:
        try:
            corr_cols = num_cols[:10]
            corr = df[corr_cols].corr().round(2)
            fig, ax = plt.subplots(figsize=(6, 4.5))
            fig.patch.set_facecolor(CARD)
            cmap = sns.color_palette("YlOrBr", as_cmap=True)
            sns.heatmap(
                corr, ax=ax, cmap=cmap, annot=True, fmt=".2f",
                linewidths=0.5, linecolor="white",
                annot_kws={"size": 8, "color": INK},
                cbar_kws={"shrink": 0.8}
            )
            ax.set_facecolor(BG)
            ax.set_title("Correlation Matrix", color=INK, fontweight="bold", fontsize=11)
            ax.tick_params(colors=MUTED, labelsize=8)
            charts_b64["heatmap"] = _fig_to_b64(fig)
        except Exception:
            pass

    return summary, cleaned_rows, charts_b64
