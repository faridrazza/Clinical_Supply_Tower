"""
Script to load CSV data into PostgreSQL database.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def clean_column_name(col_name: str) -> str:
    """
    Clean column names to be SQL-friendly.
    
    Args:
        col_name: Original column name
        
    Returns:
        Cleaned column name
    """
    # Replace spaces and special characters with underscores
    cleaned = col_name.strip().lower()
    cleaned = cleaned.replace(' ', '_')
    cleaned = cleaned.replace('(', '').replace(')', '')
    cleaned = cleaned.replace(',', '')
    cleaned = cleaned.replace('.', '_')
    cleaned = cleaned.replace('-', '_')
    
    # Remove multiple underscores
    while '__' in cleaned:
        cleaned = cleaned.replace('__', '_')
    
    return cleaned.strip('_')


def load_csv_to_postgres(csv_path: str, table_name: str, engine):
    """
    Load a CSV file into PostgreSQL table.
    
    Args:
        csv_path: Path to CSV file
        table_name: Name of the table to create
        engine: SQLAlchemy engine
    """
    try:
        logger.info(f"Loading {csv_path} into table {table_name}...")
        
        # Read CSV
        df = pd.read_csv(csv_path)
        
        # Clean column names
        df.columns = [clean_column_name(col) for col in df.columns]
        
        # Log info
        logger.info(f"  Rows: {len(df)}, Columns: {len(df.columns)}")
        logger.info(f"  Columns: {', '.join(df.columns[:5])}{'...' if len(df.columns) > 5 else ''}")
        
        # Load to PostgreSQL
        df.to_sql(
            table_name,
            engine,
            if_exists='replace',
            index=False,
            method='multi',
            chunksize=1000
        )
        
        logger.info(f"✓ Successfully loaded {table_name}")
        return True
        
    except Exception as e:
        logger.error(f"✗ Error loading {csv_path}: {str(e)}")
        return False


def main():
    """Main function to load all CSV files."""
    # Create database engine
    engine = create_engine(settings.database_url)
    
    # Test connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✓ Database connection successful")
    except Exception as e:
        logger.error(f"✗ Database connection failed: {str(e)}")
        logger.error("Please check your DATABASE_URL in .env file")
        return
    
    # Find CSV files
    data_dir = Path(__file__).parent.parent / "synthetic_clinical_data"
    
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return
    
    csv_files = list(data_dir.glob("*.csv"))
    logger.info(f"Found {len(csv_files)} CSV files")
    
    # Load each CSV file
    success_count = 0
    failed_count = 0
    
    for csv_file in csv_files:
        # Generate table name from filename
        table_name = csv_file.stem.replace('-', '_')
        
        if load_csv_to_postgres(str(csv_file), table_name, engine):
            success_count += 1
        else:
            failed_count += 1
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info(f"Loading complete!")
    logger.info(f"  Success: {success_count}")
    logger.info(f"  Failed: {failed_count}")
    logger.info("="*50)
    
    # List all tables
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            
            logger.info(f"\nTables in database ({len(tables)}):")
            for table in tables:
                logger.info(f"  - {table}")
    except Exception as e:
        logger.error(f"Error listing tables: {e}")


if __name__ == "__main__":
    main()
