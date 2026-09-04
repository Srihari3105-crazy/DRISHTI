import os
import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_drishti.db"
os.environ["JWT_SECRET"] = "test-secret-min32-chars-padded-xxxx"
