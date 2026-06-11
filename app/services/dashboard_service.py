import pandas as pd
import numpy as np
import zipfile
import json
import io

def detect_dashboard_columns(df: pd.DataFrame) -> dict:
    """
    Auto-detect which columns map to dashboard roles.
    Returns a dict with keys: date, sales, quantity, product, region, id.
    Values are column name strings or None if not found.
    """
    cols = {c.lower(): c for c in df.columns}
    result = {
        "date":     None,
        "sales":    None,
        "quantity": None,
        "product":  None,
        "region":   None,
        "id":       None,
    }

    # Date detection — try dtype first, then name patterns, then parse attempt
    for orig, lower in [(v, k) for k, v in cols.items()]:
        if pd.api.types.is_datetime64_any_dtype(df[orig]):
            result["date"] = orig
            break
    if not result["date"]:
        date_hints = ["date", "time", "day", "week", "month", "year", "period", "dt"]
        for hint in date_hints:
            for lower, orig in cols.items():
                if hint in lower:
                    try:
                        parsed = pd.to_datetime(df[orig], format="ISO8601", errors="coerce")
                        if parsed.notna().mean() > 0.7:
                            result["date"] = orig
                            break
                    except Exception:
                        pass
            if result["date"]:
                break

    # Sales/revenue detection — numeric column with sales-like name
    sales_hints = ["sales", "revenue", "amount", "total", "price", "gross",
                   "net", "income", "value", "turnover", "receipts", "billing"]
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    for hint in sales_hints:
        for lower, orig in cols.items():
            if hint in lower and orig in num_cols:
                result["sales"] = orig
                break
        if result["sales"]:
            break
    # Fallback: largest-mean numeric column
    if not result["sales"] and num_cols:
        result["sales"] = max(num_cols, key=lambda c: df[c].mean())

    # Quantity detection
    qty_hints = ["qty", "quantity", "units", "count", "volume", "sold", "orders", "items"]
    for hint in qty_hints:
        for lower, orig in cols.items():
            if hint in lower and orig in num_cols and orig != result["sales"]:
                result["quantity"] = orig
                break
        if result["quantity"]:
            break
    # Fallback: second largest-mean numeric
    if not result["quantity"] and len(num_cols) >= 2:
        remaining = [c for c in num_cols if c != result["sales"]]
        if remaining:
            result["quantity"] = max(remaining, key=lambda c: df[c].mean())

    # Product/category detection
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    product_hints = ["product", "item", "sku", "name", "category", "brand",
                     "model", "type", "segment", "line", "dept"]
    for hint in product_hints:
        for lower, orig in cols.items():
            if hint in lower and orig in cat_cols:
                result["product"] = orig
                break
        if result["product"]:
            break
    # Fallback: categorical column with 2–50 unique values
    if not result["product"]:
        for c in cat_cols:
            u = df[c].nunique()
            if 2 <= u <= 50:
                result["product"] = c
                break

    # Region/country/geography detection
    region_hints = ["country", "region", "state", "city", "location", "territory",
                    "market", "area", "zone", "geo", "province", "district"]
    for hint in region_hints:
        for lower, orig in cols.items():
            if hint in lower and orig in cat_cols and orig != result["product"]:
                result["region"] = orig
                break
        if result["region"]:
            break
    # Fallback: any remaining categorical with 2–80 unique values
    if not result["region"]:
        for c in cat_cols:
            if c == result["product"]:
                continue
            u = df[c].nunique()
            if 2 <= u <= 80:
                result["region"] = c
                break

    return result

PALETTE = [
    "#C2571A", "#E8845A", "#A04416", "#D4874E", "#7B3F1F",
    "#F0C9A0", "#5B8DB8", "#3A6B9F", "#8FC1E3", "#2D5A87",
    "#6BAE75", "#3D8B4A", "#A8D5B5", "#E8A0BF", "#C2678D",
]

