// src/components/dashboard/KPICards.jsx
import React from "react";
import { Database, AlertTriangle, Layers, Copy, Cpu, TrendingUp } from "lucide-react";

function KPI({ icon: Icon, label, value, sub, color = "cyan" }) {
  return (
    <div className="glass rounded-2xl p-4 flex items-center gap-3">
      <div className={`badge-${color} w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0`}>
        <Icon size={16} />
      </div>
      <div className="min-w-0">
        <div className="font-display font-bold text-lg text-white leading-tight">{value}</div>
        <div className="text-xs text-slate-500 font-body truncate">{label}</div>
        {sub && <div className="text-xs text-slate-600 font-body">{sub}</div>}
      </div>
    </div>
  );
}

export default function KPICards({ summary }) {
  if (!summary) return null;
  const {
    rows = 0, cols = 0, null_total = 0,
    duplicate_rows = 0, memory_kb = 0,
    columns = []
  } = summary;

  const numericCols = columns.filter(c =>
    ["int64","float64","int32","float32"].some(t => c.dtype?.includes(t))
  ).length;

  const nullPct = rows > 0
    ? ((null_total / (rows * cols)) * 100).toFixed(1)
    : 0;

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
      <KPI icon={Database}      label="Total rows"       value={rows.toLocaleString()}      color="cyan"   />
      <KPI icon={Layers}        label="Columns"          value={cols}                        color="violet" />
      <KPI icon={AlertTriangle} label="Missing values"   value={null_total.toLocaleString()} sub={`${nullPct}%`} color="amber" />
      <KPI icon={Copy}          label="Duplicate rows"   value={duplicate_rows}              color="coral"  />
      <KPI icon={Cpu}           label="Numeric columns"  value={numericCols}                 color="green"  />
      <KPI icon={TrendingUp}    label="Memory"           value={`${memory_kb} KB`}           color="cyan"   />
    </div>
  );
}
