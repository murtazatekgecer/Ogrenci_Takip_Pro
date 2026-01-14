"""
Veritabanı modelleri ve tablo oluşturma fonksiyonları.
SQLite kullanarak öğrenci takip sistemi için gerekli tabloları oluşturur.
"""
import sqlite3
import os
from datetime import datetime


def get_db_path():
    """Veritabanı dosya yolunu döndürür."""
    import os
    # Android/Mobile için yazılabilir dizin kontrolü
    storage_path = os.environ.get("FLET_APP_STORAGE_DATA")
    
    if storage_path:
        # Mobilde uygulama veri dizinine kaydet
        db_path = os.path.join(storage_path, 'ogrenci_takip.db')
    else:
        # Geliştirme ortamında - android klasöründe
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, 'ogrenci_takip.db')
        
    return db_path


def init_db():
    """
    Veritabanını başlatır ve gerekli tabloları oluşturur.
    Varsayılan kategorileri de ekler.
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Sınıf tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sinif (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT NOT NULL,
            donem TEXT DEFAULT '',
            olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Öğrenci tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ogrenci (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT NOT NULL,
            soyad TEXT NOT NULL,
            okul_no TEXT UNIQUE,
            sinif_id INTEGER,
            rozetler TEXT DEFAULT '[]',
            kayit_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sinif_id) REFERENCES sinif(id) ON DELETE SET NULL
        )
    ''')
    
    # Kategori tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS kategori (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT NOT NULL UNIQUE,
            sira INTEGER DEFAULT 0,
            varsayilan INTEGER DEFAULT 0
        )
    ''')
    
    # Not başlığı tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS not_basligi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            baslik TEXT NOT NULL,
            kategori_id INTEGER NOT NULL,
            sinif_id INTEGER,
            tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (kategori_id) REFERENCES kategori(id) ON DELETE CASCADE,
            FOREIGN KEY (sinif_id) REFERENCES sinif(id) ON DELETE CASCADE
        )
    ''')
    
    # Not tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS not_ (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ogrenci_id INTEGER NOT NULL,
            baslik_id INTEGER NOT NULL,
            puan REAL DEFAULT 0,
            guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ogrenci_id) REFERENCES ogrenci(id) ON DELETE CASCADE,
            FOREIGN KEY (baslik_id) REFERENCES not_basligi(id) ON DELETE CASCADE,
            UNIQUE(ogrenci_id, baslik_id)
        )
    ''')
    
    # İşlem geçmişi tablosu (Undo için)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS islem_gecmisi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            islem_tipi TEXT NOT NULL,
            tablo_adi TEXT NOT NULL,
            kayit_id INTEGER,
            eski_veri TEXT,
            yeni_veri TEXT,
            tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Varsayılan kategorileri SADECE kategori tablosu boş ise ekle
    # Bu sayede kullanıcı sildiğinde/düzenlediğinde tekrar oluşturulmaz
    cursor.execute('SELECT COUNT(*) as count FROM kategori')
    row = cursor.fetchone()
    if row[0] == 0:
        varsayilan_kategoriler = [
            ('Davranış', 1, 1),
            ('Ödev', 2, 1),
            ('Quiz', 3, 1)
        ]
        
        for kategori in varsayilan_kategoriler:
            try:
                cursor.execute('''
                    INSERT INTO kategori (ad, sira, varsayilan) 
                    VALUES (?, ?, ?)
                ''', kategori)
            except sqlite3.IntegrityError:
                pass
    
    conn.commit()
    conn.close()
    
    return db_path


def get_connection():
    """Veritabanı bağlantısı döndürür."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Dict-like erişim için
    return conn
