"""
Öğrenci yönetimi görünümü - CRUD işlemleri
"""
import flet as ft
from database.db_manager import get_database


class StudentsView(ft.Column):
    """Öğrenci yönetimi ekranı"""
    
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.db = get_database()
        self.expand = True
        self.spacing = 20
        
        # Arama kutusu
        self.search_field = ft.TextField(
            label="Öğrenci Ara",
            prefix_icon=ft.icons.SEARCH,
            on_change=self.filter_students,
            expand=True,
        )
        
        # Öğrenci tablosu
        self.students_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("No")),
                ft.DataColumn(ft.Text("Numara")),
                ft.DataColumn(ft.Text("Ad")),
                ft.DataColumn(ft.Text("Soyad")),
                ft.DataColumn(ft.Text("Sınıf")),
                ft.DataColumn(ft.Text("İşlemler")),
            ],
            rows=[],
            border=ft.border.all(1, ft.colors.OUTLINE),
            border_radius=10,
            vertical_lines=ft.BorderSide(1, ft.colors.OUTLINE),
            horizontal_lines=ft.BorderSide(1, ft.colors.OUTLINE),
        )
        
        # Yeni öğrenci butonu
        self.add_button = ft.FloatingActionButton(
            icon=ft.icons.ADD,
            tooltip="Yeni Öğrenci Ekle",
            on_click=self.show_add_dialog,
        )
        
        self.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Text("Öğrenci Yönetimi", size=28, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        self.search_field,
                        ft.ElevatedButton(
                            "Yeni Öğrenci",
                            icon=ft.icons.PERSON_ADD,
                            on_click=self.show_add_dialog,
                        ),
                    ]),
                    ft.Container(
                        content=ft.Column([self.students_table], scroll=ft.ScrollMode.AUTO),
                        expand=True,
                    ),
                ], spacing=15, expand=True),
                padding=20,
                expand=True,
            ),
        ]
        
        self.load_students()
    
    def load_students(self):
        """Öğrencileri yükle"""
        students = self.db.get_all_students()
        self._update_table(students)
    
    def _update_table(self, students):
        """Tabloyu güncelle"""
        self.students_table.rows.clear()
        
        for idx, student in enumerate(students, 1):
            row = ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str(idx))),
                    ft.DataCell(ft.Text(student['numara'])),
                    ft.DataCell(ft.Text(student['ad'])),
                    ft.DataCell(ft.Text(student['soyad'])),
                    ft.DataCell(ft.Text(student['sinif'])),
                    ft.DataCell(
                        ft.Row([
                            ft.IconButton(
                                icon=ft.icons.EDIT,
                                tooltip="Düzenle",
                                on_click=lambda e, s=student: self.show_edit_dialog(s),
                            ),
                            ft.IconButton(
                                icon=ft.icons.DELETE,
                                tooltip="Sil",
                                icon_color=ft.colors.RED,
                                on_click=lambda e, s=student: self.show_delete_dialog(s),
                            ),
                        ])
                    ),
                ]
            )
            self.students_table.rows.append(row)
        
        self.page.update()
    
    def filter_students(self, e):
        """Öğrencileri filtrele"""
        search_term = self.search_field.value.lower()
        students = self.db.get_all_students()
        
        if search_term:
            students = [
                s for s in students
                if search_term in s['ad'].lower() 
                or search_term in s['soyad'].lower()
                or search_term in s['numara'].lower()
                or search_term in s['sinif'].lower()
            ]
        
        self._update_table(students)
    
    def show_add_dialog(self, e):
        """Yeni öğrenci ekleme dialogu"""
        ad_field = ft.TextField(label="Ad", autofocus=True)
        soyad_field = ft.TextField(label="Soyad")
        sinif_field = ft.TextField(label="Sınıf", hint_text="Örn: 10-A")
        numara_field = ft.TextField(label="Numara")
        
        def save_student(e):
            if not all([ad_field.value, soyad_field.value, sinif_field.value, numara_field.value]):
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Tüm alanları doldurunuz!"),
                    bgcolor=ft.colors.RED,
                )
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            self.db.add_student(
                ad=ad_field.value,
                soyad=soyad_field.value,
                sinif=sinif_field.value,
                numara=numara_field.value,
            )
            
            dialog.open = False
            self.load_students()
            
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Öğrenci başarıyla eklendi!"),
                bgcolor=ft.colors.GREEN,
            )
            self.page.snack_bar.open = True
            self.page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Yeni Öğrenci Ekle"),
            content=ft.Column([
                ad_field,
                soyad_field,
                sinif_field,
                numara_field,
            ], tight=True, spacing=10),
            actions=[
                ft.TextButton("İptal", on_click=lambda e: self._close_dialog(dialog)),
                ft.ElevatedButton("Kaydet", on_click=save_student),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def show_edit_dialog(self, student):
        """Öğrenci düzenleme dialogu"""
        ad_field = ft.TextField(label="Ad", value=student['ad'], autofocus=True)
        soyad_field = ft.TextField(label="Soyad", value=student['soyad'])
        sinif_field = ft.TextField(label="Sınıf", value=student['sinif'])
        numara_field = ft.TextField(label="Numara", value=student['numara'])
        
        def update_student(e):
            if not all([ad_field.value, soyad_field.value, sinif_field.value, numara_field.value]):
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Tüm alanları doldurunuz!"),
                    bgcolor=ft.colors.RED,
                )
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            self.db.update_student(
                student_id=student['id'],
                ad=ad_field.value,
                soyad=soyad_field.value,
                sinif=sinif_field.value,
                numara=numara_field.value,
            )
            
            dialog.open = False
            self.load_students()
            
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Öğrenci bilgileri güncellendi!"),
                bgcolor=ft.colors.GREEN,
            )
            self.page.snack_bar.open = True
            self.page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Öğrenci Düzenle"),
            content=ft.Column([
                ad_field,
                soyad_field,
                sinif_field,
                numara_field,
            ], tight=True, spacing=10),
            actions=[
                ft.TextButton("İptal", on_click=lambda e: self._close_dialog(dialog)),
                ft.ElevatedButton("Güncelle", on_click=update_student),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def show_delete_dialog(self, student):
        """Öğrenci silme onay dialogu"""
        def delete_student(e):
            self.db.delete_student(student['id'])
            dialog.open = False
            self.load_students()
            
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Öğrenci silindi!"),
                bgcolor=ft.colors.ORANGE,
            )
            self.page.snack_bar.open = True
            self.page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Öğrenci Sil"),
            content=ft.Text(f"{student['ad']} {student['soyad']} adlı öğrenciyi silmek istediğinize emin misiniz?"),
            actions=[
                ft.TextButton("İptal", on_click=lambda e: self._close_dialog(dialog)),
                ft.ElevatedButton(
                    "Sil",
                    bgcolor=ft.colors.RED,
                    color=ft.colors.WHITE,
                    on_click=delete_student,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def _close_dialog(self, dialog):
        """Dialogu kapat"""
        dialog.open = False
        self.page.update()
