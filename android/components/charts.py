"""
Grafik oluşturma bileşenleri.
Flet native chart bileşenlerini kullanır.
"""
import flet as ft
import statistics

class ChartBuilder:
    """Grafik oluşturma sınıfı."""
    
    def __init__(self, dark_mode=False):
        self.dark_mode = dark_mode
        self._setup_style()
    
    def _setup_style(self):
        """Grafik stilini ayarlar."""
        if self.dark_mode:
            self.bg_color = ft.colors.GREY_900
            self.text_color = ft.colors.WHITE
            self.grid_color = ft.colors.GREY_800
            self.primary_color = ft.colors.BLUE_400
            self.secondary_color = ft.colors.GREEN_400
            self.accent_color = ft.colors.ORANGE_400
        else:
            self.bg_color = ft.colors.WHITE
            self.text_color = ft.colors.BLACK
            self.grid_color = ft.colors.GREY_200
            self.primary_color = ft.colors.BLUE
            self.secondary_color = ft.colors.GREEN
            self.accent_color = ft.colors.ORANGE
    
    def set_dark_mode(self, dark_mode):
        """Tema modunu değiştirir."""
        self.dark_mode = dark_mode
        self._setup_style()
    
    def _create_no_data_control(self, message="Henüz veri yok"):
        """Veri olmadığında gösterilecek kontrol."""
        return ft.Container(
            content=ft.Text(message, color=ft.colors.GREY_500, size=16),
            alignment=ft.alignment.center,
            height=200
        )

    def create_student_progress_chart(self, notlar, ogrenci_adi):
        """Öğrencinin zaman içindeki başarı değişimini gösteren çizgi grafik."""
        if not notlar:
            return self._create_no_data_control()

        # Verileri hazırla
        notlar_sorted = sorted(notlar, key=lambda x: x.get('tarih', ''), reverse=False) # Tarihe göre (varsa)
        # Eğer tarih yoksa eklenme sırasına göre varsayıyoruz (zaten liste)
        
        # X ve Y değerleri
        data_points = []
        labels = []
        values = []
        
        for i, note in enumerate(notlar):
            puan = note.get('puan', 0)
            baslik = note.get('baslik', '')[:10]
            values.append(puan)
            labels.append(baslik)
            
            data_points.append(
                ft.LineChartDataPoint(
                    x=i, 
                    y=puan,
                    tooltip=f"{baslik}: {puan}",
                    show_tooltip=True
                )
            )

        if not values:
             return self._create_no_data_control()

        avg = statistics.mean(values)

        return ft.Column([
            ft.Text(f"{ogrenci_adi} - Başarı Değişimi", size=16, weight=ft.FontWeight.BOLD, color=self.text_color),
            ft.Container(
                height=250,
                content=ft.LineChart(
                    data_series=[
                        ft.LineChartData(
                            data_points=data_points,
                            stroke_width=3,
                            color=self.primary_color,
                            curved=True,
                            stroke_cap_round=True,
                            below_line_bgcolor=ft.colors.with_opacity(0.2, self.primary_color),
                        ),
                        # Ortalama Çizgisi
                        ft.LineChartData(
                            data_points=[ft.LineChartDataPoint(x=-1, y=avg), ft.LineChartDataPoint(x=len(values), y=avg)],
                            stroke_width=2,
                            color=self.secondary_color,
                            dash_pattern=[5, 5],
                            curved=False,
                        ),
                         # Geçme Sınırı (50)
                        ft.LineChartData(
                            data_points=[ft.LineChartDataPoint(x=-1, y=50), ft.LineChartDataPoint(x=len(values), y=50)],
                            stroke_width=1,
                            color=ft.colors.RED,
                            dash_pattern=[2, 2],
                            curved=False,
                        )
                    ],
                    border=ft.border.all(1, self.grid_color),
                    left_axis=ft.ChartAxis(
                        labels=[
                            ft.ChartAxisLabel(value=0, label=ft.Text("0", size=10, color=self.text_color)),
                            ft.ChartAxisLabel(value=50, label=ft.Text("50", size=10, color=ft.colors.RED)),
                            ft.ChartAxisLabel(value=100, label=ft.Text("100", size=10, color=self.text_color)),
                        ],
                        labels_size=30,
                    ),
                    bottom_axis=ft.ChartAxis(
                        labels=[
                            ft.ChartAxisLabel(
                                value=i, 
                                label=ft.Container(
                                    ft.Text(l, size=10, color=self.text_color, no_wrap=True),
                                    padding=ft.padding.only(top=10),
                                    rotate=ft.Rotate(0.5) # Hafif eğik
                                )
                            ) for i, l in enumerate(labels)
                        ],
                        labels_size=40,
                    ),
                    tooltip_bgcolor=self.bg_color,
                    min_y=0,
                    max_y=105,
                    min_x=-0.5,
                    max_x=len(values) - 0.5,
                    expand=True,
                )
            ),
             ft.Row([
                ft.Row([ft.Container(width=10, height=10, bgcolor=self.primary_color), ft.Text("Puan", size=12)]),
                ft.Row([ft.Container(width=10, height=2, bgcolor=self.secondary_color), ft.Text(f"Ort: {avg:.1f}", size=12)]),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
        ])

    def create_class_distribution_chart(self, notlar, sinif_adi):
        """Sınıfın not dağılımını gösteren histogram."""
        if not notlar:
             return self._create_no_data_control()
             
        # Histogram hesapla
        bins = [(0, 24), (25, 44), (45, 54), (55, 69), (70, 84), (85, 100)]
        labels = ['0-24', '25-44', '45-54', '55-69', '70-84', '85-100']
        colors = [ft.colors.RED, ft.colors.DEEP_ORANGE, ft.colors.ORANGE, ft.colors.AMBER, ft.colors.LIGHT_GREEN, ft.colors.GREEN]
        counts = [0] * len(bins)
        
        for not_val in notlar:
            for i, (low, high) in enumerate(bins):
                if low <= not_val <= high:
                    counts[i] += 1
                    break
        
        avg = statistics.mean(notlar) if notlar else 0
        
        bar_groups = []
        for i, count in enumerate(counts):
            bar_groups.append(
                ft.BarChartGroup(
                    x=i,
                    bar_rods=[
                        ft.BarChartRod(
                            from_y=0,
                            to_y=count,
                            width=30,
                            color=colors[i],
                            tooltip=f"{labels[i]}: {count} Öğrenci",
                            border_radius=4,
                        )
                    ]
                )
            )

        max_y = max(counts) + 1 if counts else 10

        return ft.Column([
            ft.Text(f"{sinif_adi} - Not Dağılımı", size=16, weight=ft.FontWeight.BOLD, color=self.text_color),
            ft.Container(
                height=250,
                content=ft.BarChart(
                    bar_groups=bar_groups,
                    border=ft.border.all(1, ft.colors.TRANSPARENT),
                    left_axis=ft.ChartAxis(
                        labels_size=30,
                        title=ft.Text("Öğrenci Sayısı", size=10),
                        title_size=20
                    ),
                    bottom_axis=ft.ChartAxis(
                        labels=[
                            ft.ChartAxisLabel(
                                value=i, 
                                label=ft.Container(ft.Text(l, size=10, color=self.text_color), padding=5)
                            ) for i, l in enumerate(labels)
                        ],
                        labels_size=40,
                    ),
                    min_y=0,
                    max_y=max_y,
                    tooltip_bgcolor=self.bg_color,
                )
            ),
             ft.Text(f"Sınıf Ortalaması: {avg:.1f}  |  Toplam Öğrenci: {len(notlar)}", size=12, text_align=ft.TextAlign.CENTER, color=self.text_color)
        ])
    
    def create_category_comparison_chart(self, kategoriler_data, ogrenci_adi=None):
        """Kategorilere göre ortalama karşılaştırma grafiği."""
        if not kategoriler_data:
             return self._create_no_data_control()
        
        labels = list(kategoriler_data.keys())
        values = [kategoriler_data[k] or 0 for k in labels]
        
        bar_groups = []
        for i, val in enumerate(values):
            color = ft.colors.RED
            if val >= 85: color = ft.colors.GREEN
            elif val >= 70: color = ft.colors.LIGHT_GREEN
            elif val >= 55: color = ft.colors.AMBER
            elif val >= 45: color = ft.colors.ORANGE
            
            bar_groups.append(
                ft.BarChartGroup(
                    x=i,
                    bar_rods=[
                        ft.BarChartRod(
                            from_y=0,
                            to_y=val,
                            width=40,
                            color=color,
                            tooltip=f"{labels[i]}: {val:.1f}",
                            border_radius=4,
                        )
                    ]
                )
            )

        title = f"{ogrenci_adi} - " if ogrenci_adi else ""
        title += "Kategori Ortalamaları"

        return ft.Column([
            ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=self.text_color),
            ft.Container(
                height=250,
                content=ft.BarChart(
                    bar_groups=bar_groups,
                    border=ft.border.all(1, ft.colors.TRANSPARENT),
                    left_axis=ft.ChartAxis(
                        labels=[ft.ChartAxisLabel(value=v, label=ft.Text(str(v), size=10)) for v in range(0, 101, 20)],
                        labels_size=30,
                    ),
                    bottom_axis=ft.ChartAxis(
                        labels=[
                            ft.ChartAxisLabel(
                                value=i, 
                                label=ft.Container(ft.Text(l, size=11, weight=ft.FontWeight.BOLD, color=self.text_color), padding=10)
                            ) for i, l in enumerate(labels)
                        ],
                        labels_size=40,
                    ),
                    min_y=0,
                    max_y=100,
                    tooltip_bgcolor=self.bg_color,
                )
            )
        ])
    
    def create_pie_chart(self, data, title="Dağılım"):
        """Pasta grafiği."""
        if not data or all(v == 0 for v in data.values()):
             return self._create_no_data_control()
        
        sections = []
        colors = [ft.colors.GREEN, ft.colors.AMBER, ft.colors.RED, ft.colors.BLUE, ft.colors.PURPLE]
        
        total = sum(data.values())
        
        for i, (label, value) in enumerate(data.items()):
            if value > 0:
                percentage = (value / total) * 100
                sections.append(
                    ft.PieChartSection(
                        value=value,
                        title=f"{percentage:.1f}%",
                        color=colors[i % len(colors)],
                        radius=100,
                        title_style=ft.TextStyle(size=12, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                    )
                )

        # Legend oluştur
        legend_items = []
        for i, (label, value) in enumerate(data.items()):
            legend_items.append(
                ft.Row([
                    ft.Container(width=12, height=12, bgcolor=colors[i % len(colors)], border_radius=2),
                    ft.Text(f"{label} ({value})", size=12, color=self.text_color)
                ], spacing=5)
            )

        return ft.Column([
            ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=self.text_color),
            ft.Row([
                ft.Container(
                    width=200,
                    height=200,
                    content=ft.PieChart(
                        sections=sections,
                        sections_space=2,
                        center_space_radius=0,
                        expand=True
                    )
                ),
                ft.Column(legend_items, spacing=5)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
        ])
