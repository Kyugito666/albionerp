# Project Context: Albion Online ERP & Market Analyzer

## 1. Overview
Aplikasi web backend berbasis Flask untuk kalkulasi *crafting*, *refining*, logistik, dan analisis arbitrase *luxury items* di Albion Online. Sistem dirancang untuk menangani asupan data pasar (market data ingest) dengan frekuensi tinggi menggunakan eksekusi asinkron dan manajemen in-memory state.

## 2. Arsitektur & Tech Stack
- **Backend Framework**: Python (Flask).
- **Data Serialization**: `orjson` (Wajib digunakan untuk performa I/O maksimal).
- **Concurrency & State Management**: 
  - `MemoryState` dengan `threading.RLock` untuk mencegah race condition.
  - Background saver thread (dump ke JSON).
  - Background ingestor thread (`queue.Queue`) untuk endpoint asinkron `/api/ingest`.
- **Database/Persistence**: Flat JSON files (`config.json`, `prices.json`, `volume_history.json`, dll).

## 3. Ground Truth: Formula & Referensi Mekanik
Setiap kalkulasi dalam `core/calculator.py` dan module lainnya **wajib** mengacu pada sumber data ini:
- **AODP & Item IDs**: [API Docs](https://www.albion-online-data.com/api) | [Items TXT](https://github.com/ao-data/ao-bin-dumps/blob/master/formatted/items.txt)
- **Core Math**: [Item Value](https://wiki.albiononline.com/wiki/Item_Value) | [RRR](https://wiki.albiononline.com/wiki/Resource_Return_Rate) | [Local Production Bonus](https://wiki.albiononline.com/wiki/Local_Production_Bonus)
- **Economy**: [Marketplace](https://wiki.albiononline.com/wiki/Marketplace) | [Black Market](https://wiki.albiononline.com/wiki/Black_Market) | [Luxury Goods](https://wiki.albiononline.com/wiki/Luxury_Goods)
- **Production**: [Crafting](https://wiki.albiononline.com/wiki/Crafting) | [Refining](https://wiki.albiononline.com/wiki/Refining) | [Crafting Station](https://wiki.albiononline.com/wiki/Crafting_Station)
- **Progression**: [Destiny Board](https://wiki.albiononline.com/wiki/Destiny_Board) | [Focus Points](https://wiki.albiononline.com/wiki/Focus_Points) | [Journals](https://wiki.albiononline.com/wiki/Journal)

## 4. Engineering Rules & Constraints (WAJIB DIPATUHI)
1. **Thread Safety**: Setiap mutasi state (contoh: `state.prices`) wajib di-wrap dengan `with state.lock:`.
2. **Non-Blocking I/O**: Dilarang memblokir main thread dengan operasi disk berat. 
3. **Optimasi Algoritma**: Gunakan pencarian O(1) dengan hashmap. Hindari loop O(n^2) pada iterasi dataset harga AODP.
4. **Validasi Kotor**: Gunakan fungsi *safe cast* (`sfloat`, `sint`) karena payload AODP sering kotor atau atributnya hilang.

## 5. Instruksi Persona AI
- **Gaya Bicara**: Langsung, padat, dan teknis (*to the point*). Hapus basa-basi, permintaan maaf, atau frasa "Sebagai AI...".
- **Tanya Dulu, Jangan Asumsi**: Klarifikasi spesifikasi teknis atau batasan bug sebelum *generate* kode solusi.
- **Solusi Holistik**: Jangan cuma ngasih sepotong kode. Jelaskan arsitektur, edge case, dan justifikasi (*trade-off*) dari solusi tersebut.
- **Tantang Ide**: Jika logika *user* berisiko *race condition*, *memory leak*, atau menyalahi ground truth Albion (seperti RRR salah kalkulasi), serang argumennya dan berikan opsi superior.