BASE_LAYOUT = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor":  "rgba(0,0,0,0)",
    "font":          {"family": "Epilogue, sans-serif", "color": "#1C1712", "size": 12},
    "margin":        {"t": 48, "b": 48, "l": 48, "r": 24},
    "xaxis": {
        "gridcolor":    "#E8DDD0",
        "linecolor":    "#D9CEBC",
        "zeroline":     False,
        "showgrid":     True,
    },
    "yaxis": {
        "gridcolor":    "#E8DDD0",
        "linecolor":    "#D9CEBC",
        "zeroline":     False,
        "showgrid":     True,
    },
    "hoverlabel": {
        "bgcolor":      "#FFFFFF",
        "bordercolor":  "#E8DDD0",
        "font":         {"family": "Epilogue, sans-serif", "color": "#1C1712"},
    },
    "legend": {
        "bgcolor":      "rgba(255,255,255,0.85)",
        "bordercolor":  "#E8DDD0",
        "borderwidth":  1,
    },
    "colorway": PALETTE,
}

def _base_layout(title: str, extra: dict = None) -> dict:
    layout = {**BASE_LAYOUT, "title": {"text": title, "font": {"size": 15, "color": "#1C1712"}}}
    if extra:
        layout.update(extra)
    return layout

def _safe_float(val):
    """Convert numpy types to native Python float."""
    try:
        return float(val)
    except Exception:
        return 0.0

def _sanitize(obj):
    """Recursively convert numpy types to JSON-serializable Python types."""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(i) for i in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, pd.Timestamp):
        return str(obj)
    return obj

def build_sales_over_time(df: pd.DataFrame, cols: dict) -> dict:
    """
    Multi-series line chart. If product/region column exists, one line per group (top 8).
    Otherwise single line. X axis = date or index. Y axis = sales.
    """
    date_col  = cols.get("date")
    sales_col = cols.get("sales")
    group_col = cols.get("product") or cols.get("region")

    if not sales_col:
        return {}

    traces = []

    if date_col:
        try:
            df = df.copy()
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            df = df.dropna(subset=[date_col, sales_col])
            df = df.sort_values(date_col)
        except Exception:
            date_col = None

    if group_col and df[group_col].nunique() <= 12:
        top_groups = (
            df.groupby(group_col)[sales_col].sum()
            .nlargest(8).index.tolist()
        )
        for i, grp in enumerate(top_groups):
            sub = df[df[group_col] == grp]
            if date_col:
                agg = sub.groupby(date_col)[sales_col].sum().reset_index()
                x_vals = agg[date_col].astype(str).tolist()
                y_vals = agg[sales_col].tolist()
            else:
                x_vals = list(range(len(sub)))
                y_vals = sub[sales_col].tolist()

            traces.append({
                "type":   "scatter",
                "mode":   "lines+markers",
                "name":   str(grp),
                "x":      x_vals,
                "y":      y_vals,
                "line":   {"width": 2.5, "color": PALETTE[i % len(PALETTE)]},
                "marker": {"size": 5},
                "hovertemplate": f"<b>{grp}</b><br>%{{x}}<br>{sales_col}: %{{y:,.2f}}<extra></extra>",
            })
    else:
        # Single line
        if date_col:
            agg = df.groupby(date_col)[sales_col].sum().reset_index()
            x_vals = agg[date_col].astype(str).tolist()
            y_vals = agg[sales_col].tolist()
        else:
            sub = df[[sales_col]].dropna().head(300)
            x_vals = list(range(len(sub)))
            y_vals = sub[sales_col].tolist()

        traces.append({
            "type":   "scatter",
            "mode":   "lines+markers",
            "name":   sales_col,
            "x":      x_vals,
            "y":      y_vals,
            "fill":   "tozeroy",
            "fillcolor": "rgba(194,87,26,0.08)",
            "line":   {"width": 2.5, "color": "#C2571A"},
            "marker": {"size": 5, "color": "#C2571A"},
            "hovertemplate": "%{x}<br>" + sales_col + ": %{y:,.2f}<extra></extra>",
        })

    layout = _base_layout(
        f"{sales_col} over {'time' if date_col else 'index'}",
        {"showlegend": len(traces) > 1, "hovermode": "x unified"},
    )

    return _sanitize({"data": traces, "layout": layout})

