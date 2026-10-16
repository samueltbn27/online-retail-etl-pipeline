# Online Retail ETL Pipeline

Pipeline ETL sederhana (Extract, Transform, Load) untuk dataset **Online Retail**
dari UCI Machine Learning Repository. Dibangun dengan **Python standard library
saja** (tanpa dependensi eksternal).

## Alur Pipeline

```
data/raw/OnlineRetail.csv
        |
     [extract]   -> validasi + parsing tiap baris
        |
   [transform]   -> de-duplikasi, pisah penjualan vs retur, ringkasan
        |
      [load]     -> tulis CSV bersih, CSV ditolak, JSON ringkasan
        |
data/processed/OnlineRetailBersih.csv
data/rejected/OnlineRetailDitolak.csv
output/Ringkasan_Penjualan_OnlineRetail.json
```

## Struktur Proyek

```
online-retail-etl/
|-- config.py              # Path & konfigurasi lokasi file
|-- main.py                # Entry point + CLI orkestrasi ETL
|-- requirements.txt
|-- pipeline/
|   |-- models.py          # Model RetailRecord + validasi
|   |-- extract.py         # Baca & validasi CSV mentah
|   |-- transform.py       # Bersihkan, de-duplikasi, ringkasan
|   |-- load.py            # Tulis output CSV & JSON
|   `-- __init__.py
|-- data/
|   |-- raw/               # Sumber OnlineRetail.csv (tidak di-commit)
|   |-- processed/         # Hasil bersih (generated)
|   `-- rejected/          # Baris gagal validasi (generated)
`-- output/                # Ringkasan JSON (generated)
```

## Sumber Data

Unduh `OnlineRetail.csv` lalu simpan di `data/raw/OnlineRetail.csv`:

- Dataset: [Online Retail — UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/352/online+retail)
- Encoding file: `cp1252`
- Format tanggal: `DD-MM-YYYY HH:MM`
- ~541.909 baris

File dataset tidak ikut di-commit karena ukurannya besar (~44 MB).

## Cara Menjalankan

```powershell
python main.py
```

Opsi CLI:

| Flag          | Default                         | Keterangan                    |
|---------------|---------------------------------|-------------------------------|
| `--source`    | `data/raw/OnlineRetail.csv`     | CSV masukan                   |
| `--cleaned`   | `data/processed/...Bersih.csv`  | CSV hasil bersih              |
| `--rejected`  | `data/rejected/...Ditolak.csv`  | CSV baris ditolak             |
| `--summary`   | `output/...Penjualan...json`    | Ringkasan JSON                |
| `-q`, `--quiet` | mati                          | Senyapkan output progres      |

Contoh pemakaian sebagai library:

```python
from main import run

report = run(verbose=False)
print(report.load_report.cleaned_rows)
```

## Logika Transformasi

- **De-duplikasi**: baris identik (invoice, stock, qty, tanggal, harga, customer) dihapus.
- **Penjualan**: bukan invoice pembatalan (`C...`), `Quantity > 0`, dan `UnitPrice > 0`.
- **Retur**: invoice dengan awalan `C`.
- **Ringkasan bulanan**: total pendapatan, kuantitas, jumlah order, jumlah pelanggan
  per bulan (format `YYYY-MM`).

## Hasil pada Dataset Penuh

| Metrik              | Nilai            |
|---------------------|------------------|
| Total baris         | 541.909          |
| Baris penjualan     | 524.876          |
| Baris retur         | 9.251            |
| Duplikat dihapus    | 5.270            |
| Baris invalid       | 2.512            |
| Total pendapatan    | £10.641.558,95   |
| Order unik          | 19.960           |
| Pelanggan unik      | 4.338            |

## Format Output

`output/Ringkasan_Penjualan_OnlineRetail.json`:

```json
[
  {
    "year": 2010,
    "month": 12,
    "revenue": 821452.73,
    "quantity": 358019,
    "order_count": 1559,
    "customer_count": 885
  }
]
```
