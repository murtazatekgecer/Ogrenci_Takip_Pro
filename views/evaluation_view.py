"""
Değerlendirme görünümü - Tüm öğrencilerin özet tablosu
"""
import flet as ft
from database.db_manager import get_database


class EvaluationView(ft.Column):
    """Değerlendirme ekranı"""
    
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.db = get_database()
        self.expand = True
        self.spacing = 20
        
        # Sınıf filtresi
        self.class_filter = ft.Dropdown(
            label="Sınıf Filtrele",
            width=200,
            on_change=self.on_filter_change,
        )
        
        # Değerlendirme tablosu container
        self.table_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
        
        self.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Text("Değerlendirme", size=28, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        "Tüm öğrencilerin kategori bazlı not ortalamaları ve genel ortalamaları.",
                        size=14,
                        color=ft.colors.GREY,
                    ),
                    ft.Divider(),
                    ft.Row([
                        self.class_filter,
                        ft.ElevatedButton(
                            "Yenile",
                            icon=ft.icons.REFRESH,
                            on_click=lambda e: self.load_data(),
                        ),
                    ]),
                    self.table_container,
                ], spacing=15, expand=True),
                padding=20,
                expand=True,
            ),
        ]
        
        self.load_data()
    
    def load_data(self):
        """Verileri yükle ve tabloyu oluştur"""
        # Sınıf filtresi güncelle
        classes = self.db.get_all_classes()
        self.class_filter.options = [ft.dropdown.Option(key="all", text="Tümü")]
        self.class_filter.options.extend([
            ft.dropdown.Option(key=c, text=c) for c in classes
        ])
        
        if not self.class_filter.value:
            self.class_filter.value = "all"
        
        # Verileri al
        eval_data = self.db.get_evaluation_data()
        categories = self.db.get_all_categories()
        
        # Sınıf filtresi uygula
        if self.class_filter.value and self.class_filter.value != "all":
            eval_data = [e for e in eval_data if e['sinif'] == self.class_filter.value]
        
        self._build_table(eval_data, categories)
    
    def _build_table(self, eval_data, categories):
        """Tablo oluştur"""
        self.table_container.controls.clear()
        
        if not eval_data:
            self.table_container.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.SCHOOL_OUTLINED, size=60, color=ft.colors.GREY),
                        ft.Text("Henüz öğrenci kaydı yok", size=16, color=ft.colors.GREY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    padding=40,
                )
            )
            self.page.update()
            return
        
        # Tablo sütunları
        columns = [
            ft.DataColumn(ft.Text("No", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Sınıf", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Numara", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Ad Soyad", weight=ft.FontWeight.BOLD)),
        ]
        
        for cat in categories:
            columns.append(ft.DataColumn(ft.Text(cat['isim'], weight=ft.FontWeight.BOLD)))
        
        columns.append(ft.DataColumn(ft.Text("Genel", weight=ft.FontWeight.BOLD)))
        
        # Tablo satırları
        rows = []
        for idx, student in enumerate(eval_data, 1):
            cells = [
                ft.DataCell(ft.Text(str(idx))),
                ft.DataCell(ft.Text(student['sinif'])),
                ft.DataCell(ft.Text(student['numara'])),
                ft.DataCell(ft.Text(f"{student['ad']} {student['soyad']}")),
            ]
            
            for cat in categories:
                avg = student['kategoriler'].get(cat['isim'], 0)
                color = self._get_grade_color(avg)
                cells.append(
                    ft.DataCell(
                        ft.Text(
                            f"{avg:.1f}" if avg > 0 else "-",
                            color=color,
                            weight=ft.FontWeight.W_500,
                        )
                    )
                )
            
            # Genel ortalama
            genel = student['genel_ortalama']
            genel_color = self._get_grade_color(genel)
            cells.append(
                ft.DataCell(
                    ft.Container(
                        content=ft.Text(
                            f"{genel:.1f}" if genel > 0 else "-",
                            color=ft.colors.WHITE if genel > 0 else ft.colors.GREY,
                            weight=ft.FontWeight.BOLD,
                        ),
                        bgcolor=genel_color if genel > 0 else None,
                        padding=8,
                        border_radius=5,
                    )
                )
            )
            
            rows.append(ft.DataRow(cells=cells))
        
        table = ft.DataTable(
            columns=columns,
            rows=rows,
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=10,
            vertical_lines=ft.BorderSide(1, ft.colors.OUTLINE),
            horizontal_lines=ft.BorderSide(1, ft.colors.OUTLINE),
            heading_row_color=ft.colors.PRIMARY_CONTAINER,
        )
        
        self.table_container.controls.append(table)
        
        # İstatistik kartları
        stats_row = ft.Row([
            self._create_stat_card("Toplam Öğrenci", str(len(eval_data)), ft.icons.PEOPLE),
            self._create_stat_card(
                "Sınıf Ortalaması",
                f"{sum(s['genel_ortalama'] for s in eval_data) / len(eval_data):.1f}" if eval_data else "0",
                ft.icons.ANALYTICS,
            ),
        ], wrap=True)
        
        self.table_container.controls.insert(0, stats_row)
        
        self.page.update()
    
    def _get_grade_color(self, grade):
        """Not için renk döndür"""
        if grade >= 70:
            return ft.colors.GREEN
        elif grade >= 50:
            return ft.colors.ORANGE
        elif grade > 0:
            return ft.colors.RED
        return ft.colors.GREY
    
    def _create_stat_card(self, title, value, icon):
        """İstatistik kartı oluştur"""
        return ft.Card(
            content=ft.Container(
                content=ft.Row([
                    ft.Icon(icon, size=40, color=ft.colors.PRIMARY),
                    ft.Column([
                        ft.Text(title, size=12, color=ft.colors.GREY),
                        ft.Text(value, size=24, weight=ft.FontWeight.BOLD),
                    ], spacing=2),
                ]),
                padding=15,
            ),
            width=200,
        )
    
    def on_filter_change(self, e):
        """Filtre değiştiğinde"""
        self.load_data()
    
    def refresh(self):
        """Verileri yenile"""
        self.load_data()
