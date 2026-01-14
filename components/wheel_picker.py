"""
Rastgele öğrenci seçici - Çarkıfelek benzeri.
"""
import flet as ft
import random
import math
import asyncio


class WheelPicker(ft.Container):
    """Rastgele öğrenci seçici."""
    
    def __init__(self, ogrenciler, on_select=None):
        super().__init__()
        self.ogrenciler = ogrenciler
        self.on_select = on_select
        self.is_spinning = False
        self.selected_student = None
        self.animation_angle = 0
        self._build_content()
    
    def _build_content(self):
        if not self.ogrenciler:
            self.content = ft.Column([
                ft.Icon(ft.icons.PEOPLE_OUTLINE, size=60, color=ft.colors.GREY_400),
                ft.Text("Öğrenci listesi boş!", size=16, color=ft.colors.GREY_500),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            self.alignment = ft.alignment.center
            self.height = 300
            return
        
        # Seçilen öğrenci gösterimi
        self.result_text = ft.Text(
            "Çevirmeye hazır!",
            size=24,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )
        
        self.result_container = ft.Container(
            content=self.result_text,
            bgcolor=ft.colors.SURFACE_VARIANT,
            border_radius=15,
            padding=20,
            width=300,
            alignment=ft.alignment.center,
        )
        
        # Çevir butonu
        self.spin_button = ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(ft.icons.SHUFFLE, color=ft.colors.WHITE),
                ft.Text("ÇEVİR!", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
            ], alignment=ft.MainAxisAlignment.CENTER),
            on_click=self._start_spin,
            width=200,
            height=50,
            bgcolor=ft.colors.ORANGE_600,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=25),
            ),
        )
        
        # Öğrenci isimleri listesi (dönen kısım)
        self.names_column = ft.Column(
            controls=self._create_name_items(),
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=5,
        )
        
        self.wheel_container = ft.Container(
            content=self.names_column,
            height=200,
            width=280,
            border=ft.border.all(3, ft.colors.ORANGE_400),
            border_radius=10,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            alignment=ft.alignment.center,
            bgcolor=ft.colors.SURFACE,
        )
        
        # Ok işareti
        arrow = ft.Container(
            content=ft.Icon(ft.icons.ARROW_RIGHT, color=ft.colors.RED, size=30),
            alignment=ft.alignment.center_left,
            margin=ft.margin.only(left=-15),
        )
        
        self.content = ft.Column([
            ft.Text("✨ Rastgele Öğrenci Seçici", 
                   size=22, weight=ft.FontWeight.BOLD, 
                   text_align=ft.TextAlign.CENTER),
            
            ft.Container(height=20),
            
            ft.Stack([
                self.wheel_container,
                arrow,
            ]),
            
            ft.Container(height=20),
            
            self.result_container,
            
            ft.Container(height=20),
            
            self.spin_button,
            
            ft.Container(height=10),
            
            ft.Text(
                f"Toplam {len(self.ogrenciler)} öğrenci",
                size=12, color=ft.colors.GREY_600,
                text_align=ft.TextAlign.CENTER,
            ),
        ], 
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=5)
        self.padding = 20
    
    def _create_name_items(self, highlight_index=None):
        """İsim öğelerini oluşturur."""
        items = []
        display_count = min(7, len(self.ogrenciler))
        
        for i in range(display_count):
            idx = (self.animation_angle + i) % len(self.ogrenciler)
            ogrenci = self.ogrenciler[idx]
            name = f"{ogrenci['ad']} {ogrenci['soyad']}"
            
            is_center = (i == display_count // 2)
            
            item = ft.Container(
                content=ft.Text(
                    name,
                    size=16 if is_center else 13,
                    weight=ft.FontWeight.BOLD if is_center else ft.FontWeight.NORMAL,
                    color=ft.colors.ORANGE_700 if is_center else ft.colors.GREY_600,
                    text_align=ft.TextAlign.CENTER,
                ),
                bgcolor=ft.colors.ORANGE_100 if is_center else None,
                border_radius=5,
                padding=ft.padding.symmetric(horizontal=15, vertical=5),
                width=250,
                alignment=ft.alignment.center,
            )
            items.append(item)
        
        return items
    
    async def _animate_spin(self):
        """Çevirme animasyonu."""
        total_steps = random.randint(30, 50)  # Rastgele dönüş sayısı
        
        for step in range(total_steps):
            self.animation_angle = (self.animation_angle + 1) % len(self.ogrenciler)
            
            # Yavaşlayan hız
            if step < total_steps * 0.7:
                delay = 0.05
            elif step < total_steps * 0.9:
                delay = 0.1
            else:
                delay = 0.2
            
            self.names_column.controls = self._create_name_items()
            self.update()
            await asyncio.sleep(delay)
        
        # Sonuç
        center_idx = len(self._create_name_items()) // 2
        selected_idx = (self.animation_angle + center_idx) % len(self.ogrenciler)
        self.selected_student = self.ogrenciler[selected_idx]
        
        # Sonucu göster
        self.result_text.value = f"🎉 {self.selected_student['ad']} {self.selected_student['soyad']}"
        self.result_text.color = ft.colors.GREEN_700
        self.result_container.bgcolor = ft.colors.GREEN_100
        self.result_container.animate = ft.animation.Animation(300, ft.AnimationCurve.EASE_OUT)
        
        self.is_spinning = False
        self.spin_button.disabled = False
        self.update()
        
        if self.on_select:
            self.on_select(self.selected_student)
    
    def _start_spin(self, e):
        """Çevirmeyi başlatır."""
        if self.is_spinning or not self.ogrenciler:
            return
        
        self.is_spinning = True
        self.spin_button.disabled = True
        self.result_text.value = "Çevriliyor..."
        self.result_text.color = ft.colors.ORANGE_700
        self.result_container.bgcolor = ft.colors.ORANGE_100
        self.update()
        
        # Async animasyon başlat
        self.page.run_task(self._animate_spin)
    
    def reset(self):
        """Seçiciyi sıfırlar."""
        self.selected_student = None
        self.result_text.value = "Çevirmeye hazır!"
        self.result_text.color = ft.colors.ON_SURFACE
        self.result_container.bgcolor = ft.colors.SURFACE_VARIANT
        self.animation_angle = 0
        self.names_column.controls = self._create_name_items()
        self.update()
