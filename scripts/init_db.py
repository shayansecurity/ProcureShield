from app.database import init_db
from app.config import DB_PATH

if __name__ == "__main__":
    init_db()
    print(f"Initialized {DB_PATH}")
