from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Folder Data
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REJECTED_DIR = DATA_DIR / "rejected"

# Folder Output
OUTPUT_DIR = BASE_DIR / "output"

# Lokasi File Spesifik
SOURCE_FILE = RAW_DIR / "OnlineRetail.csv"
CLEANED_FILE = PROCESSED_DIR / "OnlineRetailBersih.csv"
REJECTED_FILE = REJECTED_DIR / "OnlineRetailDitolak.csv"  
SUMMARY_FILE = OUTPUT_DIR / "Ringkasan_Penjualan_OnlineRetail.json"