def build_sales_by_product(df: pd.DataFrame, cols: dict) -> dict:
    sales_col   = cols.get("sales")
    product_col = cols.get("product")

    if not sales_col or not product_col:
        return {}

    agg = (
        df.groupby(product_col)[sales_col]
        .sum()
        .reset_index()
        .sort_values(sales_col, ascending=True)
        .tail(15)
    )

    colors = [PALETTE[i % len(PALETTE)] for i in range(len(agg))]

    trace = {
        "type":        "bar",
        "orientation": "h",
        "x":           agg[sales_col].tolist(),
        "y":           agg[product_col].astype(str).tolist(),
        "marker":      {"color": colors},
        "hovertemplate": "<b>%{y}</b><br>" + sales_col + ": %{x:,.2f}<extra></extra>",
        "text":        [f"{v:,.0f}" for v in agg[sales_col]],
        "textposition": "outside",
        "cliponaxis":  False,
    }

    layout = _base_layout(
        f"{sales_col} by {product_col}",
        {"showlegend": False, "xaxis": {**BASE_LAYOUT["xaxis"], "title": sales_col},
         "yaxis": {**BASE_LAYOUT["yaxis"], "title": product_col, "automargin": True}},
    )

    return _sanitize({"data": [trace], "layout": layout})

def build_sales_by_region(df: pd.DataFrame, cols: dict) -> dict:
    sales_col  = cols.get("sales")
    region_col = cols.get("region")

    if not sales_col or not region_col:
        return {}

    agg = (
        df.groupby(region_col)[sales_col]
        .sum()
        .reset_index()
        .sort_values(sales_col, ascending=False)
        .head(20)
    )

    # Detect if region column looks like ISO country names/codes
    country_hints = [
        "country", "nation", "iso", "country_code", "countrycode"
    ]
    col_lower = region_col.lower()
    looks_like_country = any(h in col_lower for h in country_hints)

    if looks_like_country:
        trace = {
            "type":        "choropleth",
            "locations":   agg[region_col].astype(str).tolist(),
            "z":           agg[sales_col].tolist(),
            "locationmode": "country names",
            "colorscale":  [
                [0.0,  "#FFF3EC"],
                [0.25, "#F0C9A0"],
                [0.5,  "#E8845A"],
                [0.75, "#C2571A"],
                [1.0,  "#7B3F1F"],
            ],
            "colorbar": {"title": sales_col, "thickness": 14},
            "hovertemplate": "<b>%{location}</b><br>" + sales_col + ": %{z:,.2f}<extra></extra>",
        }
        layout = _base_layout(
            f"{sales_col} by {region_col}",
            {
                "geo": {
                    "showframe":    False,
                    "showcoastlines": True,
                    "coastlinecolor": "#E8DDD0",
                    "showland":     True,
                    "landcolor":    "#FAF7F2",
                    "showocean":    True,
                    "oceancolor":   "#EDF5FB",
                    "projection":   {"type": "natural earth"},
                },
                "showlegend": False,
            },
        )
        # Remove standard xaxis/yaxis from geo layout
        layout.pop("xaxis", None)
        layout.pop("yaxis", None)
    else:
        # Donut chart
        colors = [PALETTE[i % len(PALETTE)] for i in range(len(agg))]
        trace = {
            "type":        "pie",
            "labels":      agg[region_col].astype(str).tolist(),
            "values":      agg[sales_col].tolist(),
            "hole":        0.42,
            "marker":      {"colors": colors, "line": {"color": "#FFFFFF", "width": 2}},
            "hovertemplate": "<b>%{label}</b><br>" + sales_col + ": %{value:,.2f}<br>%{percent}<extra></extra>",
            "textinfo":    "label+percent",
            "textfont":    {"size": 11},
        }
        layout = _base_layout(
            f"{sales_col} by {region_col}",
            {"showlegend": True},
        )
        layout.pop("xaxis", None)
        layout.pop("yaxis", None)

    return _sanitize({"data": [trace], "layout": layout})

