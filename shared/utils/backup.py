"""
Yedekleme ve geri yükleme işlemleri.
"""
import os
import json
import csv
from datetime import datetime
from database.models import get_connection, get_db_path


class BackupManager:
    """Yedekleme işlemlerini yöneten sınıf."""
    
    def __init__(self):
        self.tables = ['sinif', 'ogrenci', 'kategori', 'not_basligi', 'not_']
    
    def create_backup_json(self, filepath):
        """Tüm veritabanını JSON formatında yedekler."""
        conn = get_connection()
        cursor = conn.cursor()
        
        backup_data = {
            'backup_date': datetime.now().isoformat(),
            'version': '1.0',
            'tables': {}
        }
        
        for table in self.tables:
            cursor.execute(f'SELECT * FROM {table}')
            rows = cursor.fetchall()
            backup_data['tables'][table] = [dict(row) for row in rows]
        
        conn.close()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
        
        return filepath
    
    def restore_backup_json(self, filepath):
        """JSON yedeğinden veritabanını geri yükler."""
        with open(filepath, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        if 'tables' not in backup_data:
            raise ValueError("Geçersiz yedek dosyası!")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Mevcut verileri temizle (ters sırada - foreign key kısıtlamaları için)
            for table in reversed(self.tables):
                cursor.execute(f'DELETE FROM {table}')
            
            # Yedekteki verileri yükle
            for table in self.tables:
                if table in backup_data['tables']:
                    for row in backup_data['tables'][table]:
                        columns = ', '.join(row.keys())
                        placeholders = ', '.join(['?' for _ in row])
                        cursor.execute(
                            f'INSERT INTO {table} ({columns}) VALUES ({placeholders})',
                            list(row.values())
                        )
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
        
        return True
    
    def create_backup_csv(self, folder_path):
        """Tüm veritabanını CSV dosyalarına yedekler."""
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        conn = get_connection()
        cursor = conn.cursor()
        
        created_files = []
        
        for table in self.tables:
            cursor.execute(f'SELECT * FROM {table}')
            rows = cursor.fetchall()
            
            if rows:
                filepath = os.path.join(folder_path, f'{table}.csv')
                with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    # Başlıklar
                    writer.writerow(rows[0].keys())
                    # Veriler
                    for row in rows:
                        writer.writerow(row)
                created_files.append(filepath)
        
        conn.close()
        
        # Metadata dosyası
        meta_path = os.path.join(folder_path, '_backup_info.json')
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump({
                'backup_date': datetime.now().isoformat(),
                'version': '1.0',
                'files': [os.path.basename(f) for f in created_files]
            }, f, ensure_ascii=False, indent=2)
        
        return folder_path
    
    def restore_backup_csv(self, folder_path):
        """CSV dosyalarından veritabanını geri yükler."""
        meta_path = os.path.join(folder_path, '_backup_info.json')
        if not os.path.exists(meta_path):
            raise ValueError("Geçersiz yedek klasörü! _backup_info.json bulunamadı.")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Mevcut verileri temizle
            for table in reversed(self.tables):
                cursor.execute(f'DELETE FROM {table}')
            
            # CSV dosyalarını yükle
            for table in self.tables:
                csv_path = os.path.join(folder_path, f'{table}.csv')
                if os.path.exists(csv_path):
                    with open(csv_path, 'r', encoding='utf-8-sig', newline='') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            columns = ', '.join(row.keys())
                            placeholders = ', '.join(['?' for _ in row])
                            values = []
                            for v in row.values():
                                # Boş string'leri None'a çevir
                                if v == '':
                                    values.append(None)
                                else:
                                    values.append(v)
                            cursor.execute(
                                f'INSERT INTO {table} ({columns}) VALUES ({placeholders})',
                                values
                            )
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
        
        return True
    
    def get_backup_info(self, filepath):
        """Yedek dosyasının bilgilerini döndürür."""
        if filepath.endswith('.json'):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    'type': 'JSON',
                    'date': data.get('backup_date', 'Bilinmiyor'),
                    'version': data.get('version', 'Bilinmiyor'),
                    'tables': list(data.get('tables', {}).keys())
                }
        elif os.path.isdir(filepath):
            meta_path = os.path.join(filepath, '_backup_info.json')
            if os.path.exists(meta_path):
                with open(meta_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {
                        'type': 'CSV',
                        'date': data.get('backup_date', 'Bilinmiyor'),
                        'version': data.get('version', 'Bilinmiyor'),
                        'files': data.get('files', [])
                    }
        
        return None
    
    def create_auto_backup(self, backup_dir=None):
        """Otomatik yedek oluşturur (tarih damgalı)."""
        if backup_dir is None:
            backup_dir = os.path.dirname(get_db_path())
        
        backup_folder = os.path.join(backup_dir, 'backups')
        if not os.path.exists(backup_folder):
            os.makedirs(backup_folder)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join(backup_folder, f'backup_{timestamp}.json')
        
        return self.create_backup_json(filepath)
