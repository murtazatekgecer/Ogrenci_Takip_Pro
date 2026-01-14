"""
Veritabanı yönetim sınıfı.
Tüm CRUD işlemleri ve iş mantığı burada tanımlanır.
"""
import sqlite3
import json
from datetime import datetime
from .models import get_connection


class DatabaseManager:
    """Veritabanı işlemlerini yöneten sınıf."""
    
    def __init__(self):
        self.undo_stack = []
        self.max_undo = 50
    
    # ==================== SINIF İŞLEMLERİ ====================
    
    def get_all_siniflar(self):
        """Tüm sınıfları döndürür."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sinif ORDER BY ad')
        result = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return result
    
    def add_sinif(self, ad, donem=''):
        """Yeni sınıf ekler."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO sinif (ad, donem) VALUES (?, ?)',
            (ad, donem)
        )
        sinif_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        self._add_to_undo('INSERT', 'sinif', sinif_id, None, {'ad': ad, 'donem': donem})
        return sinif_id
    
    def update_sinif(self, sinif_id, ad, donem=''):
        """Sınıf bilgilerini günceller."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Eski veriyi al
        cursor.execute('SELECT * FROM sinif WHERE id = ?', (sinif_id,))
        old_data = dict(cursor.fetchone())
        
        cursor.execute(
            'UPDATE sinif SET ad = ?, donem = ? WHERE id = ?',
            (ad, donem, sinif_id)
        )
        conn.commit()
        conn.close()
        
        self._add_to_undo('UPDATE', 'sinif', sinif_id, old_data, {'ad': ad, 'donem': donem})
    
    def delete_sinif(self, sinif_id):
        """Sınıfı siler."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Eski veriyi al
        cursor.execute('SELECT * FROM sinif WHERE id = ?', (sinif_id,))
        old_data = dict(cursor.fetchone())
        
        cursor.execute('DELETE FROM sinif WHERE id = ?', (sinif_id,))
        conn.commit()
        conn.close()
        
        self._add_to_undo('DELETE', 'sinif', sinif_id, old_data, None)
    
    def copy_sinif_to_new_term(self, sinif_id, new_sinif_ad, new_donem):
        """
        Sınıfı yeni dönem/seneye kopyalar.
        Öğrenciler kopyalanır, notlar sıfırlanır.
        """
        conn = get_connection()
        cursor = conn.cursor()
        
        # Yeni sınıf oluştur
        cursor.execute(
            'INSERT INTO sinif (ad, donem) VALUES (?, ?)',
            (new_sinif_ad, new_donem)
        )
        new_sinif_id = cursor.lastrowid
        
        # Öğrencileri kopyala
        cursor.execute('''
            INSERT INTO ogrenci (ad, soyad, okul_no, sinif_id)
            SELECT ad, soyad, okul_no || '_' || ?, ?
            FROM ogrenci WHERE sinif_id = ?
        ''', (new_sinif_id, new_sinif_id, sinif_id))
        
        conn.commit()
        conn.close()
        
        return new_sinif_id
    
    # ==================== ÖĞRENCİ İŞLEMLERİ ====================
    
    def get_all_ogrenciler(self, sinif_id=None):
        """Tüm öğrencileri veya belirli bir sınıfın öğrencilerini döndürür."""
        conn = get_connection()
        cursor = conn.cursor()
        
        if sinif_id:
            cursor.execute('''
                SELECT o.*, s.ad as sinif_adi 
                FROM ogrenci o 
                LEFT JOIN sinif s ON o.sinif_id = s.id 
                WHERE o.sinif_id = ?
                ORDER BY o.soyad, o.ad
            ''', (sinif_id,))
        else:
            cursor.execute('''
                SELECT o.*, s.ad as sinif_adi 
                FROM ogrenci o 
                LEFT JOIN sinif s ON o.sinif_id = s.id 
                ORDER BY o.soyad, o.ad
            ''')
        
        result = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return result
    
    def get_ogrenci_by_id(self, ogrenci_id):
        """Belirli bir öğrenciyi döndürür."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT o.*, s.ad as sinif_adi 
            FROM ogrenci o 
            LEFT JOIN sinif s ON o.sinif_id = s.id 
            WHERE o.id = ?
        ''', (ogrenci_id,))
        row = cursor.fetchone()
        result = dict(row) if row else None
        conn.close()
        return result
    
    def add_ogrenci(self, ad, soyad, okul_no, sinif_id):
        """Yeni öğrenci ekler."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO ogrenci (ad, soyad, okul_no, sinif_id) VALUES (?, ?, ?, ?)',
            (ad, soyad, okul_no, sinif_id)
        )
        ogrenci_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        self._add_to_undo('INSERT', 'ogrenci', ogrenci_id, None, 
                          {'ad': ad, 'soyad': soyad, 'okul_no': okul_no, 'sinif_id': sinif_id})
        return ogrenci_id
    
    def update_ogrenci(self, ogrenci_id, ad, soyad, okul_no, sinif_id):
        """Öğrenci bilgilerini günceller."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Eski veriyi al
        cursor.execute('SELECT * FROM ogrenci WHERE id = ?', (ogrenci_id,))
        old_data = dict(cursor.fetchone())
        
        cursor.execute(
            'UPDATE ogrenci SET ad = ?, soyad = ?, okul_no = ?, sinif_id = ? WHERE id = ?',
            (ad, soyad, okul_no, sinif_id, ogrenci_id)
        )
        conn.commit()
        conn.close()
        
        self._add_to_undo('UPDATE', 'ogrenci', ogrenci_id, old_data,
                          {'ad': ad, 'soyad': soyad, 'okul_no': okul_no, 'sinif_id': sinif_id})
    
    def delete_ogrenci(self, ogrenci_id):
        """Öğrenciyi siler."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Eski veriyi al
        cursor.execute('SELECT * FROM ogrenci WHERE id = ?', (ogrenci_id,))
        old_data = dict(cursor.fetchone())
        
        cursor.execute('DELETE FROM ogrenci WHERE id = ?', (ogrenci_id,))
        conn.commit()
        conn.close()
        
        self._add_to_undo('DELETE', 'ogrenci', ogrenci_id, old_data, None)
    
    def update_ogrenci_rozetler(self, ogrenci_id, rozetler):
        """Öğrenci rozetlerini günceller."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE ogrenci SET rozetler = ? WHERE id = ?',
            (json.dumps(rozetler), ogrenci_id)
        )
        conn.commit()
        conn.close()
    
    def filter_ogrenciler_by_average(self, sinif_id, operator, value):
        """
        Öğrencileri ortalamaya göre filtreler.
        operator: '<', '>', '<=', '>=', '='
        """
        ogrenciler = self.get_all_ogrenciler(sinif_id)
        filtered = []
        
        for ogrenci in ogrenciler:
            avg = self.get_ogrenci_genel_ortalama(ogrenci['id'])
            if avg is None:
                continue
            
            if operator == '<' and avg < value:
                filtered.append(ogrenci)
            elif operator == '>' and avg > value:
                filtered.append(ogrenci)
            elif operator == '<=' and avg <= value:
                filtered.append(ogrenci)
            elif operator == '>=' and avg >= value:
                filtered.append(ogrenci)
            elif operator == '=' and avg == value:
                filtered.append(ogrenci)
        
        return filtered
    
    # ==================== KATEGORİ İŞLEMLERİ ====================
    
    def get_all_kategoriler(self):
        """Tüm kategorileri döndürür."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM kategori ORDER BY sira')
        result = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return result
    
    def add_kategori(self, ad, sira=0):
        """Yeni kategori ekler."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO kategori (ad, sira, varsayilan) VALUES (?, ?, 0)',
            (ad, sira)
        )
        kategori_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        self._add_to_undo('INSERT', 'kategori', kategori_id, None, {'ad': ad, 'sira': sira})
        return kategori_id
    
    def update_kategori(self, kategori_id, ad, sira=None):
        """Kategori bilgilerini günceller."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Eski veriyi al
        cursor.execute('SELECT * FROM kategori WHERE id = ?', (kategori_id,))
        old_data = dict(cursor.fetchone())
        
        if sira is not None:
            cursor.execute(
                'UPDATE kategori SET ad = ?, sira = ? WHERE id = ?',
                (ad, sira, kategori_id)
            )
        else:
            cursor.execute(
                'UPDATE kategori SET ad = ? WHERE id = ?',
                (ad, kategori_id)
            )
        conn.commit()
        conn.close()
        
        self._add_to_undo('UPDATE', 'kategori', kategori_id, old_data, {'ad': ad, 'sira': sira})
    
    def delete_kategori(self, kategori_id):
        """Kategoriyi siler."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Eski veriyi al
        cursor.execute('SELECT * FROM kategori WHERE id = ?', (kategori_id,))
        old_data = dict(cursor.fetchone())
        
        cursor.execute('DELETE FROM kategori WHERE id = ?', (kategori_id,))
        conn.commit()
        conn.close()
        
        self._add_to_undo('DELETE', 'kategori', kategori_id, old_data, None)
    
    # ==================== NOT BAŞLIĞI İŞLEMLERİ ====================
    
    def get_not_basliklari(self, kategori_id=None, sinif_id=None):
        """Not başlıklarını döndürür."""
        conn = get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT nb.*, k.ad as kategori_adi, s.ad as sinif_adi
            FROM not_basligi nb
            LEFT JOIN kategori k ON nb.kategori_id = k.id
            LEFT JOIN sinif s ON nb.sinif_id = s.id
            WHERE 1=1
        '''
        params = []
        
        if kategori_id:
            query += ' AND nb.kategori_id = ?'
            params.append(kategori_id)
        if sinif_id:
            query += ' AND nb.sinif_id = ?'
            params.append(sinif_id)
        
        query += ' ORDER BY nb.tarih DESC'
        
        cursor.execute(query, params)
        result = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return result
    
    def add_not_basligi(self, baslik, kategori_id, sinif_id):
        """Yeni not başlığı ekler."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO not_basligi (baslik, kategori_id, sinif_id) VALUES (?, ?, ?)',
            (baslik, kategori_id, sinif_id)
        )
        baslik_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        self._add_to_undo('INSERT', 'not_basligi', baslik_id, None,
                          {'baslik': baslik, 'kategori_id': kategori_id, 'sinif_id': sinif_id})
        return baslik_id
    
    def update_not_basligi(self, baslik_id, baslik):
        """Not başlığını günceller."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM not_basligi WHERE id = ?', (baslik_id,))
        old_data = dict(cursor.fetchone())
        
        cursor.execute(
            'UPDATE not_basligi SET baslik = ? WHERE id = ?',
            (baslik, baslik_id)
        )
        conn.commit()
        conn.close()
        
        self._add_to_undo('UPDATE', 'not_basligi', baslik_id, old_data, {'baslik': baslik})
    
    def delete_not_basligi(self, baslik_id):
        """Not başlığını ve ilgili notları siler."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM not_basligi WHERE id = ?', (baslik_id,))
        old_data = dict(cursor.fetchone())
        
        cursor.execute('DELETE FROM not_basligi WHERE id = ?', (baslik_id,))
        conn.commit()
        conn.close()
        
        self._add_to_undo('DELETE', 'not_basligi', baslik_id, old_data, None)
    
    # ==================== NOT İŞLEMLERİ ====================
    
    def get_notlar(self, ogrenci_id=None, baslik_id=None):
        """Notları döndürür."""
        conn = get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT n.*, nb.baslik as not_basligi, k.ad as kategori_adi,
                   o.ad as ogrenci_adi, o.soyad as ogrenci_soyadi
            FROM not_ n
            LEFT JOIN not_basligi nb ON n.baslik_id = nb.id
            LEFT JOIN kategori k ON nb.kategori_id = k.id
            LEFT JOIN ogrenci o ON n.ogrenci_id = o.id
            WHERE 1=1
        '''
        params = []
        
        if ogrenci_id:
            query += ' AND n.ogrenci_id = ?'
            params.append(ogrenci_id)
        if baslik_id:
            query += ' AND n.baslik_id = ?'
            params.append(baslik_id)
        
        query += ' ORDER BY nb.tarih DESC'
        
        cursor.execute(query, params)
        result = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return result
    
    def add_or_update_not(self, ogrenci_id, baslik_id, puan):
        """Not ekler veya günceller."""
        conn = get_connection()
        cursor = conn.cursor()
        
        # Mevcut not var mı kontrol et
        cursor.execute(
            'SELECT * FROM not_ WHERE ogrenci_id = ? AND baslik_id = ?',
            (ogrenci_id, baslik_id)
        )
        existing = cursor.fetchone()
        
        if existing:
            old_data = dict(existing)
            cursor.execute(
                '''UPDATE not_ SET puan = ?, guncelleme_tarihi = CURRENT_TIMESTAMP 
                   WHERE ogrenci_id = ? AND baslik_id = ?''',
                (puan, ogrenci_id, baslik_id)
            )
            self._add_to_undo('UPDATE', 'not_', existing['id'], old_data, {'puan': puan})
        else:
            cursor.execute(
                'INSERT INTO not_ (ogrenci_id, baslik_id, puan) VALUES (?, ?, ?)',
                (ogrenci_id, baslik_id, puan)
            )
            not_id = cursor.lastrowid
            self._add_to_undo('INSERT', 'not_', not_id, None,
                              {'ogrenci_id': ogrenci_id, 'baslik_id': baslik_id, 'puan': puan})
        
        conn.commit()
        conn.close()
    
    def add_bulk_notlar(self, baslik_id, notlar_dict):
        """
        Toplu not girişi yapar.
        notlar_dict: {ogrenci_id: puan, ...}
        """
        for ogrenci_id, puan in notlar_dict.items():
            self.add_or_update_not(ogrenci_id, baslik_id, puan)
    
    def delete_not(self, ogrenci_id, baslik_id):
        """Notu siler."""
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT * FROM not_ WHERE ogrenci_id = ? AND baslik_id = ?',
            (ogrenci_id, baslik_id)
        )
        old_data = cursor.fetchone()
        if old_data:
            old_data = dict(old_data)
            cursor.execute(
                'DELETE FROM not_ WHERE ogrenci_id = ? AND baslik_id = ?',
                (ogrenci_id, baslik_id)
            )
            conn.commit()
            self._add_to_undo('DELETE', 'not_', old_data['id'], old_data, None)
        
        conn.close()
    
    # ==================== ORTALAMA HESAPLAMALARI ====================
    
    def get_ogrenci_kategori_ortalama(self, ogrenci_id, kategori_id):
        """Öğrencinin bir kategorideki ortalamasını hesaplar."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT AVG(n.puan) as ortalama
            FROM not_ n
            JOIN not_basligi nb ON n.baslik_id = nb.id
            WHERE n.ogrenci_id = ? AND nb.kategori_id = ?
        ''', (ogrenci_id, kategori_id))
        
        row = cursor.fetchone()
        conn.close()
        return row['ortalama'] if row and row['ortalama'] else None
    
    def get_ogrenci_genel_ortalama(self, ogrenci_id):
        """Öğrencinin genel ortalamasını hesaplar (kategori ortalamalarının ortalaması)."""
        kategoriler = self.get_all_kategoriler()
        ortalamalar = []
        
        for kategori in kategoriler:
            avg = self.get_ogrenci_kategori_ortalama(ogrenci_id, kategori['id'])
            if avg is not None:
                ortalamalar.append(avg)
        
        if ortalamalar:
            return sum(ortalamalar) / len(ortalamalar)
        return None
    
    def get_sinif_kategori_ortalama(self, sinif_id, kategori_id):
        """Sınıfın bir kategorideki ortalamasını hesaplar. sinif_id None ise tüm okulu hesaplar."""
        conn = get_connection()
        cursor = conn.cursor()
        
        if sinif_id:
            cursor.execute('''
                SELECT AVG(n.puan) as ortalama
                FROM not_ n
                JOIN not_basligi nb ON n.baslik_id = nb.id
                JOIN ogrenci o ON n.ogrenci_id = o.id
                WHERE o.sinif_id = ? AND nb.kategori_id = ?
            ''', (sinif_id, kategori_id))
        else:
             cursor.execute('''
                SELECT AVG(n.puan) as ortalama
                FROM not_ n
                JOIN not_basligi nb ON n.baslik_id = nb.id
                WHERE nb.kategori_id = ?
            ''', (kategori_id,))
        
        row = cursor.fetchone()
        conn.close()
        return row['ortalama'] if row and row['ortalama'] else None
    
    def get_sinif_genel_ortalama(self, sinif_id):
        """Sınıfın genel ortalamasını hesaplar."""
        kategoriler = self.get_all_kategoriler()
        ortalamalar = []
        
        for kategori in kategoriler:
            avg = self.get_sinif_kategori_ortalama(sinif_id, kategori['id'])
            if avg is not None:
                ortalamalar.append(avg)
        
        if ortalamalar:
            return sum(ortalamalar) / len(ortalamalar)
        return None
    
    def get_ogrenci_tum_notlar(self, ogrenci_id):
        """Öğrencinin tüm notlarını kategorilere göre gruplandırılmış döndürür."""
        kategoriler = self.get_all_kategoriler()
        result = {}
        
        for kategori in kategoriler:
            result[kategori['ad']] = {
                'kategori_id': kategori['id'],
                'notlar': [],
                'ortalama': self.get_ogrenci_kategori_ortalama(ogrenci_id, kategori['id'])
            }
            
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT n.puan, nb.baslik, nb.tarih
                FROM not_ n
                JOIN not_basligi nb ON n.baslik_id = nb.id
                WHERE n.ogrenci_id = ? AND nb.kategori_id = ?
                ORDER BY nb.tarih
            ''', (ogrenci_id, kategori['id']))
            
            result[kategori['ad']]['notlar'] = [dict(row) for row in cursor.fetchall()]
            conn.close()
        
        return result
    
    def get_sinif_not_dagilimi(self, sinif_id):
        """Sınıfın not dağılımını döndürür (grafik için)."""
        ogrenciler = self.get_all_ogrenciler(sinif_id)
        notlar = []
        
        for ogrenci in ogrenciler:
            avg = self.get_ogrenci_genel_ortalama(ogrenci['id'])
            if avg is not None:
                notlar.append(avg)
        
        return notlar
    
    # ==================== UNDO İŞLEMLERİ ====================
    
    def _add_to_undo(self, islem_tipi, tablo_adi, kayit_id, eski_veri, yeni_veri):
        """İşlemi undo stack'e ekler."""
        self.undo_stack.append({
            'islem_tipi': islem_tipi,
            'tablo_adi': tablo_adi,
            'kayit_id': kayit_id,
            'eski_veri': eski_veri,
            'yeni_veri': yeni_veri
        })
        
        # Stack boyutunu sınırla
        if len(self.undo_stack) > self.max_undo:
            self.undo_stack.pop(0)
    
    def undo(self):
        """Son işlemi geri alır."""
        if not self.undo_stack:
            return False
        
        islem = self.undo_stack.pop()
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            if islem['islem_tipi'] == 'INSERT':
                # Eklenen kaydı sil
                cursor.execute(
                    f"DELETE FROM {islem['tablo_adi']} WHERE id = ?",
                    (islem['kayit_id'],)
                )
            
            elif islem['islem_tipi'] == 'UPDATE':
                # Eski veriyi geri yükle
                eski = islem['eski_veri']
                columns = ', '.join([f"{k} = ?" for k in eski.keys() if k != 'id'])
                values = [v for k, v in eski.items() if k != 'id']
                values.append(islem['kayit_id'])
                cursor.execute(
                    f"UPDATE {islem['tablo_adi']} SET {columns} WHERE id = ?",
                    values
                )
            
            elif islem['islem_tipi'] == 'DELETE':
                # Silinen kaydı geri ekle
                eski = islem['eski_veri']
                columns = ', '.join(eski.keys())
                placeholders = ', '.join(['?' for _ in eski])
                cursor.execute(
                    f"INSERT INTO {islem['tablo_adi']} ({columns}) VALUES ({placeholders})",
                    list(eski.values())
                )
            
            conn.commit()
            conn.close()
            return True
        
        except Exception as e:
            conn.rollback()
            conn.close()
            raise e
    
    def can_undo(self):
        """Geri alınabilecek işlem var mı kontrol eder."""
        return len(self.undo_stack) > 0
    
    def get_undo_description(self):
        """Son geri alınabilecek işlemin açıklamasını döndürür."""
        if not self.undo_stack:
            return None
        
        islem = self.undo_stack[-1]
        tablo_map = {
            'sinif': 'Sınıf',
            'ogrenci': 'Öğrenci',
            'kategori': 'Kategori',
            'not_basligi': 'Not Başlığı',
            'not_': 'Not'
        }
        islem_map = {
            'INSERT': 'ekleme',
            'UPDATE': 'güncelleme',
            'DELETE': 'silme'
        }
        
        tablo = tablo_map.get(islem['tablo_adi'], islem['tablo_adi'])
        tip = islem_map.get(islem['islem_tipi'], islem['islem_tipi'])
        
        return f"{tablo} {tip} işlemini geri al"