def build_sales_vs_quantity(df: pd.DataFrame, cols: dict) -> dict:
    sales_col = cols.get("sales")
    qty_col   = cols.get("quantity")
    color_col = cols.get("product") or cols.get("region")

    if not sales_col or not qty_col:
        return {}

    sub = df[[sales_col, qty_col] + ([color_col] if color_col else [])].dropna().head(800)

    traces = []
    if color_col and sub[color_col].nunique() <= 15:
        groups = sub[color_col].unique()
        for i, grp in enumerate(groups):
            g = sub[sub[color_col] == grp]
            traces.append({
                "type":   "scatter",
                "mode":   "markers",
                "name":   str(grp),
                "x":      g[qty_col].tolist(),
                "y":      g[sales_col].tolist(),
                "marker": {
                    "color":   PALETTE[i % len(PALETTE)],
                    "size":    9,
                    "opacity": 0.75,
                    "line":    {"color": "#FFFFFF", "width": 0.8},
                },
                "hovertemplate": (
                    f"<b>{grp}</b><br>"
                    f"{qty_col}: %{{x:,.2f}}<br>"
                    f"{sales_col}: %{{y:,.2f}}<extra></extra>"
                ),
            })
    else:
        traces.append({
            "type":   "scatter",
            "mode":   "markers",
            "name":   f"{sales_col} vs {qty_col}",
            "x":      sub[qty_col].tolist(),
            "y":      sub[sales_col].tolist(),
            "marker": {
                "color":   "#C2571A",
                "size":    8,
                "opacity": 0.65,
                "line":    {"color": "#FFFFFF", "width": 0.6},
            },
            "hovertemplate": (
                f"{qty_col}: %{{x:,.2f}}<br>"
                f"{sales_col}: %{{y:,.2f}}<extra></extra>"
            ),
        })

    layout = _base_layout(
        f"{sales_col} vs {qty_col}",
        {
            "showlegend": len(traces) > 1,
            "xaxis": {**BASE_LAYOUT["xaxis"], "title": qty_col},
            "yaxis": {**BASE_LAYOUT["yaxis"], "title": sales_col},
        },
    )

    return _sanitize({"data": traces, "layout": layout})

def build_period_heatmap(df: pd.DataFrame, cols: dict) -> dict:
    """
    If date and sales columns exist, build a month × year heatmap of total sales.
    Falls back to a product × region heatmap if no date column.
    """
    sales_col = cols.get("sales")
    date_col  = cols.get("date")
    prod_col  = cols.get("product")
    reg_col   = cols.get("region")

    if not sales_col:
        return {}

    if date_col:
        try:
            df = df.copy()
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            df = df.dropna(subset=[date_col, sales_col])
            df["_month"] = df[date_col].dt.strftime("%b")
            df["_year"]  = df[date_col].dt.year.astype(str)

            pivot = df.pivot_table(
                index="_month", columns="_year",
                values=sales_col, aggfunc="sum", fill_value=0
            )
            month_order = ["Jan","Feb","Mar","Apr","May","Jun",
                           "Jul","Aug","Sep","Oct","Nov","Dec"]
            pivot = pivot.reindex([m for m in month_order if m in pivot.index])

            trace = {
                "type":        "heatmap",
                "x":           pivot.columns.tolist(),
                "y":           pivot.index.tolist(),
                "z":           pivot.values.tolist(),
                "colorscale":  [
                    [0.0, "#FFF3EC"], [0.5, "#E8845A"], [1.0, "#7B3F1F"]
                ],
                "hovertemplate": "%{y} %{x}<br>" + sales_col + ": %{z:,.2f}<extra></extra>",
                "colorbar":    {"title": sales_col, "thickness": 14},
            }
            layout = _base_layout(
                f"{sales_col} — Month × Year Heatmap",
                {"showlegend": False},
            )
            layout.pop("xaxis", None)
            layout.pop("yaxis", None)
            return _sanitize({"data": [trace], "layout": layout})
        except Exception:
            pass

    # Fallback — product × region pivot
    if prod_col and reg_col:
        pivot = df.pivot_table(
            index=prod_col, columns=reg_col,
            values=sales_col, aggfunc="sum", fill_value=0
        )
        pivot = pivot.iloc[:12, :12]
        trace = {
            "type":        "heatmap",
            "x":           [str(c) for c in pivot.columns],
            "y":           [str(r) for r in pivot.index],
            "z":           pivot.values.tolist(),
            "colorscale":  [
                [0.0, "#EDF5FB"], [0.5, "#5B8DB8"], [1.0, "#2D5A87"]
            ],
            "hovertemplate": "%{y} / %{x}<br>" + sales_col + ": %{z:,.2f}<extra></extra>",
            "colorbar":    {"title": sales_col, "thickness": 14},
        }
        layout = _base_layout(
            f"{sales_col} — {prod_col} × {reg_col}",
            {"showlegend": False},
        )
        layout.pop("xaxis", None)
        layout.pop("yaxis", None)
        return _sanitize({"data": [trace], "layout": layout})

    return {}

