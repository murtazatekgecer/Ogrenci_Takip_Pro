"""
Yardımcı fonksiyonlar.
"""
from datetime import datetime


def format_date(date_str, format_type='short'):
    """
    Tarih formatını düzenler.
    format_type: 'short', 'long', 'time'
    """
    if not date_str:
        return '-'
    
    try:
        if isinstance(date_str, str):
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            dt = date_str
        
        if format_type == 'short':
            return dt.strftime('%d.%m.%Y')
        elif format_type == 'long':
            return dt.strftime('%d %B %Y, %H:%M')
        elif format_type == 'time':
            return dt.strftime('%H:%M')
        else:
            return dt.strftime('%d.%m.%Y')
    except:
        return str(date_str)


def calculate_average(values):
    """Ortalama hesaplar, None değerleri atlar."""
    valid_values = [v for v in values if v is not None]
    if not valid_values:
        return None
    return sum(valid_values) / len(valid_values)


def get_grade_color(grade):
    """
    Not değerine göre renk döndürür.
    0-49: Başarısız, 50-54: Geçer, 55-69: Orta, 70-84: İyi, 85-100: Pekiyi
    """
    if grade is None:
        return '#9E9E9E'  # Gri
    
    if grade >= 85:
        return '#4CAF50'  # Yeşil - Pekiyi
    elif grade >= 70:
        return '#8BC34A'  # Açık yeşil - İyi
    elif grade >= 55:
        return '#FFC107'  # Sarı - Orta
    elif grade >= 50:
        return '#FF9800'  # Turuncu - Geçer
    else:
        return '#F44336'  # Kırmızı - Başarısız


def get_grade_text(grade):
    """Not değerine göre metin döndürür. 0-49: Başarısız, 50-54: Geçer, 55-69: Orta, 70-84: İyi, 85-100: Pekiyi"""
    if grade is None:
        return 'Değerlendirilmedi'
    
    if grade >= 85:
        return 'Pekiyi'
    elif grade >= 70:
        return 'İyi'
    elif grade >= 55:
        return 'Orta'
    elif grade >= 50:
        return 'Geçer'
    else:
        return 'Başarısız'


def validate_grade(value):
    """
    Not değerini doğrular ve temizler.
    0-100 arasında bir sayı döndürür veya None.
    """
    if value is None or value == '':
        return None
    
    try:
        grade = float(str(value).replace(',', '.'))
        if grade < 0:
            return 0
        if grade > 100:
            return 100
        return round(grade, 2)
    except:
        return None


def filter_students_by_name(students, search_text):
    """Öğrencileri isme göre filtreler."""
    if not search_text:
        return students
    
    search_lower = search_text.lower()
    return [
        s for s in students
        if search_lower in s.get('ad', '').lower() or 
           search_lower in s.get('soyad', '').lower() or
           search_lower in s.get('okul_no', '').lower()
    ]


def generate_okul_no(sinif_id, mevcut_sayisi):
    """Otomatik okul numarası oluşturur."""
    return f"{sinif_id:02d}{mevcut_sayisi + 1:03d}"


def get_badge_info(badge_id):
    """Rozet bilgilerini döndürür."""
    badges = {
        'star': {'name': 'Yıldız Öğrenci', 'icon': '⭐', 'color': '#FFD700'},
        'perfect': {'name': 'Mükemmel Not', 'icon': '💯', 'color': '#4CAF50'},
        'improved': {'name': 'Gelişme Gösteren', 'icon': '📈', 'color': '#2196F3'},
        'helper': {'name': 'Yardımsever', 'icon': '🤝', 'color': '#9C27B0'},
        'creative': {'name': 'Yaratıcı', 'icon': '💡', 'color': '#FF9800'},
        'leader': {'name': 'Lider', 'icon': '👑', 'color': '#E91E63'},
        'bookworm': {'name': 'Kitap Kurdu', 'icon': '📚', 'color': '#795548'},
        'athlete': {'name': 'Sporcu', 'icon': '🏆', 'color': '#00BCD4'},
    }
    return badges.get(badge_id, {'name': 'Bilinmeyen', 'icon': '❓', 'color': '#9E9E9E'})


def get_all_badges():
    """Tüm rozet listesini döndürür."""
    return [
        {'id': 'star', 'name': 'Yıldız Öğrenci', 'icon': '⭐', 'color': '#FFD700'},
        {'id': 'perfect', 'name': 'Mükemmel Not', 'icon': '💯', 'color': '#4CAF50'},
        {'id': 'improved', 'name': 'Gelişme Gösteren', 'icon': '📈', 'color': '#2196F3'},
        {'id': 'helper', 'name': 'Yardımsever', 'icon': '🤝', 'color': '#9C27B0'},
        {'id': 'creative', 'name': 'Yaratıcı', 'icon': '💡', 'color': '#FF9800'},
        {'id': 'leader', 'name': 'Lider', 'icon': '👑', 'color': '#E91E63'},
        {'id': 'bookworm', 'name': 'Kitap Kurdu', 'icon': '📚', 'color': '#795548'},
        {'id': 'athlete', 'name': 'Sporcu', 'icon': '🏆', 'color': '#00BCD4'},
    ]
