"""
Öğrenci Takip Pro - Ana Uygulama
Öğretmenler için kapsamlı öğrenci takip ve not yönetim sistemi.
"""
import flet as ft
from database import init_db, DatabaseManager
from views.student_view import StudentView
from views.grades_view import GradesView
from views.reports_view import ReportsView
from views.settings_view import SettingsView
from views.random_view import RandomView


def main(page):
    """Ana uygulama fonksiyonu."""
    
    # Sayfa ayarları
    page.title = "Öğrenci Takip Pro"
    page.padding = 0
    page.spacing = 0
    
    # Masaüstü-only ayarları (mobilde bu özellikler desteklenmiyor)
    if page.platform not in ["android", "ios"]:
        page.window_width = 1200
        page.window_height = 800
        page.window_min_width = 900
        page.window_min_height = 600
        page.window_icon = "icon.png"
    
    # Tema ayarları
    page.theme = ft.Theme(
        color_scheme_seed=ft.colors.BLUE,
    )
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Veritabanını başlat
    init_db()
    
    # Veritabanı yöneticisi
    db = DatabaseManager()
    
    # State
    state = {"dark_mode": False, "current_nav": 0}
    
    # Görünümler - her biri visible=False ile başlar
    student_view = StudentView(db, on_update=lambda: refresh_views())
    grades_view = GradesView(db, on_update=lambda: refresh_views())
    reports_view = ReportsView(db)
    settings_view = SettingsView(
        db, 
        on_theme_change=lambda dm: toggle_theme(dm),
        on_data_change=lambda: refresh_views()
    )
    
    # Rastgele Seç görünümü
    random_view = RandomView(db)
    
    # Konteynerler - visibility ile kontrol
    view_containers = [
        ft.Container(content=student_view, visible=True, expand=True, padding=20),
        ft.Container(content=random_view, visible=False, expand=True, padding=20),
        ft.Container(content=grades_view, visible=False, expand=True, padding=20),
        ft.Container(content=reports_view, visible=False, expand=True, padding=20),
        ft.Container(content=settings_view, visible=False, expand=True, padding=20),
    ]
    
    def refresh_views():
        undo_btn.disabled = not db.can_undo()
        for i, container in enumerate(view_containers):
            if container.visible and hasattr(container.content, 'refresh'):
                container.content.refresh()
        page.update()
    
    def toggle_theme(dm=None):
        if dm is not None:
            state["dark_mode"] = dm
        else:
            state["dark_mode"] = not state["dark_mode"]
        page.theme_mode = ft.ThemeMode.DARK if state["dark_mode"] else ft.ThemeMode.LIGHT
        theme_btn.icon = ft.icons.LIGHT_MODE if state["dark_mode"] else ft.icons.DARK_MODE
        page.update()
    
    def on_nav_click(e, index):
        """Navigasyon butonuna tıklandığında."""
        state["current_nav"] = index
        
        # Tüm view'ları gizle, sadece seçileni göster
        for i, container in enumerate(view_containers):
            container.visible = (i == index)
        
        # Görünümü yenile
        if hasattr(view_containers[index].content, 'refresh'):
            view_containers[index].content.refresh()
        
        # Buton renklerini güncelle
        update_nav_colors(index)
        
        page.update()
    
    def update_nav_colors(active_index):
        """Navigasyon butonlarının renklerini günceller."""
        for i, btn in enumerate(nav_icon_buttons):
            btn.icon_color = ft.colors.PRIMARY if i == active_index else ft.colors.GREY_600
    
    def on_undo(e):
        if db.can_undo():
            desc = db.get_undo_description()
            db.undo()
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"↩ {desc}"),
                bgcolor=ft.colors.BLUE_400
            )
            page.snack_bar.open = True
            refresh_views()
    
    # Navigasyon icon butonları (ayrı liste)
    nav_icon_buttons = []
    nav_icons = [ft.icons.PEOPLE, ft.icons.SHUFFLE, ft.icons.ASSIGNMENT, ft.icons.ANALYTICS, ft.icons.SETTINGS]
    nav_labels = ["Öğrenciler", "Rastgele Seç", "Notlar", "Raporlar", "Ayarlar"]
    
    for i, (icon, label) in enumerate(zip(nav_icons, nav_labels)):
        icon_btn = ft.IconButton(
            icon=icon,
            tooltip=label,
            icon_size=28,
            icon_color=ft.colors.PRIMARY if i == 0 else ft.colors.GREY_600,
            on_click=lambda e, idx=i: on_nav_click(e, idx),
        )
        nav_icon_buttons.append(icon_btn)
    
    # Navigasyon buton konteynerleri
    nav_buttons = [ft.Container(content=btn, padding=5) for btn in nav_icon_buttons]
    
    # Tema butonu
    theme_btn = ft.IconButton(
        icon=ft.icons.DARK_MODE,
        tooltip="Temayı Değiştir",
        on_click=lambda e: toggle_theme(),
    )
    
    # Undo butonu
    undo_btn = ft.IconButton(
        icon=ft.icons.UNDO,
        tooltip="Geri Al (Ctrl+Z)",
        on_click=on_undo,
        disabled=not db.can_undo(),
    )
    
    # Sol navigasyon paneli
    nav_column = ft.Column([
        ft.Container(
            content=ft.Column([
                ft.Icon(ft.icons.SCHOOL, size=32, color=ft.colors.PRIMARY),
                ft.Text("ÖTP", size=11, weight=ft.FontWeight.BOLD, color=ft.colors.PRIMARY),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            padding=10,
        ),
        ft.Divider(height=1),
        *nav_buttons,
        ft.Container(expand=True),
        undo_btn,
        theme_btn,
    ], spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    
    nav_panel = ft.Container(
        content=nav_column,
        width=80,
        bgcolor=ft.colors.SURFACE_VARIANT,
        padding=ft.padding.symmetric(vertical=10),
    )
    
    # İçerik alanı - Stack kullanarak visibility ile kontrol
    content_stack = ft.Stack(
        controls=view_containers,
        expand=True,
    )
    
    # Ana layout
    main_layout = ft.Row([
        nav_panel,
        ft.VerticalDivider(width=1),
        content_stack,
    ], expand=True, spacing=0)
    
    page.add(main_layout)
    
    # Klavye kısayolları
    def on_keyboard(e):
        if e.ctrl and e.key == "Z":
            on_undo(None)
    
    page.on_keyboard_event = on_keyboard


if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
