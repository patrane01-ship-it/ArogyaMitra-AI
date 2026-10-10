"""
Setup script to generate .env file with secure keys.
Run this once to create your local .env file.
"""

import os
import base64
import secrets

def generate_env_file():
    """Generate .env file with secure random keys."""
    
    # Generate secure keys
    secret_key = secrets.token_hex(32)
    encryption_key = base64.b64encode(os.urandom(32)).decode()
    
    env_content = f"""# ── Database (PostgreSQL) ───────────────────────────────
# For local dev without Docker, you can use SQLite temporarily:
# DATABASE_URL=sqlite:///./backend/data/arogya_mitra.db
# For production or Docker Postgres:
DATABASE_URL=postgresql://arogya:arogya_dev@localhost:5432/arogya_mitra

# ── Cache (Redis) ──────────────────────────────────────
# For local dev without Docker, caching will be disabled gracefully
REDIS_URL=redis://localhost:6379/0

# ── LLM ──────────────────────────────────────────────
GROQ_API_KEY=your_groq_api_key_here

# ── Security ─────────────────────────────────────────
SECRET_KEY={secret_key}
ENCRYPTION_KEY={encryption_key}

# ── App ──────────────────────────────────────────────
ENVIRONMENT=development
DEBUG=true
CORS_ORIGINS=["http://localhost:5173"]

# ── Storage ──────────────────────────────────────────
UPLOAD_DIR=./backend/data/records/encrypted
CHROMA_DB_PATH=./backend/data/chroma_db
"""
    
    with open(".env", "w", encoding="utf-8") as f:
        f.write(env_content)
    
    print("[OK] .env file created successfully!")
    print("[WARN] Please update GROQ_API_KEY with your actual Groq API key.")
    print("[WARN] If you don't have PostgreSQL/Redis running locally, update DATABASE_URL to use SQLite temporarily.")

if __name__ == "__main__":
    generate_env_file()