def build_top_n_animated(df: pd.DataFrame, cols: dict) -> dict:
    """
    Animated bar chart showing top N products/regions across time periods.
    If no date column, static top-15 bar chart with value labels.
    """
    sales_col   = cols.get("sales")
    product_col = cols.get("product") or cols.get("region")
    date_col    = cols.get("date")

    if not sales_col or not product_col:
        return {}

    if date_col:
        try:
            df = df.copy()
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            df = df.dropna(subset=[date_col, sales_col, product_col])
            df["_period"] = df[date_col].dt.to_period("M").astype(str)
            periods = sorted(df["_period"].unique())[-24:]  # last 24 periods

            frames = []
            for period in periods:
                sub = (
                    df[df["_period"] == period]
                    .groupby(product_col)[sales_col]
                    .sum()
                    .nlargest(10)
                    .reset_index()
                    .sort_values(sales_col, ascending=True)
                )
                frames.append({
                    "name": period,
                    "data": [{
                        "x":           sub[sales_col].tolist(),
                        "y":           sub[product_col].astype(str).tolist(),
                        "marker":      {"color": PALETTE[:len(sub)]},
                    }],
                    "layout": {"title": {"text": f"Top {product_col} — {period}"}},
                })

            # Initial frame
            first = df[df["_period"] == periods[0]].groupby(product_col)[sales_col].sum().nlargest(10).reset_index().sort_values(sales_col, ascending=True)
            trace = {
                "type":        "bar",
                "orientation": "h",
                "x":           first[sales_col].tolist(),
                "y":           first[product_col].astype(str).tolist(),
                "marker":      {"color": PALETTE[:len(first)]},
            }

            layout = _base_layout(
                f"Top {product_col} by {sales_col}",
                {
                    "showlegend": False,
                    "updatemenus": [{
                        "type":       "buttons",
                        "showactive": False,
                        "y":          1.15,
                        "x":          0.0,
                        "buttons": [{
                            "label":  "▶ Play",
                            "method": "animate",
                            "args":   [None, {
                                "frame":      {"duration": 600, "redraw": True},
                                "fromcurrent": True,
                                "transition": {"duration": 400},
                            }],
                        }, {
                            "label":  "⏸ Pause",
                            "method": "animate",
                            "args":   [[None], {
                                "frame":      {"duration": 0, "redraw": False},
                                "mode":       "immediate",
                                "transition": {"duration": 0},
                            }],
                        }],
                    }],
                    "sliders": [{
                        "steps": [{"args": [[p], {"frame": {"duration": 600}, "mode": "immediate"}],
                                   "label": p, "method": "animate"} for p in periods],
                        "transition": {"duration": 400},
                        "x": 0.05, "len": 0.9,
                        "currentvalue": {"prefix": "Period: ", "visible": True, "xanchor": "center"},
                    }],
                },
            )

            return _sanitize({"data": [trace], "layout": layout, "frames": frames})
        except Exception:
            pass

    # Static fallback
    agg = (
        df.groupby(product_col)[sales_col]
        .sum()
        .nlargest(15)
        .reset_index()
        .sort_values(sales_col, ascending=True)
    )
    trace = {
        "type":        "bar",
        "orientation": "h",
        "x":           agg[sales_col].tolist(),
        "y":           agg[product_col].astype(str).tolist(),
        "marker":      {"color": [PALETTE[i % len(PALETTE)] for i in range(len(agg))]},
        "text":        [f"{v:,.0f}" for v in agg[sales_col]],
        "textposition": "outside",
        "hovertemplate": "<b>%{y}</b><br>" + sales_col + ": %{x:,.2f}<extra></extra>",
    }
    layout = _base_layout(
        f"Top 15 {product_col} by {sales_col}",
        {"showlegend": False, "yaxis": {**BASE_LAYOUT["yaxis"], "automargin": True}},
    )

    return _sanitize({"data": [trace], "layout": layout})

