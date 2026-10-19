"""Debug helper: import & version check (dùng để test trên Streamlit Cloud).

Chạy trực tiếp:  streamlit run debug_imports.py
Hoặc gọi qua st.write trong app chính.
"""
import sys
import platform
import streamlit as st

st.title("🔧  Debug — Package versions")
st.write(f"**Python**: {sys.version}")
st.write(f"**Platform**: {platform.platform()}")

packages = [
    "streamlit", "numpy", "pandas", "scikit-learn",
    "lightgbm", "joblib", "matplotlib",
]
data = []
for pkg in packages:
    try:
        mod = __import__(pkg)
        ver = getattr(mod, "__version__", "?")
        data.append((pkg, "✅", ver))
    except Exception as e:
        data.append((pkg, "❌", str(e)[:60]))

import pandas as _pd
df = _pd.DataFrame(data, columns=["Package", "Status", "Version"])
st.dataframe(df, use_container_width=True)

# Show import path
try:
    import src
    st.success(f"`src` package at: {src.__file__}")
except Exception as e:
    st.error(f"Cannot import `src`: {e}")

# Show current working directory
st.write(f"**CWD**: {__import__('os').getcwd()}")
