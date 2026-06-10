import pandas as pd
import numpy as np
import io
import gc

def generate_profile(rows: list, file_name: str, minimal: bool = False) -> str:
    """
    Takes cleaned_rows (list of dicts), returns a self-contained HTML string.
    minimal=True runs a faster lightweight report (no correlations, no interactions).
    """
    try:
        from ydata_profiling import ProfileReport
    except ImportError:
        return "<html><body><div style='padding:2rem;font-family:sans-serif;'><h3>Missing Dependency</h3><p>The <b>ydata-profiling</b> package is not installed. Please install it to view the data profile.</p></div></body></html>"

    if not rows:
        return "<html><body><p>No data available for profiling.</p></body></html>"

    df = pd.DataFrame(rows)

    if len(df.columns) > 30:
        minimal = True

    # Attempt date column parsing
    for col in df.columns:
        if df[col].dtype == object:
            try:
                parsed = pd.to_datetime(df[col], format="mixed", errors="coerce")
                if parsed.notna().mean() > 0.8:
                    df[col] = parsed
            except Exception:
                pass

    profile = ProfileReport(
        df,
        title=f"Data Profile — {file_name}",
        minimal=minimal,
        explorative=not minimal,
        correlations={
            "pearson": {"calculate": not minimal},
            "spearman": {"calculate": not minimal},
            "kendall": {"calculate": False},
            "phi_k": {"calculate": False},
            "cramers": {"calculate": not minimal},
        },
        missing_diagrams={
            "bar": True,
            "matrix": not minimal,
            "heatmap": not minimal,
        },
        samples={"head": 10, "tail": 10},
        progress_bar=False,
    )

    html_out = profile.to_html()
    gc.collect()
    return html_out
