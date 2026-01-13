"""
Veritabanı yönetim modülü - SQLite ile öğrenci, kategori ve görev yönetimi
"""
import sqlite3
import os
from typing import List, Optional, Tuple, Dict
from pathlib import Path


class DatabaseManager:
    """SQLite veritabanı yönetici sınıfı"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Varsayılan veritabanı yolu
            app_data = os.getenv('APPDATA', os.path.expanduser('~'))
            db_dir = os.path.join(app_data, 'OgrenciTakipPro')
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, 'ogrenci_takip.db')
        
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._create_tables()
        self._insert_default_categories()
    
    def _connect(self):
        """Veritabanına bağlan"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
    
    def _create_tables(self):
        """Tabloları oluştur"""
        cursor = self.conn.cursor()
        
        # Öğrenciler tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad TEXT NOT NULL,
                soyad TEXT NOT NULL,
                sinif TEXT NOT NULL,
                numara TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Kategoriler tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                isim TEXT NOT NULL UNIQUE,
                varsayilan INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Görevler/Puanlar tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ogrenci_id INTEGER NOT NULL,
                kategori_id INTEGER NOT NULL,
                isim TEXT NOT NULL,
                puan INTEGER NOT NULL CHECK(puan >= 0 AND puan <= 100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ogrenci_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY (kategori_id) REFERENCES categories(id) ON DELETE CASCADE
            )
        ''')
        
        self.conn.commit()
    
    def _insert_default_categories(self):
        """Varsayılan kategorileri ekle"""
        default_categories = ['Davranış', 'Ödev', 'Quiz']
        cursor = self.conn.cursor()
        
        for kategori in default_categories:
            try:
                cursor.execute(
                    'INSERT OR IGNORE INTO categories (isim, varsayilan) VALUES (?, 1)',
                    (kategori,)
                )
            except sqlite3.IntegrityError:
                pass
        
        self.conn.commit()
    
    # ========== ÖĞRENCİ İŞLEMLERİ ==========
    
    def add_student(self, ad: str, soyad: str, sinif: str, numara: str) -> int:
        """Yeni öğrenci ekle"""
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO students (ad, soyad, sinif, numara) VALUES (?, ?, ?, ?)',
            (ad, soyad, sinif, numara)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def update_student(self, student_id: int, ad: str, soyad: str, sinif: str, numara: str):
        """Öğrenci bilgilerini güncelle"""
        cursor = self.conn.cursor()
        cursor.execute(
            'UPDATE students SET ad=?, soyad=?, sinif=?, numara=? WHERE id=?',
            (ad, soyad, sinif, numara, student_id)
        )
        self.conn.commit()
    
    def delete_student(self, student_id: int):
        """Öğrenciyi sil"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM students WHERE id=?', (student_id,))
        self.conn.commit()
    
    def get_all_students(self) -> List[dict]:
        """Tüm öğrencileri getir"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM students ORDER BY sinif, numara')
        return [dict(row) for row in cursor.fetchall()]
    
    def get_student(self, student_id: int) -> Optional[dict]:
        """Tek öğrenci getir"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM students WHERE id=?', (student_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_students_by_class(self, sinif: str) -> List[dict]:
        """Sınıfa göre öğrencileri getir"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM students WHERE sinif=? ORDER BY numara', (sinif,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_all_classes(self) -> List[str]:
        """Tüm sınıfları getir"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT DISTINCT sinif FROM students ORDER BY sinif')
        return [row['sinif'] for row in cursor.fetchall()]
    
    # ========== KATEGORİ İŞLEMLERİ ==========
    
    def add_category(self, isim: str) -> int:
        """Yeni kategori ekle"""
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO categories (isim, varsayilan) VALUES (?, 0)',
            (isim,)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def update_category(self, category_id: int, isim: str):
        """Kategori adını güncelle"""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE categories SET isim=? WHERE id=?', (isim, category_id))
        self.conn.commit()
    
    def delete_category(self, category_id: int):
        """Kategoriyi sil (varsayılan kategoriler silinebilir)"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM categories WHERE id=?', (category_id,))
        self.conn.commit()
    
    def get_all_categories(self) -> List[dict]:
        """Tüm kategorileri getir"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM categories ORDER BY varsayilan DESC, isim')
        return [dict(row) for row in cursor.fetchall()]
    
    def get_category(self, category_id: int) -> Optional[dict]:
        """Tek kategori getir"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM categories WHERE id=?', (category_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    # ========== GÖREV/PUAN İŞLEMLERİ ==========
    
    def add_task(self, ogrenci_id: int, kategori_id: int, isim: str, puan: int) -> int:
        """Yeni görev/puan ekle"""
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO tasks (ogrenci_id, kategori_id, isim, puan) VALUES (?, ?, ?, ?)',
            (ogrenci_id, kategori_id, isim, puan)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def update_task(self, task_id: int, isim: str, puan: int):
        """Görev bilgilerini güncelle"""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE tasks SET isim=?, puan=? WHERE id=?', (isim, puan, task_id))
        self.conn.commit()
    
    def delete_task(self, task_id: int):
        """Görevi sil"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE id=?', (task_id,))
        self.conn.commit()
    
    def get_student_tasks(self, ogrenci_id: int) -> List[dict]:
        """Öğrencinin tüm görevlerini getir"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT t.*, c.isim as kategori_isim 
            FROM tasks t 
            JOIN categories c ON t.kategori_id = c.id 
            WHERE t.ogrenci_id = ?
            ORDER BY c.isim, t.created_at
        ''', (ogrenci_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_student_tasks_by_category(self, ogrenci_id: int, kategori_id: int) -> List[dict]:
        """Öğrencinin belirli kategorideki görevlerini getir"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM tasks 
            WHERE ogrenci_id = ? AND kategori_id = ?
            ORDER BY created_at
        ''', (ogrenci_id, kategori_id))
        return [dict(row) for row in cursor.fetchall()]
    
    # ========== DEĞERLENDİRME İŞLEMLERİ ==========
    
    def get_student_category_average(self, ogrenci_id: int, kategori_id: int) -> float:
        """Öğrencinin bir kategorideki not ortalamasını hesapla"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT AVG(puan) as ortalama 
            FROM tasks 
            WHERE ogrenci_id = ? AND kategori_id = ?
        ''', (ogrenci_id, kategori_id))
        row = cursor.fetchone()
        return round(row['ortalama'], 2) if row['ortalama'] else 0.0
    
    def get_student_overall_average(self, ogrenci_id: int) -> float:
        """Öğrencinin genel not ortalamasını hesapla"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT AVG(puan) as ortalama 
            FROM tasks 
            WHERE ogrenci_id = ?
        ''', (ogrenci_id,))
        row = cursor.fetchone()
        return round(row['ortalama'], 2) if row['ortalama'] else 0.0
    
    def get_evaluation_data(self) -> List[dict]:
        """Tüm öğrenciler için değerlendirme verilerini getir"""
        students = self.get_all_students()
        categories = self.get_all_categories()
        
        result = []
        for student in students:
            eval_data = {
                'id': student['id'],
                'ad': student['ad'],
                'soyad': student['soyad'],
                'sinif': student['sinif'],
                'numara': student['numara'],
                'kategoriler': {},
                'genel_ortalama': 0.0
            }
            
            category_averages = []
            for cat in categories:
                avg = self.get_student_category_average(student['id'], cat['id'])
                eval_data['kategoriler'][cat['isim']] = avg
                if avg > 0:
                    category_averages.append(avg)
            
            if category_averages:
                eval_data['genel_ortalama'] = round(sum(category_averages) / len(category_averages), 2)
            
            result.append(eval_data)
        
        return result
    
    def get_report_data_by_class(self, sinif: str = None) -> Dict[str, List[dict]]:
        """Sınıf bazlı rapor verilerini getir"""
        if sinif:
            classes = [sinif]
        else:
            classes = self.get_all_classes()
        
        categories = self.get_all_categories()
        report = {}
        
        for current_class in classes:
            students = self.get_students_by_class(current_class)
            class_data = []
            
            for student in students:
                student_data = {
                    'ad': student['ad'],
                    'soyad': student['soyad'],
                    'numara': student['numara'],
                    'kategoriler': {}
                }
                
                for cat in categories:
                    tasks = self.get_student_tasks_by_category(student['id'], cat['id'])
                    avg = self.get_student_category_average(student['id'], cat['id'])
                    student_data['kategoriler'][cat['isim']] = {
                        'gorevler': tasks,
                        'ortalama': avg
                    }
                
                student_data['genel_ortalama'] = self.get_student_overall_average(student['id'])
                class_data.append(student_data)
            
            report[current_class] = class_data
        
        return report
    
    def close(self):
        """Veritabanı bağlantısını kapat"""
        if self.conn:
            self.conn.close()


# Singleton instance
_db_instance = None

def get_database() -> DatabaseManager:
    """Veritabanı instance'ını getir (singleton)"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance
