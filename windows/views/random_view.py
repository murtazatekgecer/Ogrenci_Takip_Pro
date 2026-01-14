"""
Rastgele öğrenci seçici görünümü.
"""
import flet as ft
from components.wheel_picker import WheelPicker


class RandomView(ft.Container):
    """Rastgele öğrenci seçici - tam ekran modu."""
    
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.selected_sinif = None
        self._build_content()
    
    def _build_content(self):
        # Sınıf seçici
        siniflar = self.db.get_all_siniflar()
        sinif_options = [ft.dropdown.Option(key="all", text="📚 Tüm Sınıflar")]
        sinif_options.extend([ft.dropdown.Option(key=str(s['id']), text=s['ad']) for s in siniflar])
        
        self.sinif_dropdown = ft.Dropdown(
            label="Sınıf Seçin",
            width=250,
            options=sinif_options,
            on_change=self._on_sinif_change,
        )
        
        # Çarkıfelek container
        self.wheel_container = ft.Container(
            content=ft.Column([
                ft.Icon(ft.icons.SHUFFLE, size=80, color=ft.colors.GREY_400),
                ft.Text("Önce bir sınıf seçin", size=18, color=ft.colors.GREY_500),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            alignment=ft.alignment.center,
            expand=True,
        )
        
        self.content = ft.Column([
            # Başlık
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.SHUFFLE, size=32, color=ft.colors.ORANGE),
                    ft.Text("Rastgele Öğrenci Seçici", size=24, weight=ft.FontWeight.BOLD),
                ], spacing=15),
                padding=ft.padding.only(bottom=20),
            ),
            
            # Sınıf seçici
            ft.Row([
                self.sinif_dropdown,
            ]),
            
            ft.Divider(height=20),
            
            # Çarkıfelek
            self.wheel_container,
        ], expand=True)
        self.expand = True
        self.padding = 20
    
    def _on_sinif_change(self, e):
        """Sınıf değiştiğinde çarkı güncelle."""
        value = e.control.value
        if value == "all":
            self.selected_sinif = None
        else:
            self.selected_sinif = int(value) if value else None
        
        self._update_wheel()
    
    def _update_wheel(self):
        """Çarkı günceller."""
        ogrenciler = self.db.get_all_ogrenciler(self.selected_sinif)
        
        if not ogrenciler:
            self.wheel_container.content = ft.Column([
                ft.Icon(ft.icons.PEOPLE_OUTLINE, size=80, color=ft.colors.GREY_400),
                ft.Text("Bu sınıfta öğrenci yok", size=18, color=ft.colors.GREY_500),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)
        else:
            wheel = WheelPicker(ogrenciler)
            self.wheel_container.content = wheel
        
        self.wheel_container.alignment = ft.alignment.center
        self.update()
    
    def refresh(self):
        """Görünümü yeniler."""
        siniflar = self.db.get_all_siniflar()
        sinif_options = [ft.dropdown.Option(key="all", text="📚 Tüm Sınıflar")]
        sinif_options.extend([ft.dropdown.Option(key=str(s['id']), text=s['ad']) for s in siniflar])
        self.sinif_dropdown.options = sinif_options
        
        if self.selected_sinif or self.sinif_dropdown.value:
            self._update_wheel()
        
        self.update()