def build_waterfall_or_funnel(df: pd.DataFrame, cols: dict) -> dict:
    """
    If both sales and quantity exist, build a waterfall of sales contribution by product.
    Otherwise build a funnel of top categories by value.
    """
    sales_col   = cols.get("sales")
    product_col = cols.get("product") or cols.get("region")

    if not sales_col or not product_col:
        return {}

    agg = (
        df.groupby(product_col)[sales_col]
        .sum()
        .reset_index()
        .sort_values(sales_col, ascending=False)
        .head(10)
    )

    total = agg[sales_col].sum()
    measures = ["relative"] * len(agg) + ["total"]
    x_vals   = agg[product_col].astype(str).tolist() + ["Total"]
    y_vals   = agg[sales_col].tolist() + [total]

    trace = {
        "type":        "waterfall",
        "orientation": "v",
        "measure":     measures,
        "x":           x_vals,
        "y":           y_vals,
        "connector":   {"line": {"color": "#E8DDD0", "width": 1}},
        "increasing":  {"marker": {"color": "#6BAE75"}},
        "totals":      {"marker": {"color": "#C2571A"}},
        "hovertemplate": "<b>%{x}</b><br>" + sales_col + ": %{y:,.2f}<extra></extra>",
        "text":        [f"{v:,.0f}" for v in y_vals],
        "textposition": "outside",
    }

    layout = _base_layout(
        f"{sales_col} contribution by {product_col}",
        {"showlegend": False, "xaxis": {**BASE_LAYOUT["xaxis"], "automargin": True}},
    )

    return _sanitize({"data": [trace], "layout": layout})

def build_cumulative_growth(df: pd.DataFrame, cols: dict) -> dict:
    sales_col = cols.get("sales")
    date_col  = cols.get("date")
    prod_col  = cols.get("product")

    if not sales_col:
        return {}

    traces = []

    if date_col and prod_col and df[prod_col].nunique() <= 6:
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col, sales_col])
        df = df.sort_values(date_col)

        for i, grp in enumerate(df[prod_col].unique()[:6]):
            sub = df[df[prod_col] == grp].groupby(date_col)[sales_col].sum().cumsum().reset_index()
            traces.append({
                "type":      "scatter",
                "mode":      "lines",
                "name":      str(grp),
                "x":         sub[date_col].astype(str).tolist(),
                "y":         sub[sales_col].tolist(),
                "fill":      "tonexty" if i > 0 else "tozeroy",
                "fillcolor": f"rgba({int(PALETTE[i % len(PALETTE)][1:3], 16)},"
                             f"{int(PALETTE[i % len(PALETTE)][3:5], 16)},"
                             f"{int(PALETTE[i % len(PALETTE)][5:7], 16)},0.15)",
                "line":      {"color": PALETTE[i % len(PALETTE)], "width": 2},
                "hovertemplate": f"<b>{grp}</b><br>%{{x}}<br>Cumulative: %{{y:,.2f}}<extra></extra>",
            })

    elif date_col:
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col, sales_col])
        agg = df.groupby(date_col)[sales_col].sum().cumsum().reset_index()
        traces.append({
            "type":      "scatter",
            "mode":      "lines",
            "name":      f"Cumulative {sales_col}",
            "x":         agg[date_col].astype(str).tolist(),
            "y":         agg[sales_col].tolist(),
            "fill":      "tozeroy",
            "fillcolor": "rgba(194,87,26,0.10)",
            "line":      {"color": "#C2571A", "width": 2.5},
            "hovertemplate": "%{x}<br>Cumulative: %{y:,.2f}<extra></extra>",
        })
    else:
        return {}

    layout = _base_layout(
        f"Cumulative {sales_col}",
        {"showlegend": len(traces) > 1, "hovermode": "x unified"},
    )
    return _sanitize({"data": traces, "layout": layout})

