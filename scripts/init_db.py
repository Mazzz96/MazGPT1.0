import sys
from model.db import init_db

if __name__ == "__main__":
    print("Initializing MazGPT database...")
    init_db()
    print("Database initialized.")
