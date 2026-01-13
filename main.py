"""
Öğrenci Takip Pro - Ana Uygulama
Cross-platform öğrenci takip ve değerlendirme uygulaması
"""
import flet as ft
from views.students_view import StudentsView
from views.categories_view import CategoriesView
from views.tasks_view import TasksView
from views.evaluation_view import EvaluationView
from views.reports_view import ReportsView


def main(page: ft.Page):
    """Ana uygulama fonksiyonu"""
    
    # Sayfa ayarları
    page.title = "Öğrenci Takip Pro"
    page.window.width = 1200
    page.window.height = 800
    page.window.min_width = 800
    page.window.min_height = 600
    
    # Uygulama ikonu (Windows için)
    page.window.icon = "assets/icon.png"
    
    # Varsayılan tema (karanlık mod)
    page.theme_mode = ft.ThemeMode.DARK
    
    # Tema renkleri
    page.theme = ft.Theme(
        color_scheme_seed=ft.colors.BLUE,
    )
    page.dark_theme = ft.Theme(
        color_scheme_seed=ft.colors.BLUE,
    )
    
    # Görünümler
    students_view = StudentsView(page)
    categories_view = CategoriesView(page)
    tasks_view = TasksView(page)
    evaluation_view = EvaluationView(page)
    reports_view = ReportsView(page)
    
    # Görünüm listesi
    views = [students_view, categories_view, tasks_view, evaluation_view, reports_view]
    
    # Başlangıçta sadece ilk görünüm visible
    for i, view in enumerate(views):
        view.visible = (i == 0)
    
    # İçerik alanı - tüm görünümler stack içinde
    content_area = ft.Column(
        controls=views,
        expand=True,
    )
    
    def change_view(index):
        """Görünümü değiştir"""
        # Tüm görünümleri gizle, sadece seçileni göster
        for i, view in enumerate(views):
            view.visible = (i == index)
        
        # Verileri yenile
        selected_view = views[index]
        if hasattr(selected_view, 'refresh'):
            selected_view.refresh()
        elif hasattr(selected_view, 'load_students'):
            selected_view.load_students()
        elif hasattr(selected_view, 'load_categories'):
            selected_view.load_categories()
        elif hasattr(selected_view, 'load_data'):
            selected_view.load_data()
        
        # Navigation rail ve bar sync
        rail.selected_index = index
        bottom_nav.selected_index = index
        
        page.update()
    
    def toggle_theme(e):
        """Tema değiştir (Gündüz/Gece)"""
        if page.theme_mode == ft.ThemeMode.DARK:
            page.theme_mode = ft.ThemeMode.LIGHT
            theme_button.icon = ft.icons.DARK_MODE
            theme_button.tooltip = "Gece Moduna Geç"
        else:
            page.theme_mode = ft.ThemeMode.DARK
            theme_button.icon = ft.icons.LIGHT_MODE
            theme_button.tooltip = "Gündüz Moduna Geç"
        page.update()
    
    # Tema değiştirme butonu
    theme_button = ft.IconButton(
        icon=ft.icons.LIGHT_MODE,
        tooltip="Gündüz Moduna Geç",
        on_click=toggle_theme,
    )
    
    # Navigation Rail
    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=200,
        leading=ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.SCHOOL, size=40),
                    ft.Text("ÖTP", size=16, weight=ft.FontWeight.BOLD),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
                padding=10,
            ),
            theme_button,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.icons.PEOPLE_OUTLINE,
                selected_icon=ft.icons.PEOPLE,
                label="Öğrenciler",
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.CATEGORY_OUTLINED,
                selected_icon=ft.icons.CATEGORY,
                label="Kategoriler",
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.ASSIGNMENT_OUTLINED,
                selected_icon=ft.icons.ASSIGNMENT,
                label="Görevler",
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.ANALYTICS_OUTLINED,
                selected_icon=ft.icons.ANALYTICS,
                label="Değerlendirme",
            ),
            ft.NavigationRailDestination(
                icon=ft.icons.DOWNLOAD_OUTLINED,
                selected_icon=ft.icons.DOWNLOAD,
                label="Raporlar",
            ),
        ],
        on_change=lambda e: change_view(e.control.selected_index),
    )
    
    # Mobil için BottomNavigationBar
    bottom_nav = ft.NavigationBar(
        selected_index=0,
        destinations=[
            ft.NavigationBarDestination(icon=ft.icons.PEOPLE, label="Öğrenciler"),
            ft.NavigationBarDestination(icon=ft.icons.CATEGORY, label="Kategoriler"),
            ft.NavigationBarDestination(icon=ft.icons.ASSIGNMENT, label="Görevler"),
            ft.NavigationBarDestination(icon=ft.icons.ANALYTICS, label="Değerlendirme"),
            ft.NavigationBarDestination(icon=ft.icons.DOWNLOAD, label="Raporlar"),
        ],
        on_change=lambda e: change_view(e.control.selected_index),
    )
    
    # Responsive layout
    def on_resize(e):
        """Pencere boyutu değiştiğinde layout güncelle"""
        if page.width and page.width < 768:
            # Mobil görünüm
            rail.visible = False
            bottom_nav.visible = True
        else:
            # Masaüstü görünüm
            rail.visible = True
            bottom_nav.visible = False
        page.update()
    
    page.on_resized = on_resize
    
    # Ana layout
    page.add(
        ft.Row([
            rail,
            ft.VerticalDivider(width=1),
            content_area,
        ], expand=True),
    )
    
    page.navigation_bar = bottom_nav
    
    # İlk yükleme
    on_resize(None)


if __name__ == "__main__":
    ft.app(target=main)
