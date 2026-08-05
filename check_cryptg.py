# check_cryptg.py — cryptg available? (FastTelethon speed ke liye zaroori)
try:
    import cryptg
    print("[ok] cryptg version:", getattr(cryptg, "__version__", "?"))
except Exception as e:
    print(f"[x] cryptg NOT available: {str(e)[:100]}")
import telethon
print("[ok] telethon:", telethon.__version__)
