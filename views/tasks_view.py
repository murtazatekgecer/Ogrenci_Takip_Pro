"""
Görev ve puanlama görünümü - Gelişmiş versiyon
"""
import flet as ft
from database.db_manager import get_database


class TasksView(ft.Column):
    """Görev ve puanlama ekranı"""
    
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.db = get_database()
        self.expand = True
        self.spacing = 20
        
        # Kategori seçimi
        self.category_dropdown = ft.Dropdown(
            label="Kategori Seçin",
            width=250,
            on_change=self.on_category_selected,
        )
        
        # Görev adı
        self.task_name_field = ft.TextField(
            label="Görev Adı",
            hint_text="Örn: 1. Hafta Quiz, Ödev 3",
            width=300,
        )
        
        # Yeni görev oluştur butonu
        self.create_task_button = ft.ElevatedButton(
            "Görev Oluştur ve Puanla",
            icon=ft.icons.ADD_TASK,
            on_click=self.create_task_and_open_scoring,
            style=ft.ButtonStyle(
                bgcolor=ft.colors.PRIMARY,
                color=ft.colors.ON_PRIMARY,
            ),
        )
        
        # Mevcut görevler listesi
        self.tasks_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        
        self.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Text("Görev ve Puanlama", size=28, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    
                    # Yeni görev oluşturma kartı
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text("Yeni Görev Oluştur", size=18, weight=ft.FontWeight.W_500),
                                ft.Text("Kategori ve görev adı girdikten sonra tüm öğrencilere puan verebilirsiniz.", 
                                       size=12, color=ft.colors.GREY),
                                ft.Row([
                                    self.category_dropdown,
                                    self.task_name_field,
                                    self.create_task_button,
                                ], wrap=True, spacing=15),
                            ], spacing=10),
                            padding=20,
                        ),
                    ),
                    
                    ft.Divider(),
                    
                    # Mevcut görevler başlık
                    ft.Row([
                        ft.Text("Mevcut Görevler", size=18, weight=ft.FontWeight.W_500),
                        ft.Container(expand=True),
                        ft.IconButton(
                            icon=ft.icons.REFRESH,
                            tooltip="Yenile",
                            on_click=lambda e: self.load_existing_tasks(),
                        ),
                    ]),
                    
                    # Görev listesi
                    ft.Container(
                        content=self.tasks_list,
                        expand=True,
                    ),
                    
                ], spacing=15, expand=True),
                padding=20,
                expand=True,
            ),
        ]
        
        self.load_initial_data()
    
    def load_initial_data(self):
        """Başlangıç verilerini yükle"""
        categories = self.db.get_all_categories()
        self.category_dropdown.options = [
            ft.dropdown.Option(key=str(c['id']), text=c['isim'])
            for c in categories
        ]
        self.load_existing_tasks()
        self.page.update()
    
    def on_category_selected(self, e):
        """Kategori seçildiğinde"""
        pass
    
    def create_task_and_open_scoring(self, e):
        """Görev oluştur ve puanlama dialogunu aç"""
        if not self.category_dropdown.value:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Lütfen kategori seçin!"),
                bgcolor=ft.colors.RED,
            )
            self.page.snack_bar.open = True
            self.page.update()
            return
        
        if not self.task_name_field.value or not self.task_name_field.value.strip():
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Lütfen görev adı girin!"),
                bgcolor=ft.colors.RED,
            )
            self.page.snack_bar.open = True
            self.page.update()
            return
        
        category_id = int(self.category_dropdown.value)
        task_name = self.task_name_field.value.strip()
        category = self.db.get_category(category_id)
        
        self._open_scoring_dialog(category, task_name, is_new=True)
    
    def _open_scoring_dialog(self, category, task_name, is_new=True, existing_scores=None):
        """Puanlama dialogunu aç"""
        students = self.db.get_all_students()
        
        if not students:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Önce öğrenci eklemelisiniz!"),
                bgcolor=ft.colors.RED,
            )
            self.page.snack_bar.open = True
            self.page.update()
            return
        
        score_fields = {}  # {student_id: TextField}
        
        # Görev adı düzenleme alanı (sadece düzenleme modunda görünür)
        task_name_edit_field = ft.TextField(
            value=task_name,
            label="Görev Adı",
            width=350,
            visible=not is_new,  # Sadece düzenleme modunda göster
        )
        
        # Öğrenci satırları oluştur
        student_rows = []
        for student in students:
            existing_score = ""
            task_id = None
            
            if existing_scores and student['id'] in existing_scores:
                existing_score = str(existing_scores[student['id']]['puan'])
                task_id = existing_scores[student['id']]['task_id']
            
            score_field = ft.TextField(
                value=existing_score,
                width=80,
                keyboard_type=ft.KeyboardType.NUMBER,
                text_align=ft.TextAlign.CENTER,
                hint_text="0-100",
                dense=True,
                data={'student_id': student['id'], 'task_id': task_id},
            )
            score_fields[student['id']] = score_field
            
            # Puan rengi için container
            score_color = ft.colors.GREY
            if existing_score:
                val = int(existing_score)
                score_color = ft.colors.GREEN if val >= 70 else (ft.colors.ORANGE if val >= 50 else ft.colors.RED)
            
            row = ft.Container(
                content=ft.Row([
                    ft.Text(f"{student['ad']} {student['soyad']}", width=180),
                    ft.Container(
                        content=ft.Text(student['sinif'], size=12),
                        bgcolor=ft.colors.PRIMARY_CONTAINER,
                        padding=5,
                        border_radius=3,
                        width=60,
                    ),
                    ft.Text(student['numara'], width=60),
                    score_field,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.symmetric(vertical=8, horizontal=10),
                border=ft.border.only(bottom=ft.BorderSide(1, ft.colors.OUTLINE)),
            )
            student_rows.append(row)
        
        def save_scores(e):
            """Puanları kaydet"""
            # Güncel görev adını al
            current_task_name = task_name_edit_field.value.strip() if not is_new else task_name
            
            if not current_task_name:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Görev adı boş olamaz!"),
                    bgcolor=ft.colors.RED,
                )
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            saved_count = 0
            updated_count = 0
            renamed = current_task_name != task_name and not is_new
            
            for student_id, field in score_fields.items():
                if field.value and field.value.strip():
                    try:
                        score = int(field.value)
                        if 0 <= score <= 100:
                            task_id = field.data.get('task_id')
                            if task_id:
                                # Mevcut görevi güncelle (isim dahil)
                                self.db.update_task(task_id, current_task_name, score)
                                updated_count += 1
                            else:
                                # Yeni görev ekle
                                self.db.add_task(student_id, category['id'], current_task_name, score)
                                saved_count += 1
                    except ValueError:
                        pass
            
            dialog.open = False
            self.task_name_field.value = ""
            self.load_existing_tasks()
            
            msg = ""
            if renamed:
                msg = f"Görev adı '{current_task_name}' olarak değiştirildi. "
            if saved_count > 0:
                msg += f"{saved_count} yeni puan eklendi"
            if updated_count > 0:
                msg += (", " if msg and not renamed else "") + f"{updated_count} puan güncellendi"
            
            if msg:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(msg + "!"),
                    bgcolor=ft.colors.GREEN,
                )
                self.page.snack_bar.open = True
            
            self.page.update()
        
        def close_dialog(e):
            dialog.open = False
            self.page.update()
        
        # Toplu puan girişi için yardımcı butonlar
        def set_all_scores(score):
            for field in score_fields.values():
                field.value = str(score)
            self.page.update()
        
        # Dialog title
        if is_new:
            title_content = ft.Row([
                ft.Icon(ft.icons.ASSIGNMENT, color=ft.colors.PRIMARY),
                ft.Column([
                    ft.Text(task_name, size=18, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Kategori: {category['isim']}", size=12, color=ft.colors.GREY),
                ], spacing=2),
            ])
        else:
            title_content = ft.Row([
                ft.Icon(ft.icons.EDIT, color=ft.colors.PRIMARY),
                ft.Text("Görevi Düzenle", size=18, weight=ft.FontWeight.BOLD),
            ])
        
        dialog = ft.AlertDialog(
            modal=True,
            title=title_content,
            content=ft.Container(
                content=ft.Column([
                    # Görev adı düzenleme (sadece edit modunda)
                    ft.Container(
                        content=ft.Column([
                            task_name_edit_field,
                            ft.Text(f"Kategori: {category['isim']}", size=12, color=ft.colors.GREY),
                        ], spacing=5),
                        visible=not is_new,
                        padding=ft.padding.only(bottom=10),
                    ),
                    # Toplu işlem butonları
                    ft.Row([
                        ft.Text("Hızlı Puan:", size=12),
                        ft.TextButton("100", on_click=lambda e: set_all_scores(100)),
                        ft.TextButton("85", on_click=lambda e: set_all_scores(85)),
                        ft.TextButton("70", on_click=lambda e: set_all_scores(70)),
                        ft.TextButton("50", on_click=lambda e: set_all_scores(50)),
                        ft.TextButton("0", on_click=lambda e: set_all_scores(0)),
                        ft.TextButton("Temizle", on_click=lambda e: set_all_scores("")),
                    ], spacing=5),
                    ft.Divider(),
                    # Başlık satırı
                    ft.Container(
                        content=ft.Row([
                            ft.Text("Öğrenci", width=180, weight=ft.FontWeight.BOLD),
                            ft.Text("Sınıf", width=60, weight=ft.FontWeight.BOLD),
                            ft.Text("No", width=60, weight=ft.FontWeight.BOLD),
                            ft.Text("Puan", weight=ft.FontWeight.BOLD),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        bgcolor=ft.colors.PRIMARY_CONTAINER,
                        padding=10,
                        border_radius=5,
                    ),
                    # Öğrenci listesi
                    ft.Column(
                        controls=student_rows,
                        scroll=ft.ScrollMode.AUTO,
                        height=350,
                    ),
                ], spacing=10),
                width=500,
            ),
            actions=[
                ft.TextButton("İptal", on_click=close_dialog),
                ft.ElevatedButton(
                    "Kaydet",
                    icon=ft.icons.SAVE,
                    on_click=save_scores,
                    style=ft.ButtonStyle(
                        bgcolor=ft.colors.GREEN_700,
                        color=ft.colors.WHITE,
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def load_existing_tasks(self):
        """Mevcut görevleri yükle"""
        self.tasks_list.controls.clear()
        
        categories = self.db.get_all_categories()
        students = self.db.get_all_students()
        
        if not students:
            self.tasks_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.ASSIGNMENT_OUTLINED, size=50, color=ft.colors.GREY),
                        ft.Text("Henüz görev yok", size=16, color=ft.colors.GREY),
                        ft.Text("Yukarıdan yeni görev oluşturun", size=12, color=ft.colors.GREY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    padding=40,
                )
            )
            self.page.update()
            return
        
        has_tasks = False
        
        for cat in categories:
            # Bu kategorideki tüm benzersiz görevleri bul
            task_names = {}  # {task_name: [task_data]}
            
            for student in students:
                tasks = self.db.get_student_tasks_by_category(student['id'], cat['id'])
                for task in tasks:
                    if task['isim'] not in task_names:
                        task_names[task['isim']] = []
                    task_names[task['isim']].append({
                        'student_id': student['id'],
                        'student_name': f"{student['ad']} {student['soyad']}",
                        'task_id': task['id'],
                        'puan': task['puan'],
                    })
            
            if task_names:
                has_tasks = True
                
                # Kategori başlığı
                category_section = ft.ExpansionTile(
                    title=ft.Text(cat['isim'], weight=ft.FontWeight.BOLD),
                    subtitle=ft.Text(f"{len(task_names)} görev", size=12),
                    initially_expanded=True,
                    controls=[],
                )
                
                for task_name, task_data in task_names.items():
                    # Ortalama hesapla
                    avg = sum(t['puan'] for t in task_data) / len(task_data)
                    avg_color = ft.colors.GREEN if avg >= 70 else (ft.colors.ORANGE if avg >= 50 else ft.colors.RED)
                    
                    task_card = ft.Card(
                        content=ft.Container(
                            content=ft.Row([
                                ft.Column([
                                    ft.Text(task_name, size=14, weight=ft.FontWeight.W_500),
                                    ft.Text(f"{len(task_data)} öğrenci puanlandı", size=11, color=ft.colors.GREY),
                                ], spacing=2, expand=True),
                                ft.Container(
                                    content=ft.Text(f"Ort: {avg:.1f}", color=ft.colors.WHITE, size=12),
                                    bgcolor=avg_color,
                                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                    border_radius=15,
                                ),
                                ft.IconButton(
                                    icon=ft.icons.EDIT,
                                    tooltip="Puanları Düzenle",
                                    on_click=lambda e, c=cat, tn=task_name, td=task_data: self.edit_task_scores(c, tn, td),
                                ),
                                ft.IconButton(
                                    icon=ft.icons.DELETE,
                                    tooltip="Görevi Sil",
                                    icon_color=ft.colors.RED,
                                    on_click=lambda e, tn=task_name, td=task_data: self.delete_task_confirm(tn, td),
                                ),
                            ]),
                            padding=10,
                        ),
                    )
                    category_section.controls.append(task_card)
                
                self.tasks_list.controls.append(category_section)
        
        if not has_tasks:
            self.tasks_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.ASSIGNMENT_OUTLINED, size=50, color=ft.colors.GREY),
                        ft.Text("Henüz görev yok", size=16, color=ft.colors.GREY),
                        ft.Text("Yukarıdan yeni görev oluşturun", size=12, color=ft.colors.GREY),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    padding=40,
                )
            )
        
        self.page.update()
    
    def edit_task_scores(self, category, task_name, task_data):
        """Görev puanlarını düzenle"""
        # Mevcut puanları hazırla
        existing_scores = {
            t['student_id']: {'puan': t['puan'], 'task_id': t['task_id']}
            for t in task_data
        }
        
        self._open_scoring_dialog(category, task_name, is_new=False, existing_scores=existing_scores)
    
    def delete_task_confirm(self, task_name, task_data):
        """Görev silme onayı"""
        def delete_all(e):
            for t in task_data:
                self.db.delete_task(t['task_id'])
            
            dialog.open = False
            self.load_existing_tasks()
            
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"'{task_name}' görevi ve tüm puanları silindi!"),
                bgcolor=ft.colors.ORANGE,
            )
            self.page.snack_bar.open = True
            self.page.update()
        
        def close_dialog(e):
            dialog.open = False
            self.page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Görevi Sil"),
            content=ft.Text(
                f"'{task_name}' görevini ve {len(task_data)} öğrencinin puanlarını silmek istediğinize emin misiniz?\n\n"
                "Bu işlem geri alınamaz!"
            ),
            actions=[
                ft.TextButton("İptal", on_click=close_dialog),
                ft.ElevatedButton(
                    "Sil",
                    icon=ft.icons.DELETE,
                    bgcolor=ft.colors.RED,
                    color=ft.colors.WHITE,
                    on_click=delete_all,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def refresh(self):
        """Verileri yenile"""
        self.load_initial_data()