def build_dashboard_kpis(df: pd.DataFrame, cols: dict) -> dict:
    """
    Returns a dict of KPI cards to display above the charts.
    All values are native Python types.
    """
    kpis = {}
    sales_col = cols.get("sales")
    qty_col   = cols.get("quantity")
    prod_col  = cols.get("product")
    reg_col   = cols.get("region")
    date_col  = cols.get("date")

    if sales_col:
        total = float(df[sales_col].sum())
        avg   = float(df[sales_col].mean())
        mx    = float(df[sales_col].max())
        kpis["total_sales"]   = {"value": total,  "label": f"Total {sales_col}",   "format": "currency"}
        kpis["avg_sales"]     = {"value": avg,    "label": f"Avg {sales_col}",      "format": "currency"}
        kpis["peak_sales"]    = {"value": mx,     "label": f"Peak {sales_col}",     "format": "currency"}

    if qty_col:
        kpis["total_quantity"] = {"value": float(df[qty_col].sum()), "label": f"Total {qty_col}", "format": "number"}

    if prod_col:
        top_product = df.groupby(prod_col)[sales_col].sum().idxmax() if sales_col else df[prod_col].mode()[0]
        kpis["top_product"] = {"value": str(top_product), "label": f"Top {prod_col}", "format": "text"}

    if reg_col:
        top_region = df.groupby(reg_col)[sales_col].sum().idxmax() if sales_col else df[reg_col].mode()[0]
        kpis["top_region"] = {"value": str(top_region), "label": f"Top {reg_col}", "format": "text"}

    if date_col:
        try:
            df2 = df.copy()
            df2[date_col] = pd.to_datetime(df2[date_col], errors="coerce")
            date_range = f"{df2[date_col].min().strftime('%d %b %Y')} – {df2[date_col].max().strftime('%d %b %Y')}"
            kpis["date_range"] = {"value": date_range, "label": "Date range", "format": "text"}
        except Exception:
            pass

    return kpis

def build_dashboard(rows: list, file_name: str) -> dict:
    """
    Entry point. Takes cleaned_rows list, returns full dashboard payload:
    { "kpis": {...}, "charts": {...}, "detected_cols": {...}, "file_name": str }
    """
    if not rows:
        return {"kpis": {}, "charts": {}, "detected_cols": {}, "file_name": file_name}

    df   = pd.DataFrame(rows)
    cols = detect_dashboard_columns(df)

    charts = {}
    builders = [
        ("sales_over_time",    build_sales_over_time),
        ("sales_by_product",   build_sales_by_product),
        ("sales_by_region",    build_sales_by_region),
        ("sales_vs_quantity",  build_sales_vs_quantity),
        ("period_heatmap",     build_period_heatmap),
        ("top_n_animated",     build_top_n_animated),
        ("waterfall",          build_waterfall_or_funnel),
        ("cumulative_growth",  build_cumulative_growth),
    ]

    for name, fn in builders:
        try:
            result = fn(df, cols)
            if result and result.get("data"):
                charts[name] = result
        except Exception:
            pass

    kpis = build_dashboard_kpis(df, cols)

    return {
        "kpis":          kpis,
        "charts":        charts,
        "detected_cols": {k: v for k, v in cols.items() if v},
        "file_name":     file_name,
    }

def generate_pbix(rows: list, file_name: str, cols: dict) -> bytes:
    """
    Generates a minimal .pbix binary that Power BI Desktop can open.
    Contains the cleaned dataset as a CSV inside the DataModel,
    and a single report page with 4 pre-configured visuals.
    """
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:

        # ── [Content_Types].xml ──────────────────────────────────────────
        content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="json" ContentType="application/json"/>
  <Default Extension="xml"  ContentType="application/xml"/>
  <Override PartName="/DataModel" ContentType="application/vnd.ms-pbi.datamodel"/>
  <Override PartName="/Report/Layout" ContentType="application/json"/>
