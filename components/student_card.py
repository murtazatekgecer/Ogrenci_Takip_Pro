"""
Öğrenci detay kartı bileşeni.
"""
import flet as ft
import json
from utils.helpers import get_grade_color, get_grade_text, get_badge_info, get_all_badges


class StudentCard(ft.Container):
    """Öğrenci detay kartı."""
    
    def __init__(self, db_manager, ogrenci_id, on_close=None, on_update=None):
        super().__init__()
        self.db = db_manager
        self.ogrenci_id = ogrenci_id
        self.on_close = on_close
        self.on_update = on_update
        self.ogrenci = None
        self.editing_not = None
        self._build_content()
    
    def _build_content(self):
        self.ogrenci = self.db.get_ogrenci_by_id(self.ogrenci_id)
        if not self.ogrenci:
            self.content = ft.Text("Öğrenci bulunamadı!")
            return
        
        # Rozetleri parse et
        try:
            rozetler = json.loads(self.ogrenci.get('rozetler', '[]'))
        except:
            rozetler = []
        
        # Rozet gösterimi
        rozet_row = ft.Row(
            controls=[
                ft.Tooltip(
                    content=ft.Container(
                        content=ft.Text(get_badge_info(r)['icon'], size=24),
                        bgcolor=get_badge_info(r)['color'],
                        border_radius=20,
                        padding=8,
                    ),
                    message=get_badge_info(r)['name']
                ) for r in rozetler
            ] if rozetler else [ft.Text("Rozet yok", italic=True, color=ft.colors.GREY_500)],
            spacing=5
        )
        
        # Genel ortalama
        genel_ort = self.db.get_ogrenci_genel_ortalama(self.ogrenci_id)
        
        # Ana kart
        card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    # Başlık
                    ft.Row([
                        ft.Icon(ft.icons.PERSON, size=40, color=ft.colors.PRIMARY),
                        ft.Column([
                            ft.Text(
                                f"{self.ogrenci['ad']} {self.ogrenci['soyad']}",
                                size=20, weight=ft.FontWeight.BOLD
                            ),
                            ft.Text(
                                f"Okul No: {self.ogrenci['okul_no'] or '-'} | Sınıf: {self.ogrenci.get('sinif_adi', '-')}",
                                size=13, color=ft.colors.GREY_600
                            ),
                        ], spacing=2, expand=True),
                        ft.Container(
                            content=ft.Column([
                                ft.Text("Genel Ortalama", size=11, color=ft.colors.GREY_600),
                                ft.Text(
                                    f"{genel_ort:.1f}" if genel_ort else "-",
                                    size=28, weight=ft.FontWeight.BOLD,
                                    color=get_grade_color(genel_ort)
                                ),
                                ft.Text(
                                    get_grade_text(genel_ort),
                                    size=11, color=get_grade_color(genel_ort)
                                ),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                            bgcolor=ft.colors.SURFACE_VARIANT,
                            border_radius=10,
                            padding=15,
                        ),
                        ft.IconButton(
                            icon=ft.icons.CLOSE,
                            on_click=lambda e: self.on_close() if self.on_close else None
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    
                    ft.Divider(),
                    
                    # Rozetler
                    ft.Row([
                        ft.Text("Rozetler:", weight=ft.FontWeight.BOLD),
                        rozet_row,
                        ft.IconButton(
                            icon=ft.icons.ADD_CIRCLE_OUTLINE,
                            tooltip="Rozet Ekle",
                            on_click=self._show_badge_dialog
                        )
                    ]),
                    
                    ft.Divider(),
                    
                    # Notlar
                    ft.Text("Notlar", size=16, weight=ft.FontWeight.BOLD),
                    self._build_grades_section(),
                    
                ], spacing=10, scroll=ft.ScrollMode.AUTO),
                padding=20,
                width=600,
                height=500,
            ),
            elevation=8,
        )
        
        self.content = card
    
    def _build_grades_section(self):
        """Notlar bölümünü oluşturur."""
        tum_notlar = self.db.get_ogrenci_tum_notlar(self.ogrenci_id)
        
        controls = []
        for kategori_adi, data in tum_notlar.items():
            # Kategori başlığı
            ort = data['ortalama']
            header = ft.Container(
                content=ft.Row([
                    ft.Text(kategori_adi, weight=ft.FontWeight.BOLD, size=14),
                    ft.Container(expand=True),
                    ft.Text(
                        f"Ort: {ort:.1f}" if ort else "Ort: -",
                        color=get_grade_color(ort),
                        weight=ft.FontWeight.BOLD
                    ),
                ]),
                bgcolor=ft.colors.SURFACE_VARIANT,
                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                border_radius=5,
            )
            controls.append(header)
            
            # Notlar
            if data['notlar']:
                for not_item in data['notlar']:
                    puan = not_item['puan']
                    not_row = ft.Container(
                        content=ft.Row([
                            ft.Text(not_item['baslik'], size=13, expand=True),
                            ft.Container(
                                content=ft.Text(
                                    f"{puan:.0f}" if puan else "-",
                                    color=ft.colors.WHITE,
                                    weight=ft.FontWeight.BOLD,
                                    size=12
                                ),
                                bgcolor=get_grade_color(puan),
                                border_radius=5,
                                padding=ft.padding.symmetric(horizontal=10, vertical=3),
                            ),
                        ]),
                        padding=ft.padding.only(left=15, right=10, top=3, bottom=3),
                    )
                    controls.append(not_row)
            else:
                controls.append(
                    ft.Container(
                        content=ft.Text("Bu kategoride not yok", 
                                       italic=True, color=ft.colors.GREY_500, size=12),
                        padding=ft.padding.only(left=15),
                    )
                )
            
            controls.append(ft.Container(height=10))
        
        return ft.Column(controls, spacing=3)
    
    def _show_badge_dialog(self, e):
        """Rozet ekleme dialogunu gösterir."""
        try:
            current_badges = json.loads(self.ogrenci.get('rozetler', '[]'))
        except:
            current_badges = []
        
        all_badges = get_all_badges()
        
        def toggle_badge(badge_id):
            if badge_id in current_badges:
                current_badges.remove(badge_id)
            else:
                current_badges.append(badge_id)
            self.db.update_ogrenci_rozetler(self.ogrenci_id, current_badges)
            dialog.open = False
            self.page.update()
            if self.on_update:
                self.on_update()
            self.update()
        
        badge_chips = []
        for badge in all_badges:
            is_selected = badge['id'] in current_badges
            chip = ft.Container(
                content=ft.Row([
                    ft.Text(badge['icon'], size=20),
                    ft.Text(badge['name'], size=12),
                ], spacing=5),
                bgcolor=badge['color'] if is_selected else ft.colors.SURFACE_VARIANT,
                border_radius=20,
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                on_click=lambda e, bid=badge['id']: toggle_badge(bid),
                ink=True,
            )
            badge_chips.append(chip)
        
        dialog = ft.AlertDialog(
            title=ft.Text("Rozet Ekle/Çıkar"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Eklemek veya çıkarmak için rozete tıklayın:"),
                    ft.Wrap(controls=badge_chips, spacing=10, run_spacing=10),
                ], tight=True),
                width=400,
            ),
            actions=[
                ft.TextButton("Kapat", on_click=lambda e: self._close_dialog(dialog)),
            ],
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _close_dialog(self, dialog):
        dialog.open = False
        self.page.update()
