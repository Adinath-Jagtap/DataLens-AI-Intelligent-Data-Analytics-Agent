"""
Sandboxed pandas code executor for AI-generated data queries.
Executes code against the user's cleaned DataFrame and captures output.
"""
import io
import sys
import traceback
import pandas as pd
import numpy as np


# Allowed builtins — no file I/O, no imports, no exec/eval
_SAFE_BUILTINS = {
    "abs": abs, "all": all, "any": any, "bool": bool,
    "dict": dict, "enumerate": enumerate, "filter": filter,
    "float": float, "format": format, "frozenset": frozenset,
    "int": int, "isinstance": isinstance, "len": len,
    "list": list, "map": map, "max": max, "min": min,
    "print": print, "range": range, "reversed": reversed,
    "round": round, "set": set, "slice": slice, "sorted": sorted,
    "str": str, "sum": sum, "tuple": tuple, "type": type,
    "zip": zip, "True": True, "False": False, "None": None,
}


def build_dataframe(cleaned_rows: list) -> pd.DataFrame:
    """Reconstruct a pandas DataFrame from MongoDB cleaned_rows."""
    if not cleaned_rows:
        return pd.DataFrame()
    df = pd.DataFrame(cleaned_rows)
    # Try to convert columns to appropriate numeric types
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col])
        except (ValueError, TypeError):
            pass
    return df


def execute_code(code: str, df: pd.DataFrame, timeout_seconds: int = 10) -> dict:
    """
    Execute AI-generated pandas code in a restricted namespace.

    Returns:
        {
            "success": bool,
            "output": str,       # captured stdout (print output)
            "error": str | None, # error message if failed
        }
    """
    # Restrict the execution namespace
    namespace = {
        "__builtins__": _SAFE_BUILTINS,
        "pd": pd,
        "np": np,
        "df": df.copy(),  # Never mutate the original
    }

    # Capture stdout
    old_stdout = sys.stdout
    captured = io.StringIO()

    try:
        sys.stdout = captured

        # Compile first to catch syntax errors
        compiled = compile(code, "<ai_query>", "exec")

        # Check for dangerous operations
        code_lower = code.lower()
        banned = [
            "import ", "__import__", "exec(", "eval(",
            "open(", "os.", "sys.", "subprocess",
            "shutil", "pathlib", "globals(", "locals(",
            "getattr", "setattr", "delattr", "__class__",
            "__subclasses__", "__bases__", "breakpoint",
        ]
        for b in banned:
            if b in code_lower:
                return {
                    "success": False,
                    "output": "",
                    "error": f"Blocked: '{b.strip()}' is not allowed in generated code.",
                }

        exec(compiled, namespace)

        output = captured.getvalue().strip()

        # If nothing was printed, check if the last expression has a value
        if not output:
            # Try to evaluate the last line as an expression
            lines = [l for l in code.strip().split("\n") if l.strip() and not l.strip().startswith("#")]
            if lines:
                last_line = lines[-1].strip()
                # If it looks like an expression (not an assignment or print)
                if not last_line.startswith(("print", "for ", "if ", "while ", "def ", "class ")):
                    if "=" not in last_line or last_line.startswith("df") or "==" in last_line:
                        try:
                            result = eval(last_line, namespace)
                            if result is not None:
                                if isinstance(result, pd.DataFrame):
                                    output = result.to_string(max_rows=20, max_cols=15)
                                elif isinstance(result, pd.Series):
                                    output = result.to_string(max_rows=30)
                                else:
                                    output = str(result)
                        except Exception:
                            pass

        # Truncate very long outputs
        if len(output) > 3000:
            output = output[:3000] + "\n\n… (output truncated)"

        return {
            "success": True,
            "output": output or "(No output produced)",
            "error": None,
        }

    except Exception as e:
        tb = traceback.format_exc()
        # Only show the last useful line of the traceback
        err_lines = tb.strip().split("\n")
        short_err = err_lines[-1] if err_lines else str(e)
        return {
            "success": False,
            "output": captured.getvalue().strip(),
            "error": short_err,
        }

    finally:
        sys.stdout = old_stdout
