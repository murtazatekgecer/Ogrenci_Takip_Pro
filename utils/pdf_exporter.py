"""
PDF export modülü - Excel ile aynı formatta
Türkçe karakter desteği ile
"""
from fpdf import FPDF
from typing import Dict, List
import os


class TurkishPDF(FPDF):
    """Türkçe karakter destekli PDF sınıfı"""
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
    
    def header(self):
        self.set_font('Helvetica', 'B', 14)
        self.cell(0, 10, self._safe_text('Ogrenci Takip Raporu'), 0, 1, 'C')
        self.ln(3)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', '', 8)
        self.cell(0, 10, f'Sayfa {self.page_no()}', 0, 0, 'C')
    
    def _safe_text(self, text):
        """Türkçe karakterleri ASCII'ye çevir"""
        if text is None:
            return ""
        
        text = str(text)
        replacements = {
            'ı': 'i', 'İ': 'I',
            'ğ': 'g', 'Ğ': 'G',
            'ü': 'u', 'Ü': 'U',
            'ş': 's', 'Ş': 'S',
            'ö': 'o', 'Ö': 'O',
            'ç': 'c', 'Ç': 'C',
        }
        
        for tr_char, en_char in replacements.items():
            text = text.replace(tr_char, en_char)
        
        return text


def export_to_pdf(report_data: Dict[str, List[dict]], categories: List[dict], filepath: str) -> str:
    """
    Öğrenci verilerini PDF dosyasına export et - Excel formatında
    """
    pdf = TurkishPDF()
    
    for sinif, students in report_data.items():
        if not students:
            continue
        
        # Tüm görev isimlerini kategorilere göre topla
        category_tasks = {}
        for cat in categories:
            category_tasks[cat['isim']] = set()
            for student in students:
                cat_data = student['kategoriler'].get(cat['isim'], {})
                gorevler = cat_data.get('gorevler', [])
                for gorev in gorevler:
                    category_tasks[cat['isim']].add(gorev['isim'])
            category_tasks[cat['isim']] = sorted(category_tasks[cat['isim']])
        
        pdf.add_page('L')  # Landscape mode
        
        # Sınıf başlığı
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_fill_color(68, 114, 196)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 10, pdf._safe_text(f'Sinif: {sinif}'), 0, 1, 'L', fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)
        
        # Sütun yapısını hesapla
        fixed_cols = [8, 15, 25, 25]  # No, Numara, Ad, Soyad
        fixed_width = sum(fixed_cols)
        
        # Kategori sütunlarını hesapla
        total_task_cols = 0
        for cat in categories:
            tasks = category_tasks.get(cat['isim'], [])
            total_task_cols += len(tasks) + 1  # görevler + ortalama
        
        remaining_width = 277 - fixed_width - 18  # 277 = A4 landscape, 18 = genel
        if total_task_cols > 0:
            task_col_width = remaining_width / total_task_cols
            task_col_width = min(task_col_width, 25)  # max 25
            task_col_width = max(task_col_width, 12)  # min 12
        else:
            task_col_width = 20
        
        # Sütun genişlikleri listesi
        col_widths = fixed_cols.copy()
        col_info = {}  # {kategori: {'start_idx': x, 'task_count': y}}
        
        for cat in categories:
            cat_name = cat['isim']
            tasks = category_tasks.get(cat_name, [])
            col_info[cat_name] = {
                'start_idx': len(col_widths),
                'tasks': tasks,
                'task_count': len(tasks)
            }
            for _ in tasks:
                col_widths.append(task_col_width)
            col_widths.append(task_col_width)  # Ortalama
        
        col_widths.append(18)  # Genel ortalama
        
        # ========== SATIR 1: Kategori başlıkları ==========
        pdf.set_font('Helvetica', 'B', 8)
        x_start = pdf.get_x()
        y_start = pdf.get_y()
        
        # Sabit başlıklar (2 satır yüksekliğinde)
        row_height = 7
        pdf.set_fill_color(68, 114, 196)
        pdf.set_text_color(255, 255, 255)
        
        # No, Numara, Ad, Soyad - 2 satır birleşik
        for i, header in enumerate(['No', 'Numara', 'Ad', 'Soyad']):
            pdf.set_xy(x_start + sum(col_widths[:i]), y_start)
            pdf.cell(col_widths[i], row_height * 2, header, 1, 0, 'C', True)
        
        # Kategori başlıkları
        current_x = x_start + sum(fixed_cols)
        for cat in categories:
            cat_name = cat['isim']
            info = col_info[cat_name]
            cat_width = (info['task_count'] + 1) * task_col_width
            
            pdf.set_xy(current_x, y_start)
            pdf.set_fill_color(91, 155, 213)
            pdf.cell(cat_width, row_height, pdf._safe_text(cat_name), 1, 0, 'C', True)
            current_x += cat_width
        
        # Genel Ortalama başlığı
        pdf.set_xy(current_x, y_start)
        pdf.set_fill_color(68, 114, 196)
        pdf.cell(col_widths[-1], row_height * 2, 'Genel\nOrt.', 1, 0, 'C', True)
        
        # ========== SATIR 2: Görev başlıkları ==========
        pdf.set_xy(x_start + sum(fixed_cols), y_start + row_height)
        pdf.set_font('Helvetica', 'B', 6)
        pdf.set_fill_color(142, 169, 219)
        
        for cat in categories:
            cat_name = cat['isim']
            info = col_info[cat_name]
            tasks = info['tasks']
            
            for task_name in tasks:
                short_name = pdf._safe_text(task_name[:10])
                pdf.cell(task_col_width, row_height, short_name, 1, 0, 'C', True)
            
            pdf.cell(task_col_width, row_height, 'Ort.', 1, 0, 'C', True)
        
        pdf.ln()
        pdf.set_y(y_start + row_height * 2)
        
        # ========== VERİ SATIRLARI ==========
        pdf.set_font('Helvetica', '', 7)
        pdf.set_text_color(0, 0, 0)
        
        for idx, student in enumerate(students, 1):
            y_pos = pdf.get_y()
            
            # Sayfa kontrolü
            if y_pos > 185:
                pdf.add_page('L')
                y_pos = pdf.get_y()
                
                # Başlıkları tekrar yaz
                pdf.set_font('Helvetica', 'B', 8)
                x_start = pdf.get_x()
                y_start = pdf.get_y()
                
                pdf.set_fill_color(68, 114, 196)
                pdf.set_text_color(255, 255, 255)
                
                for i, header in enumerate(['No', 'Numara', 'Ad', 'Soyad']):
                    pdf.set_xy(x_start + sum(col_widths[:i]), y_start)
                    pdf.cell(col_widths[i], row_height * 2, header, 1, 0, 'C', True)
                
                current_x = x_start + sum(fixed_cols)
                for cat in categories:
                    cat_name = cat['isim']
                    info = col_info[cat_name]
                    cat_width = (info['task_count'] + 1) * task_col_width
                    
                    pdf.set_xy(current_x, y_start)
                    pdf.set_fill_color(91, 155, 213)
                    pdf.cell(cat_width, row_height, pdf._safe_text(cat_name), 1, 0, 'C', True)
                    current_x += cat_width
                
                pdf.set_xy(current_x, y_start)
                pdf.set_fill_color(68, 114, 196)
                pdf.cell(col_widths[-1], row_height * 2, 'Genel\nOrt.', 1, 0, 'C', True)
                
                pdf.set_xy(x_start + sum(fixed_cols), y_start + row_height)
                pdf.set_font('Helvetica', 'B', 6)
                pdf.set_fill_color(142, 169, 219)
                
                for cat in categories:
                    cat_name = cat['isim']
                    info = col_info[cat_name]
                    tasks = info['tasks']
                    
                    for task_name in tasks:
                        short_name = pdf._safe_text(task_name[:10])
                        pdf.cell(task_col_width, row_height, short_name, 1, 0, 'C', True)
                    
                    pdf.cell(task_col_width, row_height, 'Ort.', 1, 0, 'C', True)
                
                pdf.set_y(y_start + row_height * 2)
                pdf.set_font('Helvetica', '', 7)
                pdf.set_text_color(0, 0, 0)
                y_pos = pdf.get_y()
            
            # Satır arka plan rengi
            if idx % 2 == 0:
                row_bg = (245, 245, 245)
            else:
                row_bg = (255, 255, 255)
            
            x_pos = pdf.l_margin
            
            # Sabit sütunlar
            pdf.set_fill_color(*row_bg)
            pdf.set_xy(x_pos, y_pos)
            pdf.cell(col_widths[0], 6, str(idx), 1, 0, 'C', True)
            x_pos += col_widths[0]
            
            pdf.set_xy(x_pos, y_pos)
            pdf.cell(col_widths[1], 6, pdf._safe_text(str(student['numara'])[:8]), 1, 0, 'C', True)
            x_pos += col_widths[1]
            
            pdf.set_xy(x_pos, y_pos)
            pdf.cell(col_widths[2], 6, pdf._safe_text(student['ad'][:12]), 1, 0, 'L', True)
            x_pos += col_widths[2]
            
            pdf.set_xy(x_pos, y_pos)
            pdf.cell(col_widths[3], 6, pdf._safe_text(student['soyad'][:12]), 1, 0, 'L', True)
            x_pos += col_widths[3]
            
            # Kategori verileri
            for cat in categories:
                cat_name = cat['isim']
                info = col_info[cat_name]
                tasks = info['tasks']
                
                cat_data = student['kategoriler'].get(cat_name, {})
                gorevler = cat_data.get('gorevler', [])
                task_scores = {g['isim']: g['puan'] for g in gorevler}
                
                # Görev puanları
                for task_name in tasks:
                    puan = task_scores.get(task_name, None)
                    
                    if puan is not None:
                        if puan >= 70:
                            pdf.set_fill_color(198, 239, 206)
                        elif puan >= 50:
                            pdf.set_fill_color(255, 235, 156)
                        else:
                            pdf.set_fill_color(255, 199, 206)
                        text = str(puan)
                    else:
                        pdf.set_fill_color(*row_bg)
                        text = '-'
                    
                    pdf.set_xy(x_pos, y_pos)
                    pdf.cell(task_col_width, 6, text, 1, 0, 'C', True)
                    x_pos += task_col_width
                
                # Kategori ortalaması
                avg = cat_data.get('ortalama', 0)
                if avg >= 70:
                    pdf.set_fill_color(198, 239, 206)
                elif avg >= 50:
                    pdf.set_fill_color(255, 235, 156)
                elif avg > 0:
                    pdf.set_fill_color(255, 199, 206)
                else:
                    pdf.set_fill_color(*row_bg)
                
                pdf.set_font('Helvetica', 'B', 7)
                pdf.set_xy(x_pos, y_pos)
                pdf.cell(task_col_width, 6, f'{avg:.0f}' if avg else '-', 1, 0, 'C', True)
                pdf.set_font('Helvetica', '', 7)
                x_pos += task_col_width
            
            # Genel ortalama
            genel = student.get('genel_ortalama', 0)
            if genel >= 70:
                pdf.set_fill_color(198, 239, 206)
            elif genel >= 50:
                pdf.set_fill_color(255, 235, 156)
            elif genel > 0:
                pdf.set_fill_color(255, 199, 206)
            else:
                pdf.set_fill_color(*row_bg)
            
            pdf.set_font('Helvetica', 'B', 7)
            pdf.set_xy(x_pos, y_pos)
            pdf.cell(col_widths[-1], 6, f'{genel:.0f}' if genel else '-', 1, 0, 'C', True)
            pdf.set_font('Helvetica', '', 7)
            
            pdf.set_y(y_pos + 6)
        
        # Sınıf özeti
        pdf.ln(3)
        if students:
            class_avg = sum(s.get('genel_ortalama', 0) for s in students) / len(students)
            pdf.set_font('Helvetica', 'B', 10)
            pdf.cell(0, 8, pdf._safe_text(f'Sinif Ortalamasi: {class_avg:.1f}'), 0, 1, 'R')
    
    pdf.output(filepath)
    return filepath
