#!/usr/bin/env python3
"""Initialize database tables"""

from database_v2 import init_db

if __name__ == "__main__":
    print("Creating database tables...")
    init_db()
    print("✅ Database tables created successfully!")
