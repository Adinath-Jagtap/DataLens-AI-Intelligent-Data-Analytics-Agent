// src/components/charts/ChartCard.jsx
import React, { useEffect, useRef } from "react";
import { Download, Maximize2 } from "lucide-react";

const DARK_LAYOUT = {
  paper_bgcolor: "transparent",
  plot_bgcolor:  "transparent",
  font:          { family: "'DM Sans', sans-serif", color: "#94a3b8", size: 11 },
  margin:        { t: 10, r: 10, b: 40, l: 50 },
  xaxis: { gridcolor: "rgba(255,255,255,0.05)", zerolinecolor: "rgba(255,255,255,0.08)", tickfont: { size: 10 } },
  yaxis: { gridcolor: "rgba(255,255,255,0.05)", zerolinecolor: "rgba(255,255,255,0.08)", tickfont: { size: 10 } },
  legend: { bgcolor: "transparent", font: { color: "#94a3b8" } },
  colorway: ["#22d3ee","#a78bfa","#fbbf24","#34d399","#fb7185","#38bdf8","#f97316","#e879f9"],
};

function buildTrace(data) {
  const color = data.color || "#22d3ee";

  switch (data.type) {
    case "bar":
      return [{ type: "bar", x: data.x, y: data.y,
                marker: { color, opacity: 0.85, line: { width: 0 } } }];

    case "line":
    case "area":
      return [{ type: "scatter", mode: "lines", x: data.x, y: data.y,
                line: { color, width: 2, shape: "spline" },
                fill: data.type === "area" ? "tozeroy" : "none",
                fillcolor: `${color}18` }];

    case "scatter":
      return [{ type: "scatter", mode: "markers", x: data.x, y: data.y,
                marker: { color, size: 6, opacity: 0.7 } }];

    case "pie":
      return [{ type: "pie", labels: data.labels, values: data.values,
                hole: 0.35,
                marker: { colors: ["#22d3ee","#a78bfa","#fbbf24","#34d399","#fb7185","#38bdf8","#f97316","#e879f9"] },
                textinfo: "percent", textfont: { color: "#e2e8f0" } }];

    case "histogram":
      return [{ type: "histogram", x: data.values,
                marker: { color, opacity: 0.8 },
                xbins: { size: (Math.max(...data.values) - Math.min(...data.values)) / 20 } }];

    case "box":
      return [{ type: "box", y: data.values, name: data.label || "",
                marker: { color }, boxmean: true }];

    case "heatmap":
      return [{ type: "heatmap", z: data.z, x: data.x, y: data.y,
                colorscale: [["0","#0f1726"],["0.5","#0ea5e9"],["1","#22d3ee"]],
                showscale: true }];

    default:
      return [{ type: "bar", x: data.x || [], y: data.y || [],
                marker: { color } }];
  }
}

export default function ChartCard({ data, title, description, onExpand }) {
  const plotRef = useRef(null);
  const divRef  = useRef(null);

  useEffect(() => {
    if (!divRef.current || !data || data.error) return;

    const traces = buildTrace(data);
    const layout = {
      ...DARK_LAYOUT,
      title: { text: "", font: { size: 13 } },
    };

    if (window.Plotly) {
      window.Plotly.newPlot(divRef.current, traces, layout, {
        responsive:     true,
        displaylogo:    false,
        modeBarButtonsToRemove: ["select2d","lasso2d","autoScale2d"],
      });
      plotRef.current = divRef.current;
    }

    return () => {
      if (plotRef.current && window.Plotly) {
        try { window.Plotly.purge(plotRef.current); } catch {}
      }
    };
  }, [data]);

  const downloadPNG = () => {
    if (!plotRef.current || !window.Plotly) return;
    window.Plotly.downloadImage(plotRef.current, {
      format: "png", width: 1200, height: 600,
      filename: (title || "chart").replace(/\s+/g, "_"),
    });
  };

  return (
    <div className="glass rounded-2xl overflow-hidden">
      {/* Card header */}
      <div className="flex items-start justify-between px-4 pt-4 pb-2">
        <div>
          <h3 className="font-display font-semibold text-sm text-white leading-tight">{title}</h3>
          {description && (
            <p className="text-xs text-slate-500 font-body mt-0.5 leading-relaxed">{description}</p>
          )}
        </div>
        <div className="flex items-center gap-1 ml-2 flex-shrink-0">
          <button onClick={downloadPNG}
                  className="p-1.5 rounded-lg hover:bg-surface-3 text-slate-500 hover:text-slate-300 transition-colors"
                  title="Download PNG">
            <Download size={13} />
          </button>
          {onExpand && (
            <button onClick={onExpand}
                    className="p-1.5 rounded-lg hover:bg-surface-3 text-slate-500 hover:text-slate-300 transition-colors"
                    title="Expand">
              <Maximize2 size={13} />
            </button>
          )}
        </div>
      </div>

      {/* Chart */}
      {data?.error ? (
        <div className="h-48 flex items-center justify-center text-slate-600 text-sm font-body">
          Could not render chart
        </div>
      ) : (
        <div ref={divRef} className="w-full" style={{ height: 240 }} />
      )}
    </div>
  );
}
