import sqlite3

DB_NAME = "database.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact TEXT,
            has_ruler BOOLEAN DEFAULT 0,
            payment_status TEXT DEFAULT 'Pendente',
            receipt_filename TEXT NOT NULL,
            is_courtesy BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    try:
        cursor.execute('ALTER TABLE teams ADD COLUMN is_courtesy BOOLEAN DEFAULT 0')
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute('ALTER TABLE teams ADD COLUMN payment_amount REAL DEFAULT 0.0')
    except sqlite3.OperationalError:
        pass
        
    for i in range(1, 5):
        try:
            cursor.execute(f'ALTER TABLE teams ADD COLUMN participant{i} TEXT')
        except sqlite3.OperationalError:
            pass
            
    for col in ['circuit_name', 'stage_name', 'year']:
        try:
            cursor.execute(f'ALTER TABLE teams ADD COLUMN {col} TEXT')
        except sqlite3.OperationalError:
            pass
            
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            circuit_name TEXT,
            stage_name TEXT,
            year TEXT
        )
    ''')
    
    try:
        cursor.execute("ALTER TABLE settings ADD COLUMN year TEXT DEFAULT '2026'")
    except sqlite3.OperationalError:
        pass
    
    cursor.execute('SELECT COUNT(*) FROM settings')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO settings (id, circuit_name, stage_name, year) VALUES (1, "Circuito Padrão", "Etapa 1", "2026")')
        
    conn.commit()
    conn.close()
