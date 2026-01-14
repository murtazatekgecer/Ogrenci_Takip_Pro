"""
Not ve kategori yönetimi görünümü.
"""
import flet as ft
from components.grade_table import GradeTable


class GradesView(ft.Container):
    """Not girişi ve kategori yönetimi."""
    
    def __init__(self, db_manager, on_update=None):
        super().__init__()
        self.db = db_manager
        self.on_update = on_update
        self.selected_sinif = None
        self.selected_kategori = None
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
        
        # Kategoriler listesi
        self.kategori_list = ft.Column([], spacing=5, scroll=ft.ScrollMode.AUTO)
        
        # Not başlıkları listesi
        self.baslik_list = ft.Column([], spacing=5, scroll=ft.ScrollMode.AUTO)
        
        # Not girişi alanı
        self.grade_entry_container = ft.Container(
            content=ft.Column([
                ft.Icon(ft.icons.ASSIGNMENT_OUTLINED, size=60, color=ft.colors.GREY_400),
                ft.Text("Not başlığı seçin", size=16, color=ft.colors.GREY_500),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            expand=True,
        )
        
        self.content = ft.Column([
            # Üst araç çubuğu
            ft.Row([
                self.sinif_dropdown,
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Kategori Ekle",
                    icon=ft.icons.CATEGORY,
                    on_click=self._show_add_kategori_dialog,
                ),
            ]),
            
            ft.Divider(),
            
            # Ana içerik - 3 sütun
            ft.Row([
                # Sol: Kategoriler
                ft.Container(
                    content=ft.Column([
                        ft.Text("Kategoriler", weight=ft.FontWeight.BOLD, size=14),
                        ft.Divider(height=1),
                        self.kategori_list,
                    ]),
                    width=200,
                    bgcolor=ft.colors.SURFACE_VARIANT,
                    border_radius=10,
                    padding=10,
                ),
                
                # Orta: Not başlıkları
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("Not Başlıkları", weight=ft.FontWeight.BOLD, size=14),
                            ft.Container(expand=True),
                            ft.IconButton(
                                icon=ft.icons.ADD,
                                tooltip="Başlık Ekle",
                                on_click=self._show_add_baslik_dialog,
                            ),
                        ]),
                        ft.Divider(height=1),
                        self.baslik_list,
                    ]),
                    width=250,
                    bgcolor=ft.colors.SURFACE_VARIANT,
                    border_radius=10,
                    padding=10,
                ),
                
                # Sağ: Not girişi
                ft.Container(
                    content=self.grade_entry_container,
                    expand=True,
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=10,
                    padding=10,
                ),
            ], expand=True, spacing=15),
        ], expand=True)
        self.expand = True
    
    def refresh(self):
        """Görünümü yeniler."""
        self._update_sinif_dropdown()
        self._load_kategoriler()
    
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
            self._load_basliklar()
    
    def _load_kategoriler(self):
        """Kategorileri yükler."""
        kategoriler = self.db.get_all_kategoriler()
        
        self.kategori_list.controls = []
        for kategori in kategoriler:
            is_selected = self.selected_kategori == kategori['id']
            
            item = ft.Container(
                content=ft.Row([
                    ft.Icon(
                        ft.icons.FOLDER if not is_selected else ft.icons.FOLDER_OPEN,
                        color=ft.colors.PRIMARY if is_selected else ft.colors.GREY_600,
                        size=20,
                    ),
                    ft.Text(
                        kategori['ad'],
                        weight=ft.FontWeight.BOLD if is_selected else None,
                        expand=True,
                    ),
                    ft.PopupMenuButton(
                        items=[
                            ft.PopupMenuItem(
                                text="Düzenle",
                                icon=ft.icons.EDIT,
                                on_click=lambda e, k=kategori: self._show_edit_kategori_dialog(k),
                            ),
                            ft.PopupMenuItem(
                                text="Sil",
                                icon=ft.icons.DELETE,
                                on_click=lambda e, k=kategori: self._confirm_delete_kategori(k),
                            ),
                        ],
                    ),
                ], spacing=5),
                bgcolor=ft.colors.PRIMARY_CONTAINER if is_selected else None,
                border_radius=8,
                padding=ft.padding.symmetric(horizontal=10, vertical=8),
                on_click=lambda e, kid=kategori['id']: self._select_kategori(kid),
                ink=True,
            )
            self.kategori_list.controls.append(item)
        
        self.update()
    
    def _select_kategori(self, kategori_id):
        """Kategori seçer."""
        self.selected_kategori = kategori_id
        self._load_kategoriler()
        self._load_basliklar()
    
    def _load_basliklar(self):
        """Not başlıklarını yükler."""
        if not self.selected_sinif or not self.selected_kategori:
            self.baslik_list.controls = [
                ft.Text("Kategori seçin", color=ft.colors.GREY_500, italic=True)
            ]
            self.update()
            return
        
        # Tüm sınıflar seçiliyse farklı sorgu yap
        if self.selected_sinif == "all":
            basliklar = self.db.get_not_basliklari(
                kategori_id=self.selected_kategori,
                sinif_id=None  # Tüm sınıflar - sadece kategori bazlı filtrele
            )
            # Aynı isimdeki başlıkları birleştir (unique başlık adları)
            unique_basliklar = {}
            for baslik in basliklar:
                baslik_adi = baslik['baslik']
                if baslik_adi not in unique_basliklar:
                    unique_basliklar[baslik_adi] = {
                        'baslik': baslik_adi,
                        'kategori_id': baslik['kategori_id'],
                        'ids': [baslik['id']],  # Tüm sınıflardaki bu başlığın id'leri
                        'sinif_ids': [baslik['sinif_id']] if baslik.get('sinif_id') else []
                    }
                else:
                    unique_basliklar[baslik_adi]['ids'].append(baslik['id'])
                    if baslik.get('sinif_id'):
                        unique_basliklar[baslik_adi]['sinif_ids'].append(baslik['sinif_id'])
            basliklar = list(unique_basliklar.values())
        else:
            basliklar = self.db.get_not_basliklari(
                kategori_id=self.selected_kategori,
                sinif_id=self.selected_sinif
            )
        
        self.baslik_list.controls = []
        
        if not basliklar:
            self.baslik_list.controls.append(
                ft.Text("Henüz başlık yok", color=ft.colors.GREY_500, italic=True)
            )
        else:
            for baslik in basliklar:
                # Tüm sınıflar modunda sınıf sayısını göster
                label_suffix = ""
                if self.selected_sinif == "all" and 'ids' in baslik:
                    label_suffix = f" ({len(baslik['ids'])} sınıf)"
                
                item = ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.ASSIGNMENT, size=18, color=ft.colors.PRIMARY),
                        ft.Container(
                            content=ft.Text(baslik['baslik'] + label_suffix, expand=True, size=13),
                            expand=True,
                            on_click=lambda e, b=baslik: self._open_grade_entry(b),
                            ink=True,
                        ),
                        ft.IconButton(
                            icon=ft.icons.EDIT,
                            tooltip="Başlığı Düzenle",
                            on_click=lambda e, b=baslik: self._show_edit_baslik_dialog(b),
                            icon_size=16,
                            icon_color=ft.colors.GREY_600,
                        ),
                        ft.IconButton(
                            icon=ft.icons.DELETE,
                            tooltip="Sil",
                            on_click=lambda e, b=baslik: self._confirm_delete_baslik(b),
                            icon_size=16,
                            icon_color=ft.colors.RED_400,
                        ),
                    ], spacing=0),
                    bgcolor=ft.colors.SURFACE,
                    border_radius=5,
                    padding=ft.padding.symmetric(horizontal=8, vertical=5),
                    border=ft.border.all(1, ft.colors.GREY_300),
                    on_click=lambda e, b=baslik: self._open_grade_entry(b),
                    ink=True,
                )
                self.baslik_list.controls.append(item)
        
        self.update()
    
    def _open_grade_entry(self, baslik):
        """Not girişi ekranını açar."""
        # Tüm sınıflar modunda mı kontrol et
        if self.selected_sinif == "all" and 'ids' in baslik:
            # Birden fazla sınıf - özel mod
            grade_table = GradeTable(
                self.db,
                sinif_id="all",  # Tüm sınıflar
                baslik_id=None,  # Tek baslik yerine
                baslik_ids=baslik['ids'],  # Tüm sınıflardaki baslik id'leri
                baslik_name=baslik['baslik'],
                on_save=self._on_grades_saved
            )
        else:
            # Tek sınıf modu
            grade_table = GradeTable(
                self.db,
                sinif_id=self.selected_sinif,
                baslik_id=baslik['id'],
                on_save=self._on_grades_saved
            )
        
        # Alignment'ı sıfırla ve içeriği değiştir
        self.grade_entry_container.alignment = None
        self.grade_entry_container.content = ft.Column([
            ft.Row([
                ft.Text("Not Girişi", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.icons.CLOSE,
                    on_click=self._close_grade_entry,
                ),
            ]),
            ft.Divider(),
            ft.Container(
                content=grade_table,
                expand=True,
            ),
        ], expand=True, spacing=5)
        
        self.update()
    
    def _close_grade_entry(self, e=None):
        """Not girişi ekranını kapatır."""
        self.grade_entry_container.content = ft.Column([
            ft.Icon(ft.icons.ASSIGNMENT_OUTLINED, size=60, color=ft.colors.GREY_400),
            ft.Text("Not başlığı seçin", size=16, color=ft.colors.GREY_500),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        self.update()
    
    def _on_grades_saved(self):
        """Notlar kaydedildiğinde."""
        if self.on_update:
            self.on_update()
    
    def _show_add_kategori_dialog(self, e):
        """Kategori ekleme dialogu."""
        ad_field = ft.TextField(label="Kategori Adı", autofocus=True)
        
        def save(e):
            if ad_field.value:
                self.db.add_kategori(ad_field.value)
                dialog.open = False
                self._load_kategoriler()
                self.page.update()
                if self.on_update:
                    self.on_update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Yeni Kategori"),
            content=ad_field,
            actions=[
                ft.TextButton("İptal", on_click=lambda e: self._close_dialog(dialog)),
                ft.ElevatedButton("Kaydet", on_click=save),
            ],
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _show_edit_kategori_dialog(self, kategori):
        """Kategori düzenleme dialogu."""
        ad_field = ft.TextField(label="Kategori Adı", value=kategori['ad'])
        
        def save(e):
            if ad_field.value:
                self.db.update_kategori(kategori['id'], ad_field.value)
                dialog.open = False
                self._load_kategoriler()
                self.page.update()
                if self.on_update:
                    self.on_update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Kategori Düzenle"),
            content=ad_field,
            actions=[
                ft.TextButton("İptal", on_click=lambda e: self._close_dialog(dialog)),
                ft.ElevatedButton("Kaydet", on_click=save),
            ],
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _confirm_delete_kategori(self, kategori):
        """Kategori silme onayı."""
        def delete(e):
            try:
                self.db.delete_kategori(kategori['id'])
                dialog.open = False
                self.selected_kategori = None
                self._load_kategoriler()
                self.page.update()
                if self.on_update:
                    self.on_update()
            except ValueError as err:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(str(err)),
                    bgcolor=ft.colors.RED
                )
                self.page.snack_bar.open = True
                dialog.open = False
                self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Kategori Sil"),
            content=ft.Text(f"'{kategori['ad']}' kategorisini silmek istediğinize emin misiniz?"),
            actions=[
                ft.TextButton("İptal", on_click=lambda e: self._close_dialog(dialog)),
                ft.ElevatedButton("Sil", on_click=delete, bgcolor=ft.colors.RED, color=ft.colors.WHITE),
            ],
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _show_add_baslik_dialog(self, e):
        """Not başlığı ekleme dialogu."""
        if not self.selected_sinif or not self.selected_kategori:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Önce sınıf ve kategori seçin!"),
                bgcolor=ft.colors.ORANGE
            )
            self.page.snack_bar.open = True
            self.page.update()
            return
        
        baslik_field = ft.TextField(label="Başlık (Örn: Matematik 1. Quiz)", autofocus=True)
        
        # Tüm sınıflar seçili mi bilgi mesajı
        info_text = ""
        if self.selected_sinif == "all":
            info_text = "📚 Bu başlık TÜM SINIFLARA eklenecek!"
        
        def save(e):
            if baslik_field.value:
                if self.selected_sinif == "all":
                    # Tüm sınıflara ekle
                    siniflar = self.db.get_all_siniflar()
                    count = 0
                    for sinif in siniflar:
                        self.db.add_not_basligi(
                            baslik_field.value,
                            self.selected_kategori,
                            sinif['id']
                        )
                        count += 1
                    dialog.open = False
                    self._load_basliklar()
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"✓ Başlık {count} sınıfa eklendi!"),
                        bgcolor=ft.colors.GREEN_400
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
                else:
                    # Tek sınıfa ekle
                    self.db.add_not_basligi(
                        baslik_field.value,
                        self.selected_kategori,
                        self.selected_sinif
                    )
                    dialog.open = False
                    self._load_basliklar()
                    self.page.update()
                
                if self.on_update:
                    self.on_update()
        
        # Dialog içeriği
        dialog_content = ft.Column([
            baslik_field,
            ft.Container(
                content=ft.Text(info_text, color=ft.colors.PRIMARY, weight=ft.FontWeight.BOLD),
                visible=(self.selected_sinif == "all"),
                padding=ft.padding.only(top=10),
            ),
        ], spacing=5, tight=True)
        
        dialog = ft.AlertDialog(
            title=ft.Text("Yeni Not Başlığı"),
            content=dialog_content,
            actions=[
                ft.TextButton("İptal", on_click=lambda e: self._close_dialog(dialog)),
                ft.ElevatedButton("Kaydet", on_click=save),
            ],
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _show_edit_baslik_dialog(self, baslik):
        """Not başlığı düzenleme dialogu."""
        baslik_field = ft.TextField(label="Başlık", value=baslik['baslik'], autofocus=True)
        
        def save(e):
            if baslik_field.value:
                self.db.update_not_basligi(baslik['id'], baslik_field.value)
                dialog.open = False
                self._load_basliklar()
                self.page.update()
                if self.on_update:
                    self.on_update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Başlık Düzenle"),
            content=baslik_field,
            actions=[
                ft.TextButton("İptal", on_click=lambda e: self._close_dialog(dialog)),
                ft.ElevatedButton("Kaydet", on_click=save),
            ],
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _confirm_delete_baslik(self, baslik):
        """Not başlığı silme onayı."""
        def delete(e):
            self.db.delete_not_basligi(baslik['id'])
            dialog.open = False
            self._load_basliklar()
            self._close_grade_entry()
            self.page.update()
            if self.on_update:
                self.on_update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Başlık Sil"),
            content=ft.Text(f"'{baslik['baslik']}' başlığını ve tüm notlarını silmek istediğinize emin misiniz?"),
            actions=[
                ft.TextButton("İptal", on_click=lambda e: self._close_dialog(dialog)),
                ft.ElevatedButton("Sil", on_click=delete, bgcolor=ft.colors.RED, color=ft.colors.WHITE),
            ],
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _close_dialog(self, dialog):
        dialog.open = False
        self.page.update()
