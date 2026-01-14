"""
Öğrenci yönetimi görünümü.
"""
import flet as ft
from components.student_card import StudentCard
from components.wheel_picker import WheelPicker
from utils.helpers import filter_students_by_name


class StudentView(ft.Container):
    """Öğrenci listesi ve yönetimi."""
    
    def __init__(self, db_manager, on_update=None):
        super().__init__()
        self.db = db_manager
        self.on_update = on_update
        self.selected_sinif = None
        self.search_text = ""
        self.filter_mode = "all"  # all, below_50, above_70
        self.sort_column = "number"  # number, name, surname, class, average
        self.sort_descending = False
        self._build_content()
    
    def _build_content(self):
        # Sınıf seçici - "Tüm Sınıflar" seçeneği ile
        siniflar = self.db.get_all_siniflar()
        sinif_options = [ft.dropdown.Option(key="all", text="📚 Tüm Sınıflar")]
        sinif_options.extend([ft.dropdown.Option(key=str(s['id']), text=s['ad']) for s in siniflar])
        
        self.sinif_dropdown = ft.Dropdown(
            label="Sınıf Seçin",
            width=200,
            options=sinif_options,
            on_change=self._on_sinif_change,
        )
        
        # Arama kutusu
        self.search_field = ft.TextField(
            label="Öğrenci Ara",
            prefix_icon=ft.icons.SEARCH,
            width=250,
            on_change=self._on_search,
            hint_text="Ad, soyad veya okul no...",
        )
        
        # Filtre dropdown
        self.filter_dropdown = ft.Dropdown(
            label="Filtre",
            width=180,
            value="all",
            options=[
                ft.dropdown.Option("all", "Tüm Öğrenciler"),
                ft.dropdown.Option("below_50", "Ort. < 50"),
                ft.dropdown.Option("above_70", "Ort. > 70"),
                ft.dropdown.Option("above_85", "Ort. > 85"),
            ],
            on_change=self._on_filter_change,
        )
        
        # Liste başlığı
        # Liste başlığı
        self.list_header = ft.Container(
            content=ft.Row([
                ft.Container(ft.Text("#", weight=ft.FontWeight.BOLD), width=40),
                ft.Container(self._create_header_button("Okul No", "number", width=80), width=80),
                ft.Container(self._create_header_button("Sınıf", "class", width=80), width=80),
                ft.Container(self._create_header_button("Ad", "name"), expand=True),
                ft.Container(self._create_header_button("Soyad", "surname"), expand=True),
                ft.Container(self._create_header_button("Ortalama", "average", width=80), width=80),
                ft.Container(ft.Text("İşlemler", weight=ft.FontWeight.BOLD), width=120, alignment=ft.alignment.center_right),
            ], alignment=ft.MainAxisAlignment.START),
            bgcolor=ft.colors.SURFACE_VARIANT,
            padding=ft.padding.symmetric(horizontal=15, vertical=12),
            border_radius=ft.border_radius.only(top_left=8, top_right=8),
        )

        # Öğrenci listesi (scrollable)
        self.student_list = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO)
        
        # Tablo container
        self.table_container = ft.Container(
            content=ft.Column([
                self.list_header,
                ft.Container(
                    content=self.student_list,
                    expand=True,
                )
            ], spacing=0),
            expand=True,
            border_radius=8,
            border=ft.border.all(1, ft.colors.OUTLINE_VARIANT),
            bgcolor=ft.colors.SURFACE,
            margin=ft.margin.only(top=0),
        )
        
        # Detay kartı için container
        self.detail_container = ft.Container(visible=False, padding=ft.padding.only(left=10))
        
        # Rastgele seçici container
        self.wheel_container = ft.Container(visible=False, padding=ft.padding.only(left=10))
        
        self.content = ft.Column([
            # Üst araç çubuğu - Satır 1
            ft.Row([
                self.sinif_dropdown,
                ft.ElevatedButton(
                    "Yeni Sınıf",
                    icon=ft.icons.ADD,
                    on_click=self._show_add_sinif_dialog,
                ),
                ft.Container(width=20),
                self.search_field,
                self.filter_dropdown,
            ]),
            
            # Üst araç çubuğu - Satır 2
            ft.Row([
                ft.ElevatedButton(
                    "Öğrenci Ekle",
                    icon=ft.icons.PERSON_ADD,
                    on_click=self._show_add_student_dialog,
                    bgcolor=ft.colors.PRIMARY,
                    color=ft.colors.WHITE,
                ),
            ]),
            
            ft.Divider(height=10),
            
            # Ana içerik - genişleyen tablo
            ft.Row([
                self.table_container,
                self.detail_container,
                self.wheel_container,
            ], expand=True, vertical_alignment=ft.CrossAxisAlignment.START),
        ], expand=True)
        self.expand = True
    
    def refresh(self):
        """Listeyi yeniler."""
        self._update_sinif_dropdown()
        self._load_students()
    
    def _update_sinif_dropdown(self):
        """Sınıf dropdown'ını günceller."""
        siniflar = self.db.get_all_siniflar()
        sinif_options = [ft.dropdown.Option(key="all", text="📚 Tüm Sınıflar")]
        sinif_options.extend([ft.dropdown.Option(key=str(s['id']), text=s['ad']) for s in siniflar])
        self.sinif_dropdown.options = sinif_options
        
        if not self.selected_sinif:
            self.sinif_dropdown.value = "all"
            self.selected_sinif = "all"
    
    def _on_sinif_change(self, e):
        """Sınıf değiştiğinde."""
        if e.control.value:
            if e.control.value == "all":
                self.selected_sinif = "all"
            else:
                self.selected_sinif = int(e.control.value)
            self._load_students()
            self.update()
    
    def _load_students(self):
        """Öğrenci listesini yükler."""
        if not self.selected_sinif:
            self.student_list.controls = []
            self.update()
            return
        
        # Tüm sınıflar seçiliyse
        if self.selected_sinif == "all":
            ogrenciler = self.db.get_all_ogrenciler(None)  # Tüm öğrenciler
        else:
            ogrenciler = self.db.get_all_ogrenciler(self.selected_sinif)
        
        # Filtrele
        if self.search_text:
            ogrenciler = filter_students_by_name(ogrenciler, self.search_text)
        
        if self.filter_mode != "all":
            filtered = []
            for o in ogrenciler:
                avg = self.db.get_ogrenci_genel_ortalama(o['id'])
                if avg is None:
                    continue
                if self.filter_mode == "below_50" and avg < 50:
                    filtered.append(o)
                elif self.filter_mode == "above_70" and avg > 70:
                    filtered.append(o)
                elif self.filter_mode == "above_85" and avg > 85:
                    filtered.append(o)
            ogrenciler = filtered
        
        # Sıralama
        def get_sort_key(o):
            if self.sort_column == "number":
                try:
                    return int(o.get('okul_no') or 0)
                except ValueError:
                    return 0
            elif self.sort_column == "name":
                return o.get('ad', '').lower()
            elif self.sort_column == "surname":
                return o.get('soyad', '').lower()
            elif self.sort_column == "class":
                return o.get('sinif_adi', '').lower()
            elif self.sort_column == "average":
                avg = self.db.get_ogrenci_genel_ortalama(o['id'])
                return avg if avg is not None else -1
            return 0
            
        ogrenciler.sort(key=get_sort_key, reverse=self.sort_descending)
        
        # Tablo satırları
        self.student_list.controls = []
        for i, ogrenci in enumerate(ogrenciler, 1):
            avg = self.db.get_ogrenci_genel_ortalama(ogrenci['id'])
            
            row_content = ft.Row([
                ft.Container(ft.Text(str(i)), width=40),
                ft.Container(ft.Text(ogrenci['okul_no'] or '-'), width=80),
                ft.Container(ft.Text(ogrenci.get('sinif_adi', '-'), size=12), width=80),
                ft.Container(ft.Text(ogrenci['ad'], no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS), expand=True),
                ft.Container(ft.Text(ogrenci['soyad'], no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS), expand=True),
                ft.Container(
                    ft.Container(
                        content=ft.Text(
                            f"{avg:.1f}" if avg else "-",
                            color=ft.colors.WHITE,
                            size=12,
                            weight=ft.FontWeight.BOLD,
                        ),
                        bgcolor=self._get_avg_color(avg),
                        border_radius=4,
                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                        alignment=ft.alignment.center,
                    ),
                    width=80,
                    alignment=ft.alignment.center_left,
                ),
                ft.Container(
                    ft.Row([
                        ft.IconButton(ft.icons.VISIBILITY, tooltip="Detay", icon_size=18, 
                                     on_click=lambda e, oid=ogrenci['id']: self._show_student_detail(oid)),
                        ft.IconButton(ft.icons.EDIT, tooltip="Düzenle", icon_size=18, 
                                     on_click=lambda e, o=ogrenci: self._show_edit_student_dialog(o)),
                        ft.IconButton(ft.icons.DELETE, tooltip="Sil", icon_size=18, icon_color=ft.colors.RED_400,
                                     on_click=lambda e, o=ogrenci: self._confirm_delete_student(o)),
                    ], spacing=0, alignment=ft.MainAxisAlignment.END),
                    width=120,
                ),
            ], alignment=ft.MainAxisAlignment.START)
            
            item = ft.Container(
                content=row_content,
                padding=ft.padding.symmetric(horizontal=15, vertical=8),
                bgcolor=ft.colors.SURFACE_VARIANT if i % 2 == 0 else None,
                border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.OUTLINE_VARIANT)),
                on_click=lambda e, oid=ogrenci['id']: self._show_student_detail(oid),
                ink=True,
            )
            self.student_list.controls.append(item)
        
        self.update()
    
    def _get_avg_color(self, avg):
        """Ortalama için renk döndürür."""
        if avg is None:
            return ft.colors.GREY
        if avg >= 85:
            return ft.colors.GREEN
        elif avg >= 70:
            return ft.colors.LIGHT_GREEN
        elif avg >= 55:
            return ft.colors.ORANGE
        elif avg >= 45:
            return ft.colors.DEEP_ORANGE
        else:
            return ft.colors.RED
    
    def _on_sinif_change(self, e):
        """Sınıf değiştiğinde."""
        if e.control.value:
            self.selected_sinif = int(e.control.value)
            self._load_students()
    
    def _on_search(self, e):
        """Arama değiştiğinde."""
        self.search_text = e.control.value
        self._load_students()
    
    def _on_filter_change(self, e):
        """Filtre değiştiğinde."""
        self.filter_mode = e.control.value
        self._load_students()
    
    def _show_student_detail(self, ogrenci_id):
        """Öğrenci detay kartını gösterir."""
        self.wheel_container.visible = False
        
        card = StudentCard(
            self.db, 
            ogrenci_id,
            on_close=self._close_detail,
            on_update=self._on_student_update
        )
        
        self.detail_container.content = card
        self.detail_container.visible = True
        self.update()
    
    def _close_detail(self):
        """Detay kartını kapatır."""
        self.detail_container.visible = False
        self.update()
    
    def _on_student_update(self):
        """Öğrenci güncellendiğinde."""
        self._load_students()
        if self.on_update:
            self.on_update()
    
    def _show_wheel_picker(self, e):
        """Çarkıfelek seçiciyi gösterir."""
        if not self.selected_sinif:
            return
        
        self.detail_container.visible = False
        
        # "all" seçiliyse tüm öğrencileri getir
        sinif_id = None if self.selected_sinif == "all" else self.selected_sinif
        ogrenciler = self.db.get_all_ogrenciler(sinif_id)
        wheel = WheelPicker(ogrenciler, on_select=self._on_random_select)
        
        self.wheel_container.content = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.icons.CLOSE,
                        on_click=lambda e: self._close_wheel(),
                    ),
                ]),
                wheel,
            ]),
            bgcolor=ft.colors.SURFACE,
            border_radius=15,
            padding=10,
            width=350,
        )
        self.wheel_container.visible = True
        self.update()
    
    def _close_wheel(self):
        """Çarkıfeleği kapatır."""
        self.wheel_container.visible = False
        self.update()
    
    def _on_random_select(self, student):
        """Rastgele öğrenci seçildiğinde."""
        pass  # İsteğe bağlı: Seçilen öğrenciyi vurgulama vb.
    
    def _show_add_sinif_dialog(self, e):
        """Sınıf ekleme dialogunu gösterir."""
        ad_field = ft.TextField(label="Sınıf Adı", autofocus=True)
        donem_field = ft.TextField(label="Dönem (Opsiyonel)")
        
        def save_sinif(e):
            if ad_field.value:
                self.db.add_sinif(ad_field.value, donem_field.value or '')
                dialog.open = False
                self.refresh()
                self.page.update()
                if self.on_update:
                    self.on_update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Yeni Sınıf Ekle"),
            content=ft.Column([ad_field, donem_field], tight=True, spacing=10),
            actions=[
                ft.TextButton("İptal", on_click=lambda e: self._close_dialog(dialog)),
                ft.ElevatedButton("Kaydet", on_click=save_sinif),
            ],
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _show_add_student_dialog(self, e):
        """Öğrenci ekleme dialogunu gösterir."""
        if not self.selected_sinif:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Önce bir sınıf seçin!"),
                bgcolor=ft.colors.ORANGE
            )
            self.page.snack_bar.open = True
            self.page.update()
            return
        
        ad_field = ft.TextField(label="Ad", autofocus=True)
        soyad_field = ft.TextField(label="Soyad")
        okul_no_field = ft.TextField(label="Okul Numarası")
        
        def save_student(e):
            if ad_field.value and soyad_field.value:
                self.db.add_ogrenci(
                    ad_field.value,
                    soyad_field.value,
                    okul_no_field.value or '',
                    self.selected_sinif
                )
                dialog.open = False
                self._load_students()
                self.page.update()
                if self.on_update:
                    self.on_update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Yeni Öğrenci Ekle"),
            content=ft.Column([ad_field, soyad_field, okul_no_field], tight=True, spacing=10),
            actions=[
                ft.TextButton("İptal", on_click=lambda e: self._close_dialog(dialog)),
                ft.ElevatedButton("Kaydet", on_click=save_student),
            ],
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _show_edit_student_dialog(self, ogrenci):
        """Öğrenci düzenleme dialogunu gösterir."""
        ad_field = ft.TextField(label="Ad", value=ogrenci['ad'])
        soyad_field = ft.TextField(label="Soyad", value=ogrenci['soyad'])
        okul_no_field = ft.TextField(label="Okul Numarası", value=ogrenci['okul_no'] or '')
        
        # Sınıf dropdown
        siniflar = self.db.get_all_siniflar()
        sinif_dropdown = ft.Dropdown(
            label="Sınıf",
            value=str(ogrenci['sinif_id']) if ogrenci['sinif_id'] else None,
            options=[ft.dropdown.Option(str(s['id']), s['ad']) for s in siniflar],
        )
        
        def save_changes(e):
            if ad_field.value and soyad_field.value:
                self.db.update_ogrenci(
                    ogrenci['id'],
                    ad_field.value,
                    soyad_field.value,
                    okul_no_field.value or '',
                    int(sinif_dropdown.value) if sinif_dropdown.value else None
                )
                dialog.open = False
                self._load_students()
                self.page.update()
                if self.on_update:
                    self.on_update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Öğrenci Düzenle"),
            content=ft.Column([ad_field, soyad_field, okul_no_field, sinif_dropdown], 
                            tight=True, spacing=10),
            actions=[
                ft.TextButton("İptal", on_click=lambda e: self._close_dialog(dialog)),
                ft.ElevatedButton("Kaydet", on_click=save_changes),
            ],
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _confirm_delete_student(self, ogrenci):
        """Öğrenci silme onayı."""
        def delete(e):
            self.db.delete_ogrenci(ogrenci['id'])
            dialog.open = False
            self._load_students()
            self.page.update()
            if self.on_update:
                self.on_update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Öğrenci Sil"),
            content=ft.Text(
                f"{ogrenci['ad']} {ogrenci['soyad']} öğrencisini silmek istediğinize emin misiniz?"
            ),
            actions=[
                ft.TextButton("İptal", on_click=lambda e: self._close_dialog(dialog)),
                ft.ElevatedButton(
                    "Sil", 
                    on_click=delete,
                    bgcolor=ft.colors.RED,
                    color=ft.colors.WHITE
                ),
            ],
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _close_dialog(self, dialog):
        """Dialogu kapatır."""
        dialog.open = False
        self.page.update()

    def _create_header_button(self, text, column, width=None):
        """Sıralama özellikli başlık butonu oluşturur."""
        icon = None
        if self.sort_column == column:
            icon = ft.icons.ARROW_DOWNWARD if self.sort_descending else ft.icons.ARROW_UPWARD
        
        content = ft.Row([
            ft.Text(text, weight=ft.FontWeight.BOLD, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
            ft.Icon(icon, size=16) if icon else ft.Container()
        ], spacing=5, alignment=ft.MainAxisAlignment.START)
        
        return ft.Container(
            content=content,
            width=width,
            on_click=lambda e: self._sort_students(column),
            ink=True,
            padding=ft.padding.symmetric(horizontal=5, vertical=5),
            border_radius=4,
        )

    def _sort_students(self, column):
        """Öğrencileri belirtilen sütuna göre sıralar."""
        if self.sort_column == column:
            self.sort_descending = not self.sort_descending
        else:
            self.sort_column = column
            self.sort_descending = False
            
        # Başlıkları güncelle (ok işaretleri için)
        self.list_header.content.controls[1].content = self._create_header_button("Okul No", "number", width=80)
        self.list_header.content.controls[2].content = self._create_header_button("Sınıf", "class", width=80)
        self.list_header.content.controls[3].content = self._create_header_button("Ad", "name")
        self.list_header.content.controls[4].content = self._create_header_button("Soyad", "surname")
        self.list_header.content.controls[5].content = self._create_header_button("Ortalama", "average", width=80)
        
        self.list_header.update()
        self._load_students()
