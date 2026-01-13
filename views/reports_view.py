"""
Raporlama görünümü - PDF ve Excel export
"""
import flet as ft
import os
from datetime import datetime
from database.db_manager import get_database
from utils.excel_exporter import export_to_excel
from utils.pdf_exporter import export_to_pdf


class ReportsView(ft.Column):
    """Raporlama ekranı"""
    
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.db = get_database()
        self.expand = True
        self.spacing = 20
        
        # Sınıf seçimi
        self.class_dropdown = ft.Dropdown(
            label="Sınıf Seçin",
            width=200,
            on_change=self.on_class_change,
        )
        
        # Durum mesajı
        self.status_text = ft.Text("", size=14)
        
        # Export butonları
        self.excel_button = ft.ElevatedButton(
            "Excel Olarak İndir",
            icon=ft.icons.TABLE_CHART,
            on_click=self.export_excel,
            style=ft.ButtonStyle(
                bgcolor=ft.colors.GREEN_700,
                color=ft.colors.WHITE,
            ),
        )
        
        self.pdf_button = ft.ElevatedButton(
            "PDF Olarak İndir",
            icon=ft.icons.PICTURE_AS_PDF,
            on_click=self.export_pdf,
            style=ft.ButtonStyle(
                bgcolor=ft.colors.RED_700,
                color=ft.colors.WHITE,
            ),
        )
        
        # Önizleme alanı
        self.preview_container = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
        
        self.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Text("Raporlar", size=28, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        "Öğrenci notlarını sınıf bazında PDF veya Excel olarak dışa aktarın.",
                        size=14,
                        color=ft.colors.GREY,
                    ),
                    ft.Divider(),
                    ft.Row([
                        self.class_dropdown,
                        self.excel_button,
                        self.pdf_button,
                    ], wrap=True),
                    self.status_text,
                    ft.Divider(),
                    ft.Text("Önizleme", size=18, weight=ft.FontWeight.W_500),
                    self.preview_container,
                ], spacing=15, expand=True),
                padding=20,
                expand=True,
            ),
        ]
        
        self.load_classes()
    
    def load_classes(self):
        """Sınıfları yükle"""
        classes = self.db.get_all_classes()
        self.class_dropdown.options = [ft.dropdown.Option(key="all", text="Tüm Sınıflar")]
        self.class_dropdown.options.extend([
            ft.dropdown.Option(key=c, text=c) for c in classes
        ])
        self.class_dropdown.value = "all"
        self.load_preview()
    
    def on_class_change(self, e):
        """Sınıf değiştiğinde"""
        self.load_preview()
    
    def load_preview(self):
        """Önizleme yükle"""
        self.preview_container.controls.clear()
        
        selected_class = self.class_dropdown.value
        if selected_class == "all":
            report_data = self.db.get_report_data_by_class()
        else:
            report_data = self.db.get_report_data_by_class(selected_class)
        
        categories = self.db.get_all_categories()
        
        if not report_data or all(len(students) == 0 for students in report_data.values()):
            self.preview_container.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.DESCRIPTION_OUTLINED, size=60, color=ft.colors.GREY),
                        ft.Text("Rapor için veri bulunamadı", size=16, color=ft.colors.GREY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    padding=40,
                )
            )
            self.page.update()
            return
        
        for sinif, students in report_data.items():
            if not students:
                continue
            
            # Sınıf başlığı
            self.preview_container.controls.append(
                ft.Container(
                    content=ft.Text(f"Sınıf: {sinif}", size=16, weight=ft.FontWeight.BOLD),
                    bgcolor=ft.colors.PRIMARY_CONTAINER,
                    padding=10,
                    border_radius=5,
                )
            )
            
            # Tablo sütunları
            columns = [
                ft.DataColumn(ft.Text("No")),
                ft.DataColumn(ft.Text("Numara")),
                ft.DataColumn(ft.Text("Ad")),
                ft.DataColumn(ft.Text("Soyad")),
            ]
            
            for cat in categories:
                columns.append(ft.DataColumn(ft.Text(cat['isim'][:10])))
            
            columns.append(ft.DataColumn(ft.Text("Genel")))
            
            # Tablo satırları
            rows = []
            for idx, student in enumerate(students, 1):
                cells = [
                    ft.DataCell(ft.Text(str(idx))),
                    ft.DataCell(ft.Text(student['numara'])),
                    ft.DataCell(ft.Text(student['ad'])),
                    ft.DataCell(ft.Text(student['soyad'])),
                ]
                
                for cat in categories:
                    avg = student['kategoriler'].get(cat['isim'], {}).get('ortalama', 0)
                    color = self._get_grade_color(avg)
                    cells.append(
                        ft.DataCell(ft.Text(f"{avg:.1f}", color=color))
                    )
                
                genel = student.get('genel_ortalama', 0)
                cells.append(
                    ft.DataCell(
                        ft.Text(
                            f"{genel:.1f}",
                            weight=ft.FontWeight.BOLD,
                            color=self._get_grade_color(genel),
                        )
                    )
                )
                
                rows.append(ft.DataRow(cells=cells))
            
            table = ft.DataTable(
                columns=columns,
                rows=rows,
                border=ft.border.all(1, ft.colors.OUTLINE),
                border_radius=5,
            )
            
            self.preview_container.controls.append(table)
            self.preview_container.controls.append(ft.Container(height=20))
        
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
    
    def export_excel(self, e):
        """Excel olarak export et"""
        try:
            selected_class = self.class_dropdown.value
            if selected_class == "all":
                report_data = self.db.get_report_data_by_class()
            else:
                report_data = self.db.get_report_data_by_class(selected_class)
            
            categories = self.db.get_all_categories()
            
            if not report_data or all(len(students) == 0 for students in report_data.values()):
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Export için veri bulunamadı!"),
                    bgcolor=ft.colors.RED,
                )
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            # Dosya yolu
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
            os.makedirs(downloads_path, exist_ok=True)
            filepath = os.path.join(downloads_path, f"ogrenci_rapor_{timestamp}.xlsx")
            
            export_to_excel(report_data, categories, filepath)
            
            self.status_text.value = f"✅ Excel dosyası kaydedildi: {filepath}"
            self.status_text.color = ft.colors.GREEN
            
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Excel dosyası kaydedildi!"),
                bgcolor=ft.colors.GREEN,
                action="Aç",
                on_action=lambda e: os.startfile(filepath) if os.name == 'nt' else None,
            )
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as ex:
            self.status_text.value = f"❌ Hata: {str(ex)}"
            self.status_text.color = ft.colors.RED
            self.page.update()
    
    def export_pdf(self, e):
        """PDF olarak export et"""
        try:
            selected_class = self.class_dropdown.value
            if selected_class == "all":
                report_data = self.db.get_report_data_by_class()
            else:
                report_data = self.db.get_report_data_by_class(selected_class)
            
            categories = self.db.get_all_categories()
            
            if not report_data or all(len(students) == 0 for students in report_data.values()):
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Export için veri bulunamadı!"),
                    bgcolor=ft.colors.RED,
                )
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            # Dosya yolu
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
            os.makedirs(downloads_path, exist_ok=True)
            filepath = os.path.join(downloads_path, f"ogrenci_rapor_{timestamp}.pdf")
            
            export_to_pdf(report_data, categories, filepath)
            
            self.status_text.value = f"✅ PDF dosyası kaydedildi: {filepath}"
            self.status_text.color = ft.colors.GREEN
            
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"PDF dosyası kaydedildi!"),
                bgcolor=ft.colors.GREEN,
                action="Aç",
                on_action=lambda e: os.startfile(filepath) if os.name == 'nt' else None,
            )
            self.page.snack_bar.open = True
            self.page.update()
            
        except Exception as ex:
            self.status_text.value = f"❌ Hata: {str(ex)}"
            self.status_text.color = ft.colors.RED
            self.page.update()
    
    def refresh(self):
        """Verileri yenile"""
        self.load_classes()
