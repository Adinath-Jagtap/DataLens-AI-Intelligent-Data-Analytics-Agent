// src/pages/Upload.jsx
import React, { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useDropzone } from "react-dropzone";
import { Upload as UploadIcon, FileSpreadsheet, X, CheckCircle, AlertCircle } from "lucide-react";
import toast from "react-hot-toast";
import Navbar from "../components/ui/Navbar";
import { useAuth } from "../context/AuthContext";
import { createAnalysis } from "../lib/db";

const MAX_SIZE = 50 * 1024 * 1024; // 50 MB

// IndexedDB helper — stores the raw File object so Analysis.jsx can read it
function storeFile(id, file) {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open("datalens_files", 2);
    req.onupgradeneeded = (e) => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains("files")) {
        db.createObjectStore("files");
      }
    };
    req.onsuccess = (e) => {
      const db = e.target.result;
      try {
        const tx    = db.transaction("files", "readwrite");
        const store = tx.objectStore("files");
        const put   = store.put(file, id);
        put.onsuccess = () => resolve();
        put.onerror   = (ev) => reject(ev.target.error);
        tx.onerror    = (ev) => reject(ev.target.error);
      } catch (err) {
        reject(err);
      }
    };
    req.onerror = (e) => reject(e.target.error);
  });
}

export default function Upload() {
  const { user }  = useAuth();
  const navigate  = useNavigate();
  const [file,    setFile]    = useState(null);
  const [error,   setError]   = useState("");
  const [loading, setLoading] = useState(false);

  const onDrop = useCallback((accepted, rejected) => {
    setError("");
    if (rejected.length > 0) {
      setError("Only CSV and Excel files are supported (max 50 MB).");
      return;
    }
    setFile(accepted[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "text/csv":                                                          [".csv"],
      "application/vnd.ms-excel":                                          [".xls"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    },
    maxSize:  MAX_SIZE,
    maxFiles: 1,
    disabled: loading,
  });

  const handleAnalyse = async () => {
    if (!file) return;
    setLoading(true);
    setError("");

    try {
      // 1. Create Firestore record
      const analysisId = await createAnalysis(user.uid, {
        fileName:    file.name,
        fileSize:    file.size,
        status:      "processing",
        summary:     null,
        charts:      [],
        chatHistory: [],
        chartCount:  0,
      });

      // 2. Store file in IndexedDB
      await storeFile(analysisId, file);

      // 3. Navigate to analysis page
      navigate(`/analysis/${analysisId}?new=1`);

    } catch (err) {
      console.error("Upload error:", err);
      // Surface a friendly message for common Firebase errors
      let msg = "Failed to start analysis. Please try again.";
      if (err?.code === "permission-denied" || err?.message?.includes("permission")) {
        msg = "Permission denied. Make sure you are signed in and Firestore rules are published.";
      } else if (err?.message) {
        msg = err.message;
      }
      setError(msg);
      toast.error(msg);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface-0">
      <Navbar />
      <main className="max-w-2xl mx-auto px-4 py-12 page-enter">
        <div className="mb-8 text-center">
          <h1 className="font-display font-bold text-3xl text-white mb-2">Upload dataset</h1>
          <p className="text-slate-400 font-body">CSV or Excel · up to 50 MB · AI processes it in seconds</p>
        </div>

        <div
          {...getRootProps()}
          className={`glass rounded-3xl p-12 text-center cursor-pointer transition-all duration-200 border-2 border-dashed
            ${isDragActive ? "border-accent-cyan bg-accent-cyan/5" : "border-surface-4 hover:border-surface-4/80"}
            ${loading ? "opacity-50 cursor-not-allowed" : ""}
          `}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center gap-4">
            <div className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-colors
              ${isDragActive ? "bg-accent-cyan/20" : "bg-surface-3"}`}>
              <UploadIcon size={28} className={isDragActive ? "text-accent-cyan" : "text-slate-400"} />
            </div>
            {isDragActive ? (
              <p className="font-display font-semibold text-accent-cyan text-lg">Drop it here!</p>
            ) : (
              <>
                <div>
                  <p className="font-display font-semibold text-white text-lg">Drag & drop your file here</p>
                  <p className="text-slate-500 font-body text-sm mt-1">
                    or <span className="text-accent-cyan">click to browse</span>
                  </p>
                </div>
                <div className="flex items-center gap-3 text-xs text-slate-600 font-body">
                  <span className="badge badge-cyan">.csv</span>
                  <span className="badge badge-violet">.xls</span>
                  <span className="badge badge-green">.xlsx</span>
                  <span>· max 50 MB</span>
                </div>
              </>
            )}
          </div>
        </div>

        {error && (
          <div className="mt-4 flex items-center gap-2 text-accent-coral text-sm font-body">
            <AlertCircle size={15} /> {error}
          </div>
        )}

        {file && (
          <div className="mt-5 glass rounded-2xl p-4 flex items-center gap-3">
            <FileSpreadsheet size={20} className="text-accent-cyan flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="font-body font-medium text-white text-sm truncate">{file.name}</div>
              <div className="text-xs text-slate-500 mt-0.5">{(file.size / 1024 / 1024).toFixed(2)} MB</div>
            </div>
            <button onClick={() => setFile(null)} className="text-slate-500 hover:text-slate-300">
              <X size={16} />
            </button>
            <CheckCircle size={16} className="text-accent-green flex-shrink-0" />
          </div>
        )}

        <button
          onClick={handleAnalyse}
          disabled={!file || loading}
          className="btn-primary w-full justify-center py-3.5 mt-6 text-base"
        >
          {loading ? (
            <><span className="w-4 h-4 border-2 border-surface-0 border-t-transparent rounded-full animate-spin" /> Starting analysis…</>
          ) : (
            <><UploadIcon size={16} /> Analyse with AI</>
          )}
        </button>

        <div className="mt-6 glass rounded-2xl p-4 text-xs text-slate-500 font-body space-y-1.5">
          <p className="flex items-center gap-2"><span className="text-accent-cyan">✓</span> Your file stays in your browser — never sent to any server</p>
          <p className="flex items-center gap-2"><span className="text-accent-cyan">✓</span> AI analysis runs locally via Pyodide (Python in WebAssembly)</p>
          <p className="flex items-center gap-2"><span className="text-accent-cyan">✓</span> Only anonymised metadata is saved to your profile</p>
        </div>
      </main>
    </div>
  );
}
