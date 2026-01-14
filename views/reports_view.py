"""
Raporlama ve görsel analiz görünümü.
"""
import flet as ft
from components.charts import ChartBuilder


class ReportsView(ft.Container):
    """Raporlar ve grafikler."""
    
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.selected_sinif = None
        self.chart_builder = ChartBuilder(dark_mode=False)
        self.sort_column = "name"
        self.sort_descending = False
        self._build_content()
    
    def _build_content(self):
        # Sınıf seçici options
        siniflar = self.db.get_all_siniflar()
        sinif_options = [ft.dropdown.Option(key="all", text="📚 Tüm Sınıflar")]
        sinif_options.extend([ft.dropdown.Option(key=str(s['id']), text=s['ad']) for s in siniflar])
        
        self.sinif_dropdown = ft.Dropdown(
            label="Sınıf Seçin",
            width=250,
            options=sinif_options,
            on_change=self._on_sinif_change,
        )
        
        # Rapor listesi başlığı
        self.list_header = ft.Container(
            content=ft.Row([
                ft.Container(ft.Text("#", weight=ft.FontWeight.BOLD), width=40),
                ft.Container(self._create_header_button("Öğrenci", "name"), expand=True),
                ft.Container(self._create_header_button("Davranış", "cat_0", width=80), width=80, alignment=ft.alignment.center),
                ft.Container(self._create_header_button("Ödev", "cat_1", width=80), width=80, alignment=ft.alignment.center),
                ft.Container(self._create_header_button("Quiz", "cat_2", width=80), width=80, alignment=ft.alignment.center),
                ft.Container(self._create_header_button("Genel", "general", width=80), width=80, alignment=ft.alignment.center),
            ], alignment=ft.MainAxisAlignment.START),
            bgcolor=ft.colors.SURFACE_VARIANT,
            padding=ft.padding.symmetric(horizontal=15, vertical=12),
            border_radius=ft.border_radius.only(top_left=8, top_right=8),
        )

        # Rapor listesi (scrollable değil, ana sayfa scroll olacak)
        self.report_list = ft.Column(spacing=0)
        
        # Tablo container
        self.table_container = ft.Container(
            content=ft.Column([
                self.list_header,
                self.report_list
            ], spacing=0),
            border_radius=8,
            border=ft.border.all(1, ft.colors.OUTLINE_VARIANT),
            bgcolor=ft.colors.SURFACE,
        )
        
        # Özet kartları
        self.summary_row = ft.Row([], spacing=15, scroll=ft.ScrollMode.AUTO)
        
        # Grafik alanları
        self.distribution_chart = ft.Container(
            content=ft.Text("Grafik yükleniyor...", color=ft.colors.ON_SURFACE_VARIANT),
            alignment=ft.alignment.center,
            height=300,
            width=500,
            border=ft.border.all(1, ft.colors.OUTLINE_VARIANT),
            border_radius=10,
        )
        
        self.category_chart = ft.Container(
            content=ft.Text("Grafik yükleniyor...", color=ft.colors.ON_SURFACE_VARIANT),
            alignment=ft.alignment.center,
            height=300,
            width=400,
            border=ft.border.all(1, ft.colors.OUTLINE_VARIANT),
            border_radius=10,
        )
        
        self.content = ft.Column([
            # Üst araç çubuğu
            ft.Row([
                self.sinif_dropdown,
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Yenile",
                    icon=ft.icons.REFRESH,
                    on_click=lambda e: self.refresh(),
                ),
            ]),
            
            ft.Divider(),
            
            # Özet kartları
            self.summary_row,
            
            ft.Container(height=15),
            
            # Grafikler
            ft.Text("Grafikler", size=16, weight=ft.FontWeight.BOLD),
            ft.Row([
                self.distribution_chart,
                self.category_chart,
            ], wrap=True, spacing=15),
            
            ft.Container(height=15),
            
            # Detaylı tablo
            ft.Text("Detaylı Rapor", size=16, weight=ft.FontWeight.BOLD),
            self.table_container,
        ], scroll=ft.ScrollMode.AUTO, expand=True)
        self.expand = True
    
    def did_mount(self):
        self.refresh()
    
    def refresh(self):
        """Raporları yeniler."""
        self._update_sinif_dropdown()
        if self.selected_sinif:
            self._load_report()
            self._load_charts()
    
    def _update_sinif_dropdown(self):
        """Sınıf dropdown'ını günceller."""
        siniflar = self.db.get_all_siniflar()
        sinif_options = [ft.dropdown.Option(key="all", text="📚 Tüm Sınıflar")]
        sinif_options.extend([ft.dropdown.Option(key=str(s['id']), text=s['ad']) for s in siniflar])
        self.sinif_dropdown.options = sinif_options
            
        if self.sinif_dropdown.options and not self.selected_sinif:
            self.sinif_dropdown.value = "all"
            self.selected_sinif = "all"
    
    def _on_sinif_change(self, e):
        """Sınıf değiştiğinde."""
        if e.control.value:
            if e.control.value == "all":
                self.selected_sinif = "all"
            else:
                self.selected_sinif = int(e.control.value)
            self._load_report()
            self._load_charts()
    
    def _load_report(self):
        """Rapor tablosunu yükler."""
        if not self.selected_sinif:
            return

        if self.selected_sinif == "all":
            ogrenciler = self.db.get_all_ogrenciler(None)
        else:
            ogrenciler = self.db.get_all_ogrenciler(self.selected_sinif)

        kategoriler = self.db.get_all_kategoriler()
        
        # Sıralama için veri hazırlığı
        report_data = []
        for ogrenci in ogrenciler:
             data = {'ogrenci': ogrenci, 'genel_ort': self.db.get_ogrenci_genel_ortalama(ogrenci['id'])}
             # Kategori ortalamaları
             cat_avgs = []
             for i, kategori in enumerate(kategoriler[:3]):
                 cat_avgs.append(self.db.get_ogrenci_kategori_ortalama(ogrenci['id'], kategori['id']))
             data['cat_avgs'] = cat_avgs
             report_data.append(data)
             
        # Sıralama fonksiyonu
        def get_sort_key(item):
            if self.sort_column == "name":
                return item['ogrenci']['ad'].lower() + " " + item['ogrenci']['soyad'].lower()
            elif self.sort_column == "general":
                return item['genel_ort'] if item['genel_ort'] is not None else -1
            elif self.sort_column.startswith("cat_"):
                idx = int(self.sort_column.split("_")[1])
                if idx < len(item['cat_avgs']):
                    val = item['cat_avgs'][idx]
                    return val if val is not None else -1
            return 0
            
        report_data.sort(key=get_sort_key, reverse=self.sort_descending)
            
        # Özet hesapla
        toplam = len(ogrenciler)
        basarili = 0
        basarisiz = 0
        ortalamalar = []
        
        self.report_list.controls = []
        for i, item in enumerate(report_data, 1):
            ogrenci = item['ogrenci']
            genel_ort = item['genel_ort']
            cat_avgs = item['cat_avgs']
            
            if genel_ort:
                ortalamalar.append(genel_ort)
                if genel_ort >= 50:
                    basarili += 1
                else:
                    basarisiz += 1
            
            # Kategori ortalamaları hücreleri
            row_cells = [
                ft.Container(ft.Text(str(i)), width=40),
                ft.Container(ft.Column([
                    ft.Text(f"{ogrenci['ad']} {ogrenci['soyad']}"),
                    ft.Text(ogrenci.get('sinif_adi', ''), size=10, color=ft.colors.OUTLINE)
                ], spacing=0), expand=True),
            ]
            
            # 3 kategori için döngü (zaten cat_avgs'da var)
            for j in range(3):
                ort = cat_avgs[j] if j < len(cat_avgs) else None
                row_cells.append(ft.Container(
                    ft.Container(
                        content=ft.Text(f"{ort:.1f}" if ort else "-", size=13, weight=ft.FontWeight.BOLD if ort else None, color=ft.colors.WHITE if ort else None),
                        bgcolor=self._get_color(ort) if ort else None,
                        border_radius=4,
                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                        alignment=ft.alignment.center,
                    ),
                    width=80,
                    alignment=ft.alignment.center,
                ))
            
            # Genel ortalama
            row_cells.append(ft.Container(
                ft.Container(
                    content=ft.Text(
                        f"{genel_ort:.1f}" if genel_ort else "-",
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.WHITE if genel_ort else None,
                    ),
                    bgcolor=self._get_color(genel_ort) if genel_ort else None,
                    border_radius=4,
                    padding=ft.padding.symmetric(horizontal=10, vertical=3),
                ),
                width=80,
                alignment=ft.alignment.center,
            ))
            
            # Row ekle
            item = ft.Container(
                content=ft.Row(row_cells, alignment=ft.MainAxisAlignment.START),
                padding=ft.padding.symmetric(horizontal=15, vertical=8),
                bgcolor=ft.colors.SURFACE_VARIANT if i % 2 == 0 else None,
                border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.OUTLINE_VARIANT)),
            )
            self.report_list.controls.append(item)
        
        # Özet kartlarını güncelle
        sinif_ort = sum(ortalamalar) / len(ortalamalar) if ortalamalar else 0
        
        self.summary_row.controls = [
            self._create_summary_card("Toplam Öğrenci", str(toplam), ft.icons.PEOPLE, ft.colors.BLUE),
            self._create_summary_card("Başarılı", str(basarili), ft.icons.CHECK_CIRCLE, ft.colors.GREEN),
            self._create_summary_card("Başarısız", str(basarisiz), ft.icons.CANCEL, ft.colors.RED),
            self._create_summary_card("Sınıf Ortalaması", f"{sinif_ort:.1f}", ft.icons.ANALYTICS, ft.colors.PURPLE),
        ]
        
        self.report_list.update()
        self.summary_row.update()
        self.update()
    
    def _create_summary_card(self, title, value, icon, color):
        """Özet kartı oluşturur."""
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, size=40, color=color),
                ft.Column([
                    ft.Text(title, size=12, color=ft.colors.ON_SURFACE_VARIANT),
                    ft.Text(value, size=24, weight=ft.FontWeight.BOLD, color=color),
                ], spacing=0),
            ], spacing=15),
            bgcolor=ft.colors.SURFACE_VARIANT,
            border_radius=10,
            padding=15,
            width=200,
        )
    
    def _load_charts(self):
        """Grafikleri yükler."""
        # Not dağılımı grafiği
        sinif_id = None if self.selected_sinif == "all" else self.selected_sinif
        notlar = self.db.get_sinif_not_dagilimi(sinif_id)
        
        sinif_adi = "Tüm Sınıflar"
        if sinif_id:
            siniflar = self.db.get_all_siniflar()
            sinif = next((s for s in siniflar if s['id'] == sinif_id), None)
            sinif_adi = sinif['ad'] if sinif else ""
        
        self.distribution_chart.content = self.chart_builder.create_class_distribution_chart(notlar, sinif_adi)
        
        # Kategori ortalamaları grafiği
        kategoriler = self.db.get_all_kategoriler()
        kategori_data = {}
        for kategori in kategoriler:
            ort = self.db.get_sinif_kategori_ortalama(sinif_id, kategori['id'])
            if ort:
                kategori_data[kategori['ad']] = ort
        
        self.category_chart.content = self.chart_builder.create_category_comparison_chart(kategori_data, sinif_adi)
        
        self.update()
    
    def _get_color(self, value):
        """Değere göre renk döndürür."""
        if value is None:
            return None
        if value >= 85:
            return ft.colors.GREEN
        elif value >= 70:
            return ft.colors.LIGHT_GREEN
        elif value >= 55:
            return ft.colors.ORANGE
        elif value >= 45:
            return ft.colors.DEEP_ORANGE
        else:
            return ft.colors.RED

    def _create_header_button(self, text, column, width=None):
        """Sıralama özellikli başlık butonu oluşturur."""
        icon = None
        if self.sort_column == column:
            icon = ft.icons.ARROW_DOWNWARD if self.sort_descending else ft.icons.ARROW_UPWARD
        
        content = ft.Row([
            ft.Text(text, weight=ft.FontWeight.BOLD, no_wrap=True),
            ft.Icon(icon, size=16) if icon else ft.Container()
        ], spacing=5, alignment=ft.MainAxisAlignment.START)
        if hasattr(ft.alignment, 'center'):
             # Wrap in another container for alignment if provided
             pass
        
        return ft.Container(
            content=content,
            width=width,
            on_click=lambda e: self._sort_report(column),
            ink=True,
            padding=ft.padding.symmetric(horizontal=5, vertical=5),
            border_radius=4,
            alignment=ft.alignment.center if width else ft.alignment.center_left 
        )

    def _sort_report(self, column):
        """Raporu belirtilen sütuna göre sıralar."""
        if self.sort_column == column:
            self.sort_descending = not self.sort_descending
        else:
            self.sort_column = column
            self.sort_descending = False
            
        # Başlıkları güncelle (ok işaretleri için)
        self.list_header.content.controls[1].content = self._create_header_button("Öğrenci", "name")
        self.list_header.content.controls[2].content = self._create_header_button("Davranış", "cat_0", width=80)
        self.list_header.content.controls[3].content = self._create_header_button("Ödev", "cat_1", width=80)
        self.list_header.content.controls[4].content = self._create_header_button("Quiz", "cat_2", width=80)
        self.list_header.content.controls[5].content = self._create_header_button("Genel", "general", width=80)
        
        self.list_header.update()
        self._load_report()