</Types>"""
        zf.writestr("[Content_Types].xml", content_types)

        # ── _rels/.rels ──────────────────────────────────────────────────
        rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.microsoft.com/powerbi/2016/report" Target="Report/Layout"/>
  <Relationship Id="rId2" Type="http://schemas.microsoft.com/powerbi/2016/datamodel" Target="DataModel"/>
</Relationships>"""
        zf.writestr("_rels/.rels", rels)

        # ── DataModel (CSV embedded as UTF-8) ───────────────────────────
        df = pd.DataFrame(rows)
        csv_data = df.to_csv(index=False).encode("utf-8")
        zf.writestr("DataModel", csv_data)

        # ── Version ─────────────────────────────────────────────────────
        zf.writestr("Version", "2.128.0.0")

        # ── Report/Layout (JSON) ─────────────────────────────────────────
        sales_col   = cols.get("sales", "")
        qty_col     = cols.get("quantity", "")
        product_col = cols.get("product", "")
        region_col  = cols.get("region", "")
        date_col    = cols.get("date", "")
        table_name  = file_name.rsplit(".", 1)[0].replace(" ", "_") or "DataLens"

        def col_ref(col):
            if not col:
                return {}
            return {
                "Column": {
                    "Expression": {"SourceRef": {"Entity": table_name}},
                    "Property":   col,
                }
            }

        def measure_ref(col, agg="Sum"):
            if not col:
                return {}
            return {
                "Aggregation": {
                    "Expression": col_ref(col),
                    "Function":   0,  # 0 = Sum
                }
            }

        visuals = []

        # Visual 1 — Line chart: Sales over Time
        if date_col and sales_col:
            visuals.append({
                "id":   1,
                "type": "lineChart",
                "name": f"{sales_col} over time",
                "x": 0, "y": 0, "width": 360, "height": 250,
                "dataRoles": {
                    "Category": [col_ref(date_col)],
                    "Y":        [measure_ref(sales_col)],
                    "Series":   ([col_ref(product_col)] if product_col else []),
                },
            })

        # Visual 2 — Bar chart: Sales by Product
        if product_col and sales_col:
            visuals.append({
                "id":   2,
                "type": "barChart",
                "name": f"{sales_col} by {product_col}",
                "x": 380, "y": 0, "width": 360, "height": 250,
                "dataRoles": {
                    "Category": [col_ref(product_col)],
                    "Y":        [measure_ref(sales_col)],
                },
            })

        # Visual 3 — Pie/map: Sales by Region
        if region_col and sales_col:
            visuals.append({
                "id":   3,
                "type": "pieChart",
                "name": f"{sales_col} by {region_col}",
                "x": 0, "y": 270, "width": 360, "height": 250,
                "dataRoles": {
                    "Category": [col_ref(region_col)],
                    "Y":        [measure_ref(sales_col)],
                },
            })

        # Visual 4 — Scatter: Sales vs Quantity
        if sales_col and qty_col:
            visuals.append({
                "id":   4,
                "type": "scatterChart",
                "name": f"{sales_col} vs {qty_col}",
                "x": 380, "y": 270, "width": 360, "height": 250,
                "dataRoles": {
                    "X":        [measure_ref(qty_col)],
                    "Y":        [measure_ref(sales_col)],
                    "Details":  ([col_ref(product_col or region_col)] if (product_col or region_col) else []),
                },
            })

        layout = {
            "id":      1,
            "name":    "DataLens Dashboard",
            "width":   1280,
            "height":  720,
            "config":  "{}",
            "filters": "[]",
            "sections": [{
                "id":       1,
                "name":     "Dashboard",
                "width":    1280,
                "height":   720,
                "visualContainers": [
                    {
                        "id":     v["id"],
                        "x":      v["x"],
                        "y":      v["y"],
                        "width":  v["width"],
                        "height": v["height"],
                        "config": json.dumps({
                            "name":    v["name"],
                            "layouts": [{"id": 0, "position": {
                                "x": v["x"], "y": v["y"],
                                "width": v["width"], "height": v["height"],
                                "tabOrder": v["id"],
                            }}],
                            "singleVisual": {
                                "visualType": v["type"],
                                "projections": v["dataRoles"],
                                "prototypeQuery": {
                                    "Version": 2,
                                    "From": [{"Name": table_name, "Entity": table_name, "Type": 0}],
                                    "Select": [],
                                },
                            },
                        }),
                        "filters": "[]",
                    }
                    for v in visuals
                ],
            }],
            "datasetId":   "",
            "reportId":    "",
            "resourcePackages": [],
        }

        zf.writestr("Report/Layout", json.dumps(layout, ensure_ascii=False))

        # ── Report/_rels/Layout.rels ─────────────────────────────────────
        layout_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>"""
        zf.writestr("Report/_rels/Layout.rels", layout_rels)

    return buf.getvalue()
