// src/context/AuthContext.jsx
import React, { createContext, useContext, useEffect, useState } from "react";
import {
  onAuthStateChanged, signInWithEmailAndPassword,
  createUserWithEmailAndPassword, signInWithPopup,
  signOut, updateProfile
} from "firebase/auth";
import { auth, googleProvider, ADMIN_UID } from "../lib/firebase";
import { ensureUserProfile } from "../lib/db";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user,    setUser]    = useState(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, async (u) => {
      setUser(u);
      setIsAdmin(!!u && u.uid === ADMIN_UID);
      if (u) {
        try {
          await ensureUserProfile(u.uid, u.displayName || "User", u.email);
        } catch {}
      }
      setLoading(false);
    });
    return unsub;
  }, []);

  const login = (email, password) =>
    signInWithEmailAndPassword(auth, email, password);

  const loginWithGoogle = () =>
    signInWithPopup(auth, googleProvider);

  const register = async (email, password, name) => {
    const cred = await createUserWithEmailAndPassword(auth, email, password);
    await updateProfile(cred.user, { displayName: name });
    return cred;
  };

  const logout = () => signOut(auth);

  return (
    <AuthContext.Provider value={{ user, isAdmin, loading, login, loginWithGoogle, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
