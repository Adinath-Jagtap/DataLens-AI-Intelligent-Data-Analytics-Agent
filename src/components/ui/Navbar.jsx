// src/components/ui/Navbar.jsx
import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { BarChart2, Home, Upload, History, User, LogOut, Menu, X } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import toast from "react-hot-toast";

const NAV_LINKS = [
  { to: "/home",    icon: Home,    label: "Home"    },
  { to: "/upload",  icon: Upload,  label: "Upload"  },
  { to: "/history", icon: History, label: "History" },
  { to: "/profile", icon: User,    label: "Profile" },
];

export default function Navbar() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate  = useNavigate();
  const [open, setOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    toast.success("Signed out");
    navigate("/", { replace: true });
  };

  return (
    <nav className="sticky top-0 z-50 glass border-b border-white/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between h-14">
        {/* Logo */}
        <Link to="/home" className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg flex items-center justify-center"
               style={{ background: "linear-gradient(135deg,#0ea5e9,#22d3ee)" }}>
            <BarChart2 size={14} className="text-surface-0" />
          </div>
          <span className="font-display font-bold text-white text-base">DataLens AI</span>
        </Link>

        {/* Desktop links */}
        <div className="hidden md:flex items-center gap-1">
          {NAV_LINKS.map(({ to, icon: Icon, label }) => (
            <Link key={to} to={to}
                  className={`nav-link flex items-center gap-1.5 ${location.pathname === to ? "active" : ""}`}>
              <Icon size={14} /> {label}
            </Link>
          ))}
        </div>

        {/* Right side */}
        <div className="hidden md:flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-2">
            <div className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold"
                 style={{ background: "linear-gradient(135deg,#0ea5e9,#a78bfa)" }}>
              {user?.displayName?.[0]?.toUpperCase() || "U"}
            </div>
            <span className="text-slate-300 text-xs font-body max-w-[120px] truncate">
              {user?.displayName || user?.email}
            </span>
          </div>
          <button onClick={handleLogout} className="btn-secondary py-1.5 px-3 text-xs">
            <LogOut size={13} /> Sign out
          </button>
        </div>

        {/* Mobile hamburger */}
        <button className="md:hidden text-slate-400" onClick={() => setOpen(v => !v)}>
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="md:hidden border-t border-white/5 px-4 py-3 space-y-1">
          {NAV_LINKS.map(({ to, icon: Icon, label }) => (
            <Link key={to} to={to} onClick={() => setOpen(false)}
                  className={`nav-link flex items-center gap-2 w-full ${location.pathname === to ? "active" : ""}`}>
              <Icon size={14} /> {label}
            </Link>
          ))}
          <button onClick={handleLogout} className="nav-link flex items-center gap-2 w-full text-accent-coral">
            <LogOut size={14} /> Sign out
          </button>
        </div>
      )}
    </nav>
  );
}
