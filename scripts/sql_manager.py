# sql_manager.py (FIXED VERSION)
import pandas as pd
from sqlalchemy import create_engine, text
import os
import glob
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def create_database():
    """SQLite database banata hai aur tables create karta hai"""
    # Database engine create karo 
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///database/cricsheet.db')  # Default fallback
    engine = create_engine(DATABASE_URL)
    print(f"Using database: {DATABASE_URL}")  # Debug info
    
    # Tables create karne ke liye SQL queries
    create_tables_queries = [
        """
        CREATE TABLE IF NOT EXISTS matches (
            match_id TEXT PRIMARY KEY,
            match_type TEXT,
            team1 TEXT,
            team2 TEXT,
            venue TEXT,
            date TEXT,
            winner TEXT,
            toss_winner TEXT,
            toss_decision TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS innings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_id TEXT,
            match_type TEXT,
            inning_team TEXT,
            over INTEGER,
            ball INTEGER,
            batsman TEXT,
            bowler TEXT,
            runs_batted INTEGER,
            extras INTEGER,
            total_runs INTEGER,
            wicket INTEGER,
            FOREIGN KEY (match_id) REFERENCES matches (match_id)
        )
        """
    ]
    
    # Database folder banayo
    os.makedirs('database', exist_ok=True)
    
    # Tables create karo
    with engine.connect() as conn:
        for query in create_tables_queries:
            conn.execute(text(query))
        conn.commit()
    
    print("Database tables successfully created!")
    return engine

def load_data_to_db(engine):
    """Processed data ko database mein load karta hai - DYNAMIC VERSION"""
    try:
        # Check which CSV files are available
        print("Checking available CSV files...")
        
        # Match files find karo
        match_files = glob.glob('data/processed/*_matches.csv')
        innings_files = glob.glob('data/processed/*_innings.csv')
        
        print(f"Found {len(match_files)} match files and {len(innings_files)} innings files")
        
        # All matches combine karo
        all_matches = pd.DataFrame()
        for match_file in match_files:
            match_type = os.path.basename(match_file).replace('_matches.csv', '')
            print(f"Loading {match_type} matches...")
            df = pd.read_csv(match_file)
            all_matches = pd.concat([all_matches, df], ignore_index=True)
        
        # All innings combine karo
        all_innings = pd.DataFrame()
        for innings_file in innings_files:
            match_type = os.path.basename(innings_file).replace('_innings.csv', '')
            print(f"Loading {match_type} innings...")
            df = pd.read_csv(innings_file)
            all_innings = pd.concat([all_innings, df], ignore_index=True)
        
        # Check if we have data
        if all_matches.empty or all_innings.empty:
            print("Koi data nahi mila. Pehle data_processor.py run karo.")
            return
        
        # Data ko database mein insert karo
        print("Loading matches data...")
        all_matches.to_sql('matches', engine, if_exists='append', index=False)
        
        print("Loading innings data...")
        all_innings.to_sql('innings', engine, if_exists='append', index=False)
        
        # Data summary print karo
        print("\n📊 Data Loading Summary:")
        print(f"Total Matches Loaded: {len(all_matches)}")
        print(f"Total Ball-by-Ball Records: {len(all_innings):,}")
        
        # Match types breakdown
        print("\nMatch Types Breakdown:")
        for match_type in all_matches['match_type'].unique():
            count = len(all_matches[all_matches['match_type'] == match_type])
            print(f"- {match_type}: {count} matches")
        
        print("Data successfully loaded into database!")
        
    except Exception as e:
        print(f"Error loading data: {e}")
        print("Make sure CSV files exist in data/processed/ folder")
        print("Pehle data_processor.py run karo")

def check_database_tables(engine):
    """Database tables aur unke columns check karta hai"""
    print("\nChecking database tables...")
    
    with engine.connect() as conn:
        # Tables list
        tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        print("Tables in database:")
        for table in tables:
            print(f" - {table[0]}")
        
        # Columns for each table
        for table_name in ['matches', 'innings']:
            print(f"\nColumns in {table_name}:")
            result = conn.execute(text(f"PRAGMA table_info({table_name})"))
            for row in result:
                print(f" - {row[1]} ({row[2]})")

def check_csv_files():
    """CSV files check karta hai"""
    print("Checking CSV files in data/processed/...")
    
    if not os.path.exists('data/processed'):
        print("data/processed/ folder hi nahi hai!")
        return
    
    csv_files = glob.glob('data/processed/*.csv')
    if not csv_files:
        print("Koi CSV files nahi mili!")
        return
    
    print("Available CSV files:")
    for file in csv_files:
        file_size = os.path.getsize(file) / 1024  # KB mein
        print(f" - {os.path.basename(file)} ({file_size:.1f} KB)")
        
        # Peek into first few rows
        try:
            df = pd.read_csv(file, nrows=2)
            print(f"   Columns: {list(df.columns)}")
            print(f"   Rows: {len(pd.read_csv(file))}")
        except:
            print("   Could not read file")

if __name__ == "__main__":
    # Pehle existing database delete karo (agar hai toh)
    if os.path.exists('database/cricsheet.db'):
        os.remove('database/cricsheet.db')
        print("Old database deleted")
    
    # Pehle CSV files check karo
    check_csv_files()
    print("\n" + "="*50 + "\n")
    
    # Phir database banayo aur data load karo
    engine = create_database()
    check_database_tables(engine)
    print("\n" + "="*50 + "\n")
    
    load_data_to_db(engine)