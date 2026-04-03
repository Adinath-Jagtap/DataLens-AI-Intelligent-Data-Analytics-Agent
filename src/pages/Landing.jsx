// src/pages/Landing.jsx
import React, { useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { BarChart2, Zap, Brain, Shield, ArrowRight, Database, TrendingUp, MessageSquare } from "lucide-react";

const FEATURES = [
  { icon: Database,      color: "cyan",   title: "Upload any dataset",   desc: "CSV or Excel. Drag, drop, done. Supports up to 50 MB." },
  { icon: Brain,         color: "violet", title: "AI cleans your data",  desc: "Groq AI detects issues, fills nulls, removes outliers automatically." },
  { icon: BarChart2,     color: "amber",  title: "10+ smart charts",     desc: "Auto-generated visualisations chosen by AI for your specific data." },
  { icon: TrendingUp,    color: "green",  title: "Interactive dashboard",desc: "Filter, drill down, and explore with real-time controls." },
  { icon: MessageSquare, color: "coral",  title: "Chat with your data",  desc: "Ask questions in plain English. AI answers with numbers and insights." },
  { icon: Shield,        color: "cyan",   title: "Saved forever",        desc: "Every analysis, chart, and chat is saved to your profile." },
];

const STATS = [
  { value: "10+",  label: "Chart types" },
  { value: "~5s",  label: "Processing time" },
  { value: "100%", label: "Free, always" },
  { value: "0",    label: "Servers needed" },
];

export default function Landing() {
  const canvasRef = useRef(null);

  // Animated particle grid background
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx    = canvas.getContext("2d");
    let   frame  = 0;
    const dots   = Array.from({ length: 60 }, () => ({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      r: Math.random() * 1.5 + 0.3,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
    }));

    const resize = () => { canvas.width = window.innerWidth; canvas.height = window.innerHeight; };
    resize();
    window.addEventListener("resize", resize);

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      dots.forEach(d => {
        d.x += d.vx; d.y += d.vy;
        if (d.x < 0 || d.x > canvas.width)  d.vx *= -1;
        if (d.y < 0 || d.y > canvas.height) d.vy *= -1;
        ctx.beginPath();
        ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(34,211,238,0.25)";
        ctx.fill();
      });
      // Draw connections
      dots.forEach((a, i) => {
        dots.slice(i + 1).forEach(b => {
          const dist = Math.hypot(a.x - b.x, a.y - b.y);
          if (dist < 120) {
            ctx.beginPath();
            ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
            ctx.strokeStyle = `rgba(34,211,238,${0.06 * (1 - dist / 120)})`;
            ctx.lineWidth   = 0.5;
            ctx.stroke();
          }
        });
      });
      frame = requestAnimationFrame(draw);
    };
    draw();
    return () => { cancelAnimationFrame(frame); window.removeEventListener("resize", resize); };
  }, []);

  return (
    <div className="min-h-screen bg-surface-0 overflow-hidden">
      {/* Animated background */}
      <canvas ref={canvasRef} className="fixed inset-0 pointer-events-none opacity-60" />

      {/* Glow blobs */}
      <div className="fixed top-1/4 left-1/4 w-96 h-96 rounded-full pointer-events-none"
           style={{ background: "radial-gradient(circle, rgba(34,211,238,0.06) 0%, transparent 70%)" }} />
      <div className="fixed bottom-1/3 right-1/4 w-80 h-80 rounded-full pointer-events-none"
           style={{ background: "radial-gradient(circle, rgba(167,139,250,0.06) 0%, transparent 70%)" }} />

      {/* Nav */}
      <nav className="relative z-10 flex items-center justify-between px-8 py-5 max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg flex items-center justify-center"
               style={{ background: "linear-gradient(135deg,#0ea5e9,#22d3ee)" }}>
            <BarChart2 size={16} className="text-surface-0" />
          </div>
          <span className="font-display font-bold text-white text-lg tracking-tight">DataLens AI</span>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/login"  className="btn-secondary text-sm">Sign in</Link>
          <Link to="/signup" className="btn-primary text-sm">Get started free</Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative z-10 text-center px-6 pt-24 pb-20 max-w-5xl mx-auto">
        <div className="badge badge-cyan mb-6 mx-auto">
          <Zap size={10} /> Powered by Groq · Runs in your browser
        </div>
        <h1 className="font-display font-extrabold text-5xl md:text-7xl leading-tight mb-6"
            style={{ letterSpacing: "-0.03em" }}>
          <span className="text-white">Turn raw data into</span>
          <br />
          <span className="gradient-text">expert insights</span>
        </h1>
        <p className="font-body text-slate-400 text-lg md:text-xl max-w-2xl mx-auto mb-10 leading-relaxed">
          Upload your CSV or Excel file. DataLens AI cleans it, generates professional charts,
          builds an interactive dashboard, and lets you chat with your data — all in seconds.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link to="/signup" className="btn-primary text-base px-7 py-3">
            Start analysing free <ArrowRight size={16} />
          </Link>
          <Link to="/login" className="btn-secondary text-base px-7 py-3">
            Sign in
          </Link>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-20">
          {STATS.map(s => (
            <div key={s.label} className="glass rounded-2xl py-5 px-4">
              <div className="font-display font-bold text-3xl gradient-text mb-1">{s.value}</div>
              <div className="font-body text-sm text-slate-500">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="relative z-10 px-6 pb-24 max-w-6xl mx-auto">
        <h2 className="section-heading text-3xl md:text-4xl text-center mb-3">Everything you need</h2>
        <p className="text-slate-500 text-center mb-12 font-body">No code. No server. No cost.</p>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map(f => (
            <div key={f.title} className="glass glass-hover rounded-2xl p-6">
              <div className={`badge badge-${f.color} mb-4`}>
                <f.icon size={12} />
              </div>
              <h3 className="font-display font-semibold text-white text-lg mb-2">{f.title}</h3>
              <p className="font-body text-sm text-slate-400 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA footer */}
      <section className="relative z-10 text-center px-6 pb-24">
        <div className="glass rounded-3xl max-w-2xl mx-auto p-12">
          <h2 className="section-heading text-3xl mb-4">Ready to see your data differently?</h2>
          <p className="text-slate-400 font-body mb-8">Free forever. No credit card needed.</p>
          <Link to="/signup" className="btn-primary text-base px-8 py-3 mx-auto">
            Create free account <ArrowRight size={16} />
          </Link>
        </div>
      </section>
    </div>
  );
}
