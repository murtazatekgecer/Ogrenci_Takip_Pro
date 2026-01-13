"""
Kategori yönetimi görünümü
"""
import flet as ft
from database.db_manager import get_database


class CategoriesView(ft.Column):
    """Kategori yönetimi ekranı"""
    
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.db = get_database()
        self.expand = True
        self.spacing = 20
        
        # Kategori listesi
        self.categories_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        
        self.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Text("Kategori Yönetimi", size=28, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        "Davranış, Ödev ve Quiz varsayılan kategorilerdir. Yeni kategoriler ekleyebilir veya mevcut kategorileri düzenleyebilirsiniz.",
                        size=14,
                        color=ft.colors.GREY,
                    ),
                    ft.Divider(),
                    ft.ElevatedButton(
                        "Yeni Kategori Ekle",
                        icon=ft.icons.ADD_CIRCLE,
                        on_click=self.show_add_dialog,
                    ),
                    ft.Container(
                        content=self.categories_list,
                        expand=True,
                    ),
                ], spacing=15, expand=True),
                padding=20,
                expand=True,
            ),
        ]
        
        self.load_categories()
    
    def load_categories(self):
        """Kategorileri yükle"""
        categories = self.db.get_all_categories()
        self.categories_list.controls.clear()
        
        for cat in categories:
            is_default = cat.get('varsayilan', 0) == 1
            
            card = ft.Card(
                content=ft.Container(
                    content=ft.Row([
                        ft.Icon(
                            ft.icons.CATEGORY,
                            size=40,
                            color=ft.colors.PRIMARY,
                        ),
                        ft.Column([
                            ft.Text(
                                cat['isim'],
                                size=18,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                "Varsayılan Kategori" if is_default else "Özel Kategori",
                                size=12,
                                color=ft.colors.GREY,
                            ),
                        ], spacing=2, expand=True),
                        ft.Row([
                            ft.IconButton(
                                icon=ft.icons.EDIT,
                                tooltip="Düzenle",
                                on_click=lambda e, c=cat: self.show_edit_dialog(c),
                            ),
                            ft.IconButton(
                                icon=ft.icons.DELETE,
                                tooltip="Sil",
                                icon_color=ft.colors.RED,
                                on_click=lambda e, c=cat: self.show_delete_dialog(c),
                            ),
                        ]),
                    ], alignment=ft.MainAxisAlignment.START),
                    padding=15,
                ),
            )
            self.categories_list.controls.append(card)
        
        self.page.update()
    
    def show_add_dialog(self, e):
        """Yeni kategori ekleme dialogu"""
        isim_field = ft.TextField(label="Kategori Adı", autofocus=True)
        
        def save_category(e):
            if not isim_field.value:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Kategori adı giriniz!"),
                    bgcolor=ft.colors.RED,
                )
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            try:
                self.db.add_category(isim=isim_field.value)
                dialog.open = False
                self.load_categories()
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Kategori başarıyla eklendi!"),
                    bgcolor=ft.colors.GREEN,
                )
                self.page.snack_bar.open = True
                self.page.update()
            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Bu kategori zaten mevcut!"),
                    bgcolor=ft.colors.RED,
                )
                self.page.snack_bar.open = True
                self.page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Yeni Kategori Ekle"),
            content=ft.Column([isim_field], tight=True),
            actions=[
                ft.TextButton("İptal", on_click=lambda e: self._close_dialog(dialog)),
                ft.ElevatedButton("Kaydet", on_click=save_category),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def show_edit_dialog(self, category):
        """Kategori düzenleme dialogu"""
        isim_field = ft.TextField(label="Kategori Adı", value=category['isim'], autofocus=True)
        
        def update_category(e):
            if not isim_field.value:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Kategori adı giriniz!"),
                    bgcolor=ft.colors.RED,
                )
                self.page.snack_bar.open = True
                self.page.update()
                return
            
            try:
                self.db.update_category(category_id=category['id'], isim=isim_field.value)
                dialog.open = False
                self.load_categories()
                
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Kategori güncellendi!"),
                    bgcolor=ft.colors.GREEN,
                )
                self.page.snack_bar.open = True
                self.page.update()
            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Bu kategori adı zaten mevcut!"),
                    bgcolor=ft.colors.RED,
                )
                self.page.snack_bar.open = True
                self.page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Kategori Düzenle"),
            content=ft.Column([isim_field], tight=True),
            actions=[
                ft.TextButton("İptal", on_click=lambda e: self._close_dialog(dialog)),
                ft.ElevatedButton("Güncelle", on_click=update_category),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def show_delete_dialog(self, category):
        """Kategori silme onay dialogu"""
        def delete_category(e):
            self.db.delete_category(category['id'])
            dialog.open = False
            self.load_categories()
            
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Kategori silindi!"),
                bgcolor=ft.colors.ORANGE,
            )
            self.page.snack_bar.open = True
            self.page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Kategori Sil"),
            content=ft.Text(
                f"'{category['isim']}' kategorisini silmek istediğinize emin misiniz?\n\n"
                "Bu kategoriye ait tüm puanlar da silinecektir!"
            ),
            actions=[
                ft.TextButton("İptal", on_click=lambda e: self._close_dialog(dialog)),
                ft.ElevatedButton(
                    "Sil",
                    bgcolor=ft.colors.RED,
                    color=ft.colors.WHITE,
                    on_click=delete_category,
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
