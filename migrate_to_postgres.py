import psycopg2
from psycopg2.extras import execute_values

OLD_RENDER_URL = 'postgresql://mealplanner_db_ybes_user:xbSKte8qrxdimTWJAZtH5LMFxGDmdX0R@dpg-d9mr30bm8hqs73cusbh0-a.frankfurt-postgres.render.com/mealplanner_db_ybes?sslmode=require'
NEON_URL = 'postgresql://neondb_owner:npg_ByLQ8sWeK3AZ@ep-blue-silence-b12tn3os-pooler.c-5.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'

TABLES_IN_ORDER = [
    'user',
    'meal',
    'ingredient',
    'followers',
    'follow_requests',
    'push_subscription',
    'storage_item',
]

def get_columns(cursor, table):
    cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = %s ORDER BY ordinal_position", (table,))
    return [row[0] for row in cursor.fetchall()]

def migrate_table(old_conn, new_conn, table):
    old_cursor = old_conn.cursor()
    columns = get_columns(old_cursor, table)

    if not columns:
        print(f"Hopper over '{table}' - finnes ikke")
        return

    col_list = ', '.join(f'"{c}"' for c in columns)
    old_cursor.execute(f'SELECT {col_list} FROM "{table}"')
    rows = old_cursor.fetchall()

    if not rows:
        print(f"'{table}': ingen rader å migrere")
        return

    new_cursor = new_conn.cursor()
    insert_query = f'INSERT INTO "{table}" ({col_list}) VALUES %s ON CONFLICT DO NOTHING'

    execute_values(new_cursor, insert_query, rows)
    new_conn.commit()
    print(f"'{table}': migrerte {len(rows)} rader")

def reset_sequences(conn, table):
    cursor = conn.cursor()
    try:
        cursor.execute(f'''
            SELECT setval(
                pg_get_serial_sequence('"{table}"', 'id'),
                COALESCE((SELECT MAX(id) FROM "{table}"), 1)
            )
        ''')
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Kunne ikke resette sequence for '{table}': {e}")

def main():
    old_conn = psycopg2.connect(OLD_RENDER_URL)
    new_conn = psycopg2.connect(NEON_URL)

    for table in TABLES_IN_ORDER:
        migrate_table(old_conn, new_conn, table)
        reset_sequences(new_conn, table)

    old_conn.close()
    new_conn.close()
    print("Ferdig!")

if __name__ == '__main__':
    main()