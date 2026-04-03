// src/components/ui/RouteGuards.jsx
import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

// Spinner shown while auth state loads
function Spinner() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-0">
      <div className="flex flex-col items-center gap-4">
        <div className="w-10 h-10 border-2 border-surface-3 border-t-accent-cyan rounded-full animate-spin" />
        <p className="text-slate-500 text-sm font-body">Loading…</p>
      </div>
    </div>
  );
}

/** Any logged-in user */
export function RequireAuth({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return <Spinner />;
  if (!user)   return <Navigate to="/login" state={{ from: location }} replace />;
  return children;
}

/** Admin only */
export function RequireAdmin({ children }) {
  const { user, isAdmin, loading } = useAuth();
  const location = useLocation();
  if (loading)   return <Spinner />;
  if (!user)     return <Navigate to="/login" state={{ from: location }} replace />;
  if (!isAdmin)  return <Navigate to="/home" replace />;
  return children;
}

/** Redirect logged-in users away from login/signup */
export function RedirectIfAuthed({ children }) {
  const { user, isAdmin, loading } = useAuth();
  if (loading) return <Spinner />;
  if (user)    return <Navigate to={isAdmin ? "/admin" : "/home"} replace />;
  return children;
}
