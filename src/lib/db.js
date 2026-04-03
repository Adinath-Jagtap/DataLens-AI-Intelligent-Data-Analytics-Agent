// src/lib/db.js
import {
  collection, doc, setDoc, getDoc, getDocs,
  updateDoc, deleteDoc, query, where, orderBy,
  limit, serverTimestamp, addDoc
} from "firebase/firestore";
import { ref, uploadBytes, getDownloadURL, deleteObject } from "firebase/storage";
import { db, storage } from "./firebase";

// ─── Analyses ───────────────────────────────────────────────────────────────

export async function createAnalysis(uid, data) {
  const ref = doc(collection(db, "users", uid, "analyses"));
  await setDoc(ref, {
    ...data,
    createdAt: serverTimestamp(),
    updatedAt: serverTimestamp(),
  });
  return ref.id;
}

export async function getAnalysis(uid, analysisId) {
  const snap = await getDoc(doc(db, "users", uid, "analyses", analysisId));
  return snap.exists() ? { id: snap.id, ...snap.data() } : null;
}

export async function updateAnalysis(uid, analysisId, data) {
  await updateDoc(doc(db, "users", uid, "analyses", analysisId), {
    ...data,
    updatedAt: serverTimestamp(),
  });
}

export async function getUserAnalyses(uid) {
  const q = query(
    collection(db, "users", uid, "analyses"),
    orderBy("createdAt", "desc"),
    limit(50)
  );
  const snap = await getDocs(q);
  return snap.docs.map(d => ({ id: d.id, ...d.data() }));
}

export async function deleteAnalysis(uid, analysisId) {
  await deleteDoc(doc(db, "users", uid, "analyses", analysisId));
}

// ─── Chat history ────────────────────────────────────────────────────────────

export async function saveChat(uid, analysisId, messages) {
  await updateDoc(doc(db, "users", uid, "analyses", analysisId), {
    chatHistory: messages,
    updatedAt:   serverTimestamp(),
  });
}

// ─── User profile ────────────────────────────────────────────────────────────

export async function ensureUserProfile(uid, displayName, email) {
  const ref = doc(db, "users", uid);
  const snap = await getDoc(ref);
  if (!snap.exists()) {
    await setDoc(ref, {
      displayName,
      email,
      createdAt:    serverTimestamp(),
      analysisCount: 0,
    });
  }
}

export async function getUserProfile(uid) {
  const snap = await getDoc(doc(db, "users", uid));
  return snap.exists() ? { id: snap.id, ...snap.data() } : null;
}

// ─── File storage ────────────────────────────────────────────────────────────

export async function uploadDatasetFile(uid, analysisId, file) {
  const fileRef = ref(storage, `datasets/${uid}/${analysisId}/${file.name}`);
  await uploadBytes(fileRef, file);
  return getDownloadURL(fileRef);
}

export async function deleteDatasetFile(uid, analysisId, fileName) {
  const fileRef = ref(storage, `datasets/${uid}/${analysisId}/${fileName}`);
  try { await deleteObject(fileRef); } catch {}
}

// ─── Admin helpers ────────────────────────────────────────────────────────────

export async function getAllUsers() {
  const snap = await getDocs(collection(db, "users"));
  return snap.docs.map(d => ({ id: d.id, ...d.data() }));
}

export async function getAllAnalyses() {
  // Admin: get analyses across all users (top 200)
  const usersSnap = await getDocs(collection(db, "users"));
  const all = [];
  for (const userDoc of usersSnap.docs) {
    const q    = query(collection(db, "users", userDoc.id, "analyses"), orderBy("createdAt", "desc"), limit(10));
    const aSnap = await getDocs(q);
    aSnap.docs.forEach(d => all.push({ id: d.id, uid: userDoc.id, ...d.data() }));
  }
  return all.sort((a, b) => (b.createdAt?.seconds || 0) - (a.createdAt?.seconds || 0));
}

export async function deleteUser(uid) {
  // Delete all analyses
  const q    = query(collection(db, "users", uid, "analyses"));
  const snap = await getDocs(q);
  await Promise.all(snap.docs.map(d => deleteDoc(d.ref)));
  // Delete user doc
  await deleteDoc(doc(db, "users", uid));
}
