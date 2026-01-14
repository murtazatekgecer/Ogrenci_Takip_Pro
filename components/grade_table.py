"""
Toplu not girişi tablosu bileşeni.
Tab/Enter ile hızlı navigasyon destekli.
"""
import flet as ft
from utils.helpers import validate_grade, get_grade_color


class GradeTable(ft.Container):
    """Toplu not girişi tablosu."""
    
    def __init__(self, db_manager, sinif_id, baslik_id=None, on_save=None, 
                 baslik_ids=None, baslik_name=None):
        super().__init__()
        self.db = db_manager
        self.sinif_id = sinif_id
        self.baslik_id = baslik_id
        self.baslik_ids = baslik_ids or []  # Tüm sınıflar modu için
        self.baslik_name = baslik_name
        self.on_save = on_save
        self.grade_inputs = {}  # {ogrenci_id: {baslik_id: input}}
        self.input_refs = []
        self.current_focus_index = 0
        self.has_changes = False
        self.sort_column = "number" # number, class, name
        self.sort_descending = False
        self._build_content()
    
    def _build_content(self):
        # Tüm sınıflar modu mu?
        is_all_mode = self.sinif_id == "all" and self.baslik_ids
        
        if is_all_mode:
            # Tüm sınıflardaki öğrencileri al
            ogrenciler = self.db.get_all_ogrenciler(None)  # Tüm öğrenciler
            baslik_text = self.baslik_name or "Tüm Sınıflar"
            
            # Öğrenci-başlık id eşleştirmesi
            ogrenci_baslik_map = {}
            for baslik_id in self.baslik_ids:
                basliklar = self.db.get_not_basliklari()
                baslik = next((b for b in basliklar if b['id'] == baslik_id), None)
                if baslik and baslik.get('sinif_id'):
                    # Bu başlık hangi sınıfa ait
                    sinif_ogrenciler = self.db.get_all_ogrenciler(baslik['sinif_id'])
                    for og in sinif_ogrenciler:
                        ogrenci_baslik_map[og['id']] = baslik_id
            
            # Mevcut notları al - her baslik_id için
            mevcut_notlar = {}
            for ogrenci in ogrenciler:
                baslik_id = ogrenci_baslik_map.get(ogrenci['id'])
                if baslik_id:
                    notlar = self.db.get_notlar(ogrenci_id=ogrenci['id'], baslik_id=baslik_id)
                    if notlar:
                        mevcut_notlar[ogrenci['id']] = {
                            'puan': notlar[0]['puan'],
                            'baslik_id': baslik_id
                        }
                    else:
                        mevcut_notlar[ogrenci['id']] = {
                            'puan': None,
                            'baslik_id': baslik_id
                        }
        else:
            # Tek sınıf modu
            ogrenciler = self.db.get_all_ogrenciler(self.sinif_id)
            
            # Not başlığı bilgisi
            basliklar = self.db.get_not_basliklari()
            baslik = next((b for b in basliklar if b['id'] == self.baslik_id), None)
            baslik_text = baslik['baslik'] if baslik else 'Bilinmeyen Başlık'
            
            # Mevcut notları al
            mevcut_notlar = {}
            for ogrenci in ogrenciler:
                notlar = self.db.get_notlar(ogrenci_id=ogrenci['id'], baslik_id=self.baslik_id)
                if notlar:
                    mevcut_notlar[ogrenci['id']] = {
                        'puan': notlar[0]['puan'],
                        'baslik_id': self.baslik_id
                    }
                else:
                    mevcut_notlar[ogrenci['id']] = {
                        'puan': None,
                        'baslik_id': self.baslik_id
                    }
            
            ogrenci_baslik_map = {og['id']: self.baslik_id for og in ogrenciler}
        
        # Sıralama
        def get_sort_key(o):
            if self.sort_column == "number":
                try:
                    return int(o.get('okul_no') or 0)
                except ValueError:
                    return 0
            elif self.sort_column == "name":
                return o.get('ad', '').lower()
            elif self.sort_column == "class":
                return o.get('sinif_adi', '').lower()
            return 0
            
        ogrenciler.sort(key=get_sort_key, reverse=self.sort_descending)
        
        # Öğrenci satırları
        rows = []
        self.input_refs = []
        
        # Başlık satırı - Tüm sınıflar modunda Sınıf sütunu ekle
        # Başlık satırı - Tüm sınıflar modunda Sınıf sütunu ekle
        header_cols = [
            ft.Container(ft.Text("#", weight=ft.FontWeight.BOLD), width=40),
            ft.Container(self._create_header_button("Okul No", "number"), width=80),
        ]
        if is_all_mode:
            header_cols.append(ft.Container(self._create_header_button("Sınıf", "class"), width=80))
        header_cols.extend([
            ft.Container(self._create_header_button("Ad Soyad", "name"), expand=True),
            ft.Container(ft.Text("Not", weight=ft.FontWeight.BOLD), width=120),
            ft.Container(ft.Text("Durum", weight=ft.FontWeight.BOLD), width=100),
        ])
        
        header_row = ft.Container(
            content=ft.Row(header_cols),
            bgcolor=ft.colors.SURFACE_VARIANT,
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            border_radius=ft.border_radius.only(top_left=5, top_right=5),
        )
        rows.append(header_row)
        
        for i, ogrenci in enumerate(ogrenciler):
            not_bilgi = mevcut_notlar.get(ogrenci['id'], {'puan': None, 'baslik_id': None})
            mevcut_not = not_bilgi['puan']
            baslik_id_for_ogrenci = not_bilgi.get('baslik_id') or ogrenci_baslik_map.get(ogrenci['id'], self.baslik_id)
            
            # Not input
            grade_input = ft.TextField(
                value=str(int(mevcut_not)) if mevcut_not is not None else "",
                width=100,
                content_padding=ft.padding.symmetric(horizontal=10, vertical=15),
                text_align=ft.TextAlign.CENTER,
                keyboard_type=ft.KeyboardType.NUMBER,
                on_change=lambda e, oid=ogrenci['id']: self._on_grade_change(e, oid),
                on_submit=lambda e, idx=i: self._move_to_next(idx),
                hint_text="Not",
                border_color=ft.colors.BLUE_400,
                focused_border_color=ft.colors.BLUE_700,
                border_width=2,
            )
            
            self.input_refs.append(grade_input)
            self.grade_inputs[ogrenci['id']] = {
                'input': grade_input,
                'baslik_id': baslik_id_for_ogrenci
            }
            
            # Satır sütunları
            row_cols = [
                ft.Container(
                    ft.Text(str(i + 1), text_align=ft.TextAlign.CENTER),
                    width=40,
                ),
                ft.Container(
                    ft.Text(ogrenci['okul_no'] or '-'),
                    width=80,
                ),
            ]
            if is_all_mode:
                row_cols.append(ft.Container(
                    ft.Text(ogrenci.get('sinif_adi', '-'), size=11),
                    width=80,
                ))
            row_cols.extend([
                ft.Container(
                    ft.Text(f"{ogrenci['ad']} {ogrenci['soyad']}"),
                    expand=True,
                ),
                ft.Container(
                    grade_input,
                    width=120,
                ),
                ft.Container(
                    ft.Container(
                        content=ft.Text(
                            self._get_status_text(mevcut_not),
                            size=12,
                            color=ft.colors.WHITE,
                        ),
                        bgcolor=self._get_status_color(mevcut_not),
                        border_radius=5,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    ),
                    width=100,
                ),
            ])
            
            # Satır
            row = ft.Container(
                content=ft.Row(row_cols, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.symmetric(horizontal=10, vertical=8),
                bgcolor=ft.colors.SURFACE_VARIANT if i % 2 == 0 else None,
            )
            rows.append(row)
        
        # Kısayol bilgisi
        shortcut_info = ft.Container(
            content=ft.Row([
                ft.Icon(ft.icons.KEYBOARD, size=16, color=ft.colors.GREY_600),
                ft.Text(
                    "Enter: Sonraki satıra geç | Ctrl+S: Kaydet",
                    size=12, color=ft.colors.GREY_600
                ),
            ], spacing=5),
            padding=5,
        )
        
        self.content = ft.Column([
            # Başlık
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.EDIT_NOTE, color=ft.colors.PRIMARY),
                    ft.Text(baslik_text, size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "Kaydet",
                        icon=ft.icons.SAVE,
                        on_click=self._save_grades,
                        bgcolor=ft.colors.PRIMARY,
                        color=ft.colors.WHITE,
                    ),
                ]),
                padding=10,
                bgcolor=ft.colors.SURFACE_VARIANT,
                border_radius=ft.border_radius.only(top_left=10, top_right=10),
            ),
            
            # Tablo
            ft.Container(
                content=ft.Column(
                    rows,
                    spacing=0,
                    scroll=ft.ScrollMode.AUTO,
                ),
                expand=True,
                border=ft.border.all(1, ft.colors.OUTLINE_VARIANT),
                border_radius=ft.border_radius.only(bottom_left=5, bottom_right=5),
            ),
            
            # Kısayol bilgisi ve toplam
            ft.Row([
                shortcut_info,
                ft.Container(expand=True),
                ft.Text(f"Toplam: {len(ogrenciler)} öğrenci", 
                       weight=ft.FontWeight.BOLD, color=ft.colors.GREY_700),
            ]),
        ], spacing=0, expand=True)
        self.expand = True
    
    def _on_grade_change(self, e, ogrenci_id):
        """Not değiştiğinde çağrılır."""
        self.has_changes = True
        
        # Renk güncelle
        value = validate_grade(e.control.value)
        if e.control.value and value is None:
            e.control.border_color = ft.colors.RED
        else:
            e.control.border_color = ft.colors.BLUE_400
        e.control.update()
    
    def _move_to_next(self, current_index):
        """Sonraki inputa geçer."""
        next_index = current_index + 1
        if next_index < len(self.input_refs):
            self.input_refs[next_index].focus()
            self.current_focus_index = next_index
        else:
            # Son satırdaysa kaydet
            self._save_grades(None)
    
    def _get_status_text(self, grade):
        """Not durumu metnini döndürür."""
        if grade is None:
            return "Girilmedi"
        if grade >= 85:
            return "Pekiyi"
        elif grade >= 70:
            return "İyi"
        elif grade >= 55:
            return "Orta"
        elif grade >= 50:
            return "Geçer"
        else:
            return "Başarısız"
    
    def _get_status_color(self, grade):
        """Not durumu için renk döndürür."""
        if grade is None:
            return ft.colors.GREY_400
        if grade >= 85:
            return ft.colors.GREEN
        elif grade >= 70:
            return ft.colors.LIGHT_GREEN_700
        elif grade >= 55:
            return ft.colors.ORANGE
        elif grade >= 50:
            return ft.colors.DEEP_ORANGE
        else:
            return ft.colors.RED
    
    def _save_grades(self, e):
        """Notları kaydeder."""
        errors = []
        saved_count = 0
        
        for ogrenci_id, data in self.grade_inputs.items():
            input_field = data['input']
            baslik_id = data['baslik_id']
            
            if not baslik_id:
                continue
                
            value = input_field.value.strip()
            if value:
                grade = validate_grade(value)
                if grade is None:
                    errors.append(f"Geçersiz not değeri: {value}")
                else:
                    self.db.add_or_update_not(ogrenci_id, baslik_id, grade)
                    saved_count += 1
        
        if errors:
            if hasattr(self, 'page') and self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Hatalar: {', '.join(errors)}"),
                    bgcolor=ft.colors.RED_400
                )
                self.page.snack_bar.open = True
                self.page.update()
            return
        
        if saved_count > 0:
            self.has_changes = False
            
            if hasattr(self, 'page') and self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"✓ {saved_count} not kaydedildi!"),
                    bgcolor=ft.colors.GREEN_400
                )
                self.page.snack_bar.open = True
                self.page.update()
            
            if self.on_save:
                self.on_save()
    
    def focus_first(self):
        """İlk inputa focus ver."""
        if self.input_refs:
            self.input_refs[0].focus()
            self.current_focus_index = 0

    def _create_header_button(self, text, column):
        """Sıralama özellikli başlık butonu oluşturur."""
        icon = None
        if self.sort_column == column:
            icon = ft.icons.ARROW_DOWNWARD if self.sort_descending else ft.icons.ARROW_UPWARD
        
        content = ft.Row([
            ft.Text(text, weight=ft.FontWeight.BOLD, no_wrap=True),
            ft.Icon(icon, size=16) if icon else ft.Container()
        ], spacing=5, alignment=ft.MainAxisAlignment.START)
        
        return ft.Container(
            content=content,
            on_click=lambda e: self._sort_table(column),
            ink=True,
            padding=ft.padding.symmetric(horizontal=5, vertical=5),
            border_radius=4,
        )

    def _sort_table(self, column):
        """Tabloyu sütuna göre sıralar."""
        if self.sort_column == column:
            self.sort_descending = not self.sort_descending
        else:
            self.sort_column = column
            self.sort_descending = False
            
        self.controls = [self.build()]
        self.update()
