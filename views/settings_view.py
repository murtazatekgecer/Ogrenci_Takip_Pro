"""
Ayarlar görünümü.
"""
import flet as ft
from utils.export import ExportManager
from utils.backup import BackupManager


class SettingsView(ft.Container):
    """Ayarlar ve veri yönetimi."""
    
    def __init__(self, db_manager, on_theme_change=None, on_data_change=None):
        super().__init__()
        self.db = db_manager
        self.on_theme_change = on_theme_change
        self.on_data_change = on_data_change
        self.export_manager = ExportManager(db_manager)
        self.backup_manager = BackupManager()
        self.dark_mode = False
        self._build_content()
    
    def _build_content(self):
        # FilePicker'lar
        self.save_file_picker = ft.FilePicker(on_result=self._on_save_file)
        self.open_file_picker = ft.FilePicker(on_result=self._on_open_file)
        self.folder_picker = ft.FilePicker(on_result=self._on_folder_select)
        
        # Tema switch
        self.theme_switch = ft.Switch(
            label="Karanlık Mod",
            value=self.dark_mode,
            on_change=self._on_theme_toggle,
        )
        
        # Sınıf seçici (export için)
        siniflar = self.db.get_all_siniflar()
        sinif_options = [ft.dropdown.Option(key="all", text="📚 Tüm Sınıflar")]
        sinif_options.extend([ft.dropdown.Option(key=str(s['id']), text=s['ad']) for s in siniflar])
        
        self.sinif_dropdown = ft.Dropdown(
            label="Sınıf",
            width=200,
            options=sinif_options,
        )
        
        self.content = ft.Column([            
            # Dışa aktarma
            self._create_section(
                "Dışa Aktarma",
                ft.icons.UPLOAD_FILE,
                [
                    ft.Row([
                        self.sinif_dropdown,
                    ]),
                    ft.Container(height=10),
                    ft.Row([
                        ft.ElevatedButton(
                            "Excel - Öğrenci Listesi",
                            icon=ft.icons.TABLE_CHART,
                            on_click=lambda e: self._export_excel_list(),
                        ),
                        ft.ElevatedButton(
                            "Excel - Not Çizelgesi",
                            icon=ft.icons.GRID_ON,
                            on_click=lambda e: self._export_excel_grades(),
                        ),
                    ], wrap=True),
                    ft.Row([
                        ft.ElevatedButton(
                            "PDF - Sınıf Raporu",
                            icon=ft.icons.PICTURE_AS_PDF,
                            on_click=lambda e: self._export_pdf_report(),
                        ),
                    ], wrap=True),
                ]
            ),
            
            ft.Divider(height=30),
            
            # Yedekleme
            self._create_section(
                "Yedekleme ve Geri Yükleme",
                ft.icons.BACKUP,
                [
                    ft.Row([
                        ft.ElevatedButton(
                            "Yedek Al (JSON)",
                            icon=ft.icons.SAVE,
                            on_click=lambda e: self._create_backup_json(),
                            bgcolor=ft.colors.GREEN,
                            color=ft.colors.WHITE,
                        ),
                        ft.ElevatedButton(
                            "Yedek Al (CSV)",
                            icon=ft.icons.SAVE_ALT,
                            on_click=lambda e: self._create_backup_csv(),
                        ),
                    ], wrap=True),
                    ft.Container(height=10),
                    ft.Row([
                        ft.ElevatedButton(
                            "Yedeği Geri Yükle",
                            icon=ft.icons.RESTORE,
                            on_click=lambda e: self._restore_backup(),
                            bgcolor=ft.colors.ORANGE,
                            color=ft.colors.WHITE,
                        ),
                    ]),
                    ft.Container(height=10),
                    ft.Text(
                        "⚠️ Geri yükleme mevcut tüm verilerin üzerine yazacaktır!",
                        color=ft.colors.ORANGE_700,
                        size=12,
                    ),
                ]
            ),
            
            ft.Divider(height=30),
            
            # Sınıf devri
            self._create_section(
                "Sınıf Devri",
                ft.icons.CONTENT_COPY,
                [
                    ft.Text(
                        "Mevcut bir sınıfı yeni döneme/seneye kopyalar. Öğrenci listesi aktarılır, notlar sıfırlanır.",
                        color=ft.colors.GREY_600,
                        size=13,
                    ),
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "Sınıf Devret",
                        icon=ft.icons.ARROW_FORWARD,
                        on_click=self._show_class_transfer_dialog,
                    ),
                ]
            ),
            
            # Hidden file pickers
            self.save_file_picker,
            self.open_file_picker,
            self.folder_picker,
        ], scroll=ft.ScrollMode.AUTO)
    
    def _create_section(self, title, icon, controls):
        """Ayar bölümü oluşturur."""
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icon, color=ft.colors.PRIMARY),
                    ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
                ], spacing=10),
                ft.Container(height=10),
                *controls,
            ]),
            bgcolor=ft.colors.SURFACE_VARIANT,
            border_radius=10,
            padding=20,
        )
    
    def _on_theme_toggle(self, e):
        """Tema değiştiğinde."""
        self.dark_mode = e.control.value
        if self.on_theme_change:
            self.on_theme_change(self.dark_mode)
    
    def _get_selected_sinif(self):
        """Seçili sınıf ID'sini döndürür. Tümü için 'all' döner."""
        if self.sinif_dropdown.value:
            if self.sinif_dropdown.value == "all":
                return "all"
            return int(self.sinif_dropdown.value)
        return None
    
    def _export_excel_list(self):
        """Öğrenci listesini Excel'e aktarır."""
        sinif_id = self._get_selected_sinif()
        if not sinif_id:
            self._show_error("Önce bir sınıf seçin!")
            return
        
        self._current_export = 'excel_list'
        self.save_file_picker.save_file(
            dialog_title="Öğrenci Listesi Kaydet",
            file_name="ogrenci_listesi.xlsx",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["xlsx"],
        )
    
    def _export_excel_grades(self):
        """Not çizelgesini Excel'e aktarır."""
        sinif_id = self._get_selected_sinif()
        if not sinif_id:
            self._show_error("Önce bir sınıf seçin!")
            return
        
        self._current_export = 'excel_grades'
        self.save_file_picker.save_file(
            dialog_title="Not Çizelgesi Kaydet",
            file_name="not_cizelgesi.xlsx",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["xlsx"],
        )
    
    def _export_pdf_report(self):
        """Sınıf raporunu PDF'e aktarır."""
        sinif_id = self._get_selected_sinif()
        if not sinif_id:
            self._show_error("Önce bir sınıf seçin!")
            return
        
        self._current_export = 'pdf_report'
        self.save_file_picker.save_file(
            dialog_title="Sınıf Raporu Kaydet",
            file_name="sinif_raporu.pdf",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["pdf"],
        )
    
    def _on_save_file(self, e):
        """Dosya kaydetme sonucu."""
        if not e.path:
            return
        
        path = e.path
        sinif_id = self._get_selected_sinif()
        # Export manager None kabul eder tümü için
        export_sinif_id = None if sinif_id == "all" else sinif_id
        
        try:
            if self._current_export == 'excel_list':
                self.export_manager.export_sinif_listesi_excel(export_sinif_id, path)
            elif self._current_export == 'excel_grades':
                self.export_manager.export_not_cizelgesi_excel(export_sinif_id, path)
            elif self._current_export == 'pdf_report':
                self.export_manager.export_sinif_raporu_pdf(export_sinif_id, path)
            elif self._current_export == 'backup_json':
                self.backup_manager.create_backup_json(path)
            
            def open_file(e):
                import os
                import sys
                try:
                    # Windows-only: os.startfile
                    if sys.platform == 'win32':
                        os.startfile(path)
                    else:
                        # Android/Linux/Mac - dosya açma desteklenmiyor
                        pass
                except Exception as err:
                    print(f"Dosya açma hatası: {err}")

            # Sadece Windows'ta "Dosyayı Aç" butonu göster
            import sys
            if sys.platform == 'win32':
                self._show_success(
                    f"Dosya kaydedildi: {path}",
                    action_text="DOSYAYI AÇ",
                    on_action=open_file
                )
            else:
                self._show_success(f"Dosya kaydedildi: {path}")
        except Exception as err:
            self._show_error(f"Hata: {str(err)}")
    
    def _create_backup_json(self):
        """JSON yedek oluşturur."""
        self._current_export = 'backup_json'
        self.save_file_picker.save_file(
            dialog_title="Yedek Kaydet",
            file_name="ogrenci_takip_yedek.json",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["json"],
        )
    
    def _create_backup_csv(self):
        """CSV yedek oluşturur."""
        self._current_export = 'backup_csv'
        self.folder_picker.get_directory_path(
            dialog_title="Yedek Klasörü Seç",
        )
    
    def _on_folder_select(self, e):
        """Klasör seçme sonucu."""
        if not e.path:
            return
        
        try:
            if self._current_export == 'backup_csv':
                import os
                backup_path = os.path.join(e.path, 'ogrenci_takip_backup')
                self.backup_manager.create_backup_csv(backup_path)
                self._show_success(f"Yedek oluşturuldu: {backup_path}")
        except Exception as err:
            self._show_error(f"Hata: {str(err)}")
    
    def _restore_backup(self):
        """Yedeği geri yükler."""
        self._current_export = 'restore'
        self.open_file_picker.pick_files(
            dialog_title="Yedek Dosyası Seç",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["json"],
        )
    
    def _on_open_file(self, e):
        """Dosya açma sonucu."""
        if not e.files:
            return
        
        filepath = e.files[0].path
        
        try:
            self.backup_manager.restore_backup_json(filepath)
            self._show_success("Yedek başarıyla geri yüklendi!")
            if self.on_data_change:
                self.on_data_change()
        except Exception as err:
            self._show_error(f"Geri yükleme hatası: {str(err)}")
    
    def _show_class_transfer_dialog(self, e):
        """Sınıf devri dialogu."""
        siniflar = self.db.get_all_siniflar()
        
        source_dropdown = ft.Dropdown(
            label="Kaynak Sınıf",
            width=200,
            options=[ft.dropdown.Option(str(s['id']), s['ad']) for s in siniflar],
        )
        new_name_field = ft.TextField(label="Yeni Sınıf Adı", hint_text="Örn: 10-A")
        new_donem_field = ft.TextField(label="Yeni Dönem", hint_text="Örn: 2024-2025")
        
        def transfer(e):
            if not source_dropdown.value or not new_name_field.value:
                self._show_error("Tüm alanları doldurun!")
                return
            
            try:
                self.db.copy_sinif_to_new_term(
                    int(source_dropdown.value),
                    new_name_field.value,
                    new_donem_field.value or ''
                )
                dialog.open = False
                self._show_success("Sınıf başarıyla devredildi!")
                self.page.update()
                if self.on_data_change:
                    self.on_data_change()
            except Exception as err:
                self._show_error(f"Hata: {str(err)}")
        
        dialog = ft.AlertDialog(
            title=ft.Text("Sınıf Devret"),
            content=ft.Column([
                ft.Text("Kaynak sınıftaki öğrenciler yeni sınıfa kopyalanacak, notlar sıfırlanacaktır."),
                ft.Container(height=10),
                source_dropdown,
                new_name_field,
                new_donem_field,
            ], tight=True, spacing=10),
            actions=[
                ft.TextButton("İptal", on_click=lambda e: self._close_dialog(dialog)),
                ft.ElevatedButton("Devret", on_click=transfer),
            ],
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _show_success(self, message, action_text=None, on_action=None):
        """Başarı mesajı gösterir."""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(f"✓ {message}"),
            bgcolor=ft.colors.GREEN,
            action=action_text,
            on_action=on_action,
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _show_error(self, message):
        """Hata mesajı gösterir."""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.colors.RED
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def _close_dialog(self, dialog):
        dialog.open = False
        self.page.update()
    
    def refresh(self):
        """Görünümü yeniler."""
        siniflar = self.db.get_all_siniflar()
        sinif_options = [ft.dropdown.Option(key="all", text="📚 Tüm Sınıflar")]
        sinif_options.extend([ft.dropdown.Option(key=str(s['id']), text=s['ad']) for s in siniflar])
        self.sinif_dropdown.options = sinif_options
        self.update()
