import json
import os
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.environ.get('BACKUP_DB_URL')
BACKUP_DIR = os.path.expanduser('~/mealplanner_backups')
KEEP = 10


def main():
    if not DB_URL:
        raise SystemExit('Add BACKUP_DB_URL to your .env file first.')

    os.makedirs(BACKUP_DIR, exist_ok=True)

    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
    )
    tables = [row['table_name'] for row in cur.fetchall()]

    backup = {}
    for table in tables:
        cur.execute(f'SELECT * FROM "{table}"')
        backup[table] = cur.fetchall()
    conn.close()

    filename = datetime.now().strftime('backup_%Y-%m-%d_%H%M.json')
    path = os.path.join(BACKUP_DIR, filename)
    with open(path, 'w') as f:
        json.dump(backup, f, default=str, indent=1)
    os.chmod(path, 0o600)

    files = sorted(f for f in os.listdir(BACKUP_DIR) if f.startswith('backup_'))
    for old in files[:-KEEP]:
        os.remove(os.path.join(BACKUP_DIR, old))

    total = sum(len(rows) for rows in backup.values())
    print(f'Saved {total} rows from {len(tables)} tables to {path}')


if __name__ == '__main__':
    main()