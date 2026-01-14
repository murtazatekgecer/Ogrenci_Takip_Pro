"""
Ana görünüm ve navigasyon.
"""
import flet as ft
from .student_view import StudentView
from .grades_view import GradesView
from .reports_view import ReportsView
from .settings_view import SettingsView
from .random_view import RandomView


class MainView(ft.Container):
    """Ana uygulama görünümü."""
    
    def __init__(self, page, db_manager):
        super().__init__()
        self.page = page
        self.db = db_manager
        self.current_view = "students"
        self.dark_mode = False
        
        # Alt görünümler
        self.student_view = None
        self.grades_view = None
        self.reports_view = None
        self.settings_view = None
        self.random_view = None
        self._build_content()
    
    def _build_content(self):
        self._init_views()
        
        # Tema değiştirme butonu
        self.theme_button = ft.IconButton(
            icon=ft.icons.DARK_MODE if not self.dark_mode else ft.icons.LIGHT_MODE,
            tooltip="Temayı Değiştir",
            on_click=self._toggle_theme,
        )
        
        # Undo butonu
        self.undo_button = ft.IconButton(
            icon=ft.icons.UNDO,
            tooltip="Geri Al",
            on_click=self._undo_action,
            disabled=not self.db.can_undo(),
        )
        
        # Navigasyon butonları
        self.nav_buttons = ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.SCHOOL, size=32, color=ft.colors.PRIMARY),
                    ft.Text("ÖTP", size=12, weight=ft.FontWeight.BOLD, color=ft.colors.PRIMARY),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                padding=10,
            ),
            ft.Divider(height=1),
            self._create_nav_button(0, ft.icons.PEOPLE, "Öğrenciler"),
            self._create_nav_button(1, ft.icons.SHUFFLE, "Rastgele Seç"),
            self._create_nav_button(2, ft.icons.ASSIGNMENT, "Notlar"),
            self._create_nav_button(3, ft.icons.ANALYTICS, "Raporlar"),
            self._create_nav_button(4, ft.icons.SETTINGS, "Ayarlar"),
            ft.Container(expand=True),
            self.undo_button,
            self.theme_button,
        ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        # Sol navigasyon paneli
        self.nav_panel = ft.Container(
            content=self.nav_buttons,
            width=80,
            bgcolor=ft.colors.SURFACE_VARIANT,
            padding=ft.padding.symmetric(vertical=10),
        )
        
        # İçerik alanı
        self.content_area = ft.Container(
            content=self.student_view,
            expand=True,
            padding=20,
        )
        
        # Ana layout
        main_row = ft.Row([
            self.nav_panel,
            ft.VerticalDivider(width=1),
            self.content_area,
        ], expand=True, spacing=0)
        
        self.content = main_row
        self.expand = True
    
    def _create_nav_button(self, index, icon, tooltip):
        """Navigasyon butonu oluşturur."""
        return ft.Container(
            content=ft.IconButton(
                icon=icon,
                tooltip=tooltip,
                icon_size=28,
                on_click=lambda e, idx=index: self._on_nav_click(idx),
            ),
            padding=5,
        )
    
    def _init_views(self):
        """Alt görünümleri başlatır."""
        self.student_view = StudentView(self.db, on_update=self._refresh_views)
        self.grades_view = GradesView(self.db, on_update=self._refresh_views)
        self.reports_view = ReportsView(self.db)
        self.settings_view = SettingsView(
            self.db, 
            on_theme_change=self._apply_theme,
            on_data_change=self._refresh_views
        )
        self.random_view = RandomView(self.db)
    
    def _on_nav_click(self, index):
        """Navigasyon tıklandığında çağrılır."""
        views = [
            self.student_view,
            self.random_view,
            self.grades_view,
            self.reports_view,
            self.settings_view,
        ]
        
        self.content_area.content = views[index]
        
        # Görünümü güncelle
        if hasattr(views[index], 'refresh'):
            views[index].refresh()
        
        self.update()
    
    def _toggle_theme(self, e):
        """Temayı değiştirir."""
        self.dark_mode = not self.dark_mode
        self._apply_theme(self.dark_mode)
    
    def _apply_theme(self, dark_mode):
        """Temayı uygular."""
        self.dark_mode = dark_mode
        self.page.theme_mode = ft.ThemeMode.DARK if dark_mode else ft.ThemeMode.LIGHT
        self.theme_button.icon = ft.icons.LIGHT_MODE if dark_mode else ft.icons.DARK_MODE
        self.page.update()
    
    def _undo_action(self, e):
        """Son işlemi geri alır."""
        if self.db.can_undo():
            desc = self.db.get_undo_description()
            self.db.undo()
            
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"↩ {desc}"),
                bgcolor=ft.colors.BLUE_400
            )
            self.page.snack_bar.open = True
            
            self._refresh_views()
            self.page.update()
    
    def _refresh_views(self):
        """Tüm görünümleri yeniler."""
        self.undo_button.disabled = not self.db.can_undo()
        
        # Aktif görünümü yenile
        current = self.content_area.content
        if hasattr(current, 'refresh'):
            current.refresh()
        
        self.update()
