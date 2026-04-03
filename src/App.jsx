// src/App.jsx
import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { AuthProvider } from "./context/AuthContext";
import { RequireAuth, RequireAdmin, RedirectIfAuthed } from "./components/ui/RouteGuards";

// Pages (lazy loaded)
const Landing   = React.lazy(() => import("./pages/Landing"));
const Login     = React.lazy(() => import("./pages/Login"));
const Signup    = React.lazy(() => import("./pages/Signup"));
const Home      = React.lazy(() => import("./pages/Home"));
const Upload    = React.lazy(() => import("./pages/Upload"));
const Analysis  = React.lazy(() => import("./pages/Analysis"));
const Profile   = React.lazy(() => import("./pages/Profile"));
const History   = React.lazy(() => import("./pages/History"));
const AdminPanel= React.lazy(() => import("./pages/AdminPanel"));

function AppRoutes() {
  return (
    <React.Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-surface-0">
        <div className="w-8 h-8 border-2 border-surface-3 border-t-accent-cyan rounded-full animate-spin" />
      </div>
    }>
      <Routes>
        {/* Public */}
        <Route path="/" element={<Landing />} />
        <Route path="/login"  element={<RedirectIfAuthed><Login /></RedirectIfAuthed>} />
        <Route path="/signup" element={<RedirectIfAuthed><Signup /></RedirectIfAuthed>} />

        {/* User routes */}
        <Route path="/home"              element={<RequireAuth><Home /></RequireAuth>} />
        <Route path="/upload"            element={<RequireAuth><Upload /></RequireAuth>} />
        <Route path="/analysis/:id"      element={<RequireAuth><Analysis /></RequireAuth>} />
        <Route path="/profile"           element={<RequireAuth><Profile /></RequireAuth>} />
        <Route path="/history"           element={<RequireAuth><History /></RequireAuth>} />

        {/* Admin routes */}
        <Route path="/admin"             element={<RequireAdmin><AdminPanel /></RequireAdmin>} />
        <Route path="/admin/*"           element={<RequireAdmin><AdminPanel /></RequireAdmin>} />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </React.Suspense>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: "#141f33",
              color:      "#e2e8f0",
              border:     "1px solid rgba(255,255,255,0.08)",
              fontFamily: "'DM Sans', sans-serif",
              fontSize:   "14px",
            },
            success: { iconTheme: { primary: "#34d399", secondary: "#0a0f1a" } },
            error:   { iconTheme: { primary: "#fb7185", secondary: "#0a0f1a" } },
          }}
        />
      </BrowserRouter>
    </AuthProvider>
  );
}
