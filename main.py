# -*- coding: utf-8 -*-
"""Gafori Studio - Android textile pattern maker."""
import os, random
from datetime import datetime
from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
from kivy.uix.image import Image as KivyImage
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from PIL import Image

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    def fa(s):
        return get_display(arabic_reshaper.reshape(str(s)))
except Exception:
    def fa(s):
        return str(s)

# Android shared-storage path; fallback is the app's private documents folder.
def get_app_dir():
    preferred = "/storage/emulated/0/GaforiStudio"
    try:
        os.makedirs(preferred, exist_ok=True)
        probe = os.path.join(preferred, ".write_test")
        with open(probe, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(probe)
        return preferred
    except Exception:
        path = os.path.join(App.get_running_app().user_data_dir, "GaforiStudio")
        os.makedirs(path, exist_ok=True)
        return path

FONT_CANDIDATES = [
    "/system/fonts/NotoNaskhArabic-Regular.ttf",
    "/system/fonts/NotoSansArabic-Regular.ttf",
    "/system/fonts/DroidSans.ttf",
]
FONT_PATH = next((p for p in FONT_CANDIDATES if os.path.exists(p)), None)

def label(text, **kw):
    kw.setdefault("font_size", "14sp")
    if FONT_PATH:
        kw.setdefault("font_name", FONT_PATH)
    return Label(text=fa(text), **kw)

def button(text, **kw):
    kw.setdefault("font_size", "13sp")
    if FONT_PATH:
        kw.setdefault("font_name", FONT_PATH)
    kw.setdefault("size_hint_y", None)
    kw.setdefault("height", dp(42))
    return Button(text=fa(text), **kw)

class PatternEditor(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(5), padding=dp(7), **kwargs)
        self.source_image = None
        self.preview_image = None
        self.columns, self.rows = 2, 7
        self.scale_percent, self.gap_percent = 100, 12
        self.rotation = 0
        self.staggered, self.random_rotation = True, False
        self.bg_rgb = (238, 235, 239)
        self.out_w, self.out_h = 2400, 3600
        with self.canvas.before:
            Color(.08, .09, .12, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.add_widget(label("GAFORI STUDIO | طراحی پترن پارچه",
                              size_hint_y=None, height=dp(40), font_size="17sp",
                              color=(1, 1, 1, 1)))
        top = GridLayout(cols=2, spacing=dp(5), size_hint_y=None, height=dp(88))
        top.add_widget(button("انتخاب عکس گل / نقش", on_release=self.open_image))
        top.add_widget(button("ساخت پترن", on_release=self.generate_pattern))
        top.add_widget(button("ذخیره PNG", on_release=self.save_pattern))
        top.add_widget(button("ذخیره نقش شفاف", on_release=self.save_cutout))
        self.add_widget(top)

        self.preview = KivyImage(allow_stretch=True, keep_ratio=True, size_hint_y=1)
        self.add_widget(self.preview)
        self.status = label("عکس نقش را انتخاب کن؛ بعد تنظیمات را انجام بده.",
                            size_hint_y=None, height=dp(42), color=(1,1,1,1),
                            font_size="12sp")
        self.add_widget(self.status)

        scroll = ScrollView(size_hint_y=None, height=dp(320), do_scroll_x=False)
        self.controls = GridLayout(cols=1, spacing=dp(4), padding=dp(3), size_hint_y=None)
        self.controls.bind(minimum_height=self.controls.setter("height"))
        self.col_label, self.col_slider = self.add_slider("تعداد گل در عرض", 1, 8, 2, self.set_columns)
        self.row_label, self.row_slider = self.add_slider("تعداد ردیف در طول", 1, 24, 7, self.set_rows)
        self.scale_label, self.scale_slider = self.add_slider("اندازه نقش (%)", 20, 180, 100, self.set_scale)
        self.gap_label, self.gap_slider = self.add_slider("فاصله بین نقش‌ها (%)", 0, 65, 12, self.set_gap)
        self.rot_label, self.rot_slider = self.add_slider("چرخش نقش (درجه)", -180, 180, 0, self.set_rotation)

        toggles = GridLayout(cols=2, spacing=dp(4), size_hint_y=None, height=dp(88))
        self.stagger_btn = button("چیدمان یکی‌درمیان: روشن", on_release=self.toggle_stagger)
        self.random_btn = button("چرخش تصادفی: خاموش", on_release=self.toggle_random)
        toggles.add_widget(self.stagger_btn)
        toggles.add_widget(self.random_btn)
        toggles.add_widget(button("زمینه شفاف", on_release=self.transparent_bg))
        toggles.add_widget(button("تنظیمات اولیه", on_release=self.reset_controls))
        self.controls.add_widget(toggles)

        self.controls.add_widget(label("رنگ زمینه", size_hint_y=None, height=dp(26), color=(1,1,1,1)))
        colors = GridLayout(cols=4, spacing=dp(4), size_hint_y=None, height=dp(88))
        self.color_choices = [
            ("یخی",(238,235,239)), ("سفید",(255,255,255)), ("مشکی",(24,24,27)),
            ("موشی",(157,155,160)), ("یاسی",(216,202,231)),
            ("آبی خاکستری",(177,195,207)), ("صورتی یخی",(235,211,218)),
            ("طلایی یخی",(226,215,184))
        ]
        for name, rgb in self.color_choices:
            colors.add_widget(button(name, on_release=lambda inst, c=rgb, n=name: self.set_bg(c,n)))
        self.controls.add_widget(colors)

        self.controls.add_widget(label("اندازه خروجی", size_hint_y=None, height=dp(26), color=(1,1,1,1)))
        presets = GridLayout(cols=2, spacing=dp(4), size_hint_y=None, height=dp(88))
        presets.add_widget(button("۱۵۰ × ۳۰۰ سانتی‌متر", on_release=lambda *_: self.set_dimensions(2400,4800,"۱۵۰×۳۰۰")))
        presets.add_widget(button("۱۲۰ × ۴۰۰ سانتی‌متر", on_release=lambda *_: self.set_dimensions(1920,6400,"۱۲۰×۴۰۰")))
        presets.add_widget(button("۱۵۰ × ۴۰۰ سانتی‌متر", on_release=lambda *_: self.set_dimensions(2400,6400,"۱۵۰×۴۰۰")))
        presets.add_widget(button("خروجی استاندارد", on_release=lambda *_: self.set_dimensions(2400,3600,"استاندارد")))
        self.controls.add_widget(presets)
        self.controls.add_widget(label("خروجی‌ها در پوشه GaforiStudio ذخیره می‌شوند.",
                                       size_hint_y=None, height=dp(28),
                                       color=(.8,.85,1,1), font_size="12sp"))
        scroll.add_widget(self.controls)
        self.add_widget(scroll)

    def _update_bg(self, *_):
        self.bg_rect.pos, self.bg_rect.size = self.pos, self.size

    def add_slider(self, title, mn, mx, val, cb):
        lab = label(f"{title}: {int(val)}", size_hint_y=None, height=dp(24),
                    color=(1,1,1,1), font_size="12sp")
        sl = Slider(min=mn, max=mx, value=val, size_hint_y=None, height=dp(28))
        sl.bind(value=lambda _i, v: cb(int(v)))
        self.controls.add_widget(lab)
        self.controls.add_widget(sl)
        return lab, sl

    def set_columns(self,v):
        self.columns=max(1,int(v)); self.col_label.text=fa(f"تعداد گل در عرض: {self.columns}")
    def set_rows(self,v):
        self.rows=max(1,int(v)); self.row_label.text=fa(f"تعداد ردیف در طول: {self.rows}")
    def set_scale(self,v):
        self.scale_percent=int(v); self.scale_label.text=fa(f"اندازه نقش (%): {self.scale_percent}")
    def set_gap(self,v):
        self.gap_percent=int(v); self.gap_label.text=fa(f"فاصله بین نقش‌ها (%): {self.gap_percent}")
    def set_rotation(self,v):
        self.rotation=int(v); self.rot_label.text=fa(f"چرخش نقش (درجه): {self.rotation}")

    def toggle_stagger(self,*_):
        self.staggered=not self.staggered
        self.stagger_btn.text=fa("چیدمان یکی‌درمیان: روشن" if self.staggered else "چیدمان منظم: روشن")
    def toggle_random(self,*_):
        self.random_rotation=not self.random_rotation
        self.random_btn.text=fa("چرخش تصادفی: روشن" if self.random_rotation else "چرخش تصادفی: خاموش")
    def set_bg(self,rgb,name):
        self.bg_rgb=rgb; self.status.text=fa("رنگ زمینه انتخاب شد: "+name)
    def transparent_bg(self,*_):
        self.bg_rgb=None; self.status.text=fa("زمینه شفاف شد؛ پترن را دوباره بساز.")
    def set_dimensions(self,w,h,name):
        self.out_w,self.out_h=w,h
        self.status.text=fa(f"اندازه خروجی {name}: {w}×{h} پیکسل")

    def open_image(self,*_):
        chooser=FileChooserIconView(filters=["*.png","*.jpg","*.jpeg","*.webp"], path="/storage/emulated/0")
        box=BoxLayout(orientation="vertical",spacing=dp(5))
        box.add_widget(chooser)
        row=BoxLayout(size_hint_y=None,height=dp(46),spacing=dp(5))
        pop=Popup(title=fa("انتخاب عکس نقش"),content=box,size_hint=(.96,.9))
        def choose(*args):
            if not chooser.selection:
                self.status.text=fa("یک عکس انتخاب کن.")
                return
            try:
                self.source_image=Image.open(chooser.selection[0]).convert("RGBA")
                self.status.text=fa("عکس انتخاب شد: "+os.path.basename(chooser.selection[0]))
                self.show_image(self.source_image,"source_preview.png")
                pop.dismiss()
            except Exception as e:
                self.status.text=fa("خطا در بازکردن عکس: "+str(e)[:100])
        row.add_widget(button("انتخاب",on_release=choose))
        row.add_widget(button("بستن",on_release=pop.dismiss))
        box.add_widget(row)
        pop.open()

    def show_image(self,img,filename):
        path=os.path.join(get_app_dir(),filename)
        thumb=img.copy()
        thumb.thumbnail((1100,1300),Image.Resampling.LANCZOS)
        thumb.save(path)
        self.preview.source=path
        self.preview.reload()

    @staticmethod
    def composite_clipped(canvas, tile, x, y):
        # Correctly clip tiles that cross image edges.
        left, top = max(0,x), max(0,y)
        right, bottom = min(canvas.width,x+tile.width), min(canvas.height,y+tile.height)
        if right <= left or bottom <= top:
            return
        crop = tile.crop((left-x, top-y, right-x, bottom-y))
        canvas.alpha_composite(crop, (left, top))

    def generate_pattern(self,*_):
        if self.source_image is None:
            self.status.text=fa("اول عکس گل یا نقش را انتخاب کن.")
            return
        try:
            w,h=self.out_w,self.out_h
            if w*h>30_000_000:
                self.status.text=fa("اندازه خروجی بیش از حد بزرگ است.")
                return
            bg=(0,0,0,0) if self.bg_rgb is None else self.bg_rgb+(255,)
            canvas=Image.new("RGBA",(w,h),bg)
            cw,ch=w/self.columns,h/self.rows
            base_w=max(1,int(cw*(1-self.gap_percent/100)*self.scale_percent/100))
            base_h=max(1,int(ch*(1-self.gap_percent/100)*self.scale_percent/100))
            src=self.source_image.copy()
            src.thumbnail((base_w,base_h),Image.Resampling.LANCZOS)
            rng=random.Random()
            for r in range(self.rows):
                for c in range(self.columns):
                    x=int(c*cw+(cw-src.width)/2)
                    if self.staggered and r%2:
                        x+=int(cw/2)
                    y=int(r*ch+(ch-src.height)/2)
                    angle=self.rotation+(rng.randint(-35,35) if self.random_rotation else 0)
                    tile=src.rotate(angle,expand=True,resample=Image.Resampling.BICUBIC) if angle%360 else src
                    for xx in (x-w,x,x+w):
                        for yy in (y-h,y,y+h):
                            self.composite_clipped(canvas,tile,xx,yy)
            stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
            filename=os.path.join(get_app_dir(),f"Gafori_pattern_{stamp}.png")
            canvas.save(filename,"PNG",optimize=True)
            self.preview_image=filename
            self.show_image(canvas,"pattern_preview.png")
            self.status.text=fa(f"پترن ذخیره شد: {w}×{h} پیکسل | {filename}")
        except Exception as e:
            self.status.text=fa("خطا در ساخت پترن: "+str(e)[:140])

    def save_pattern(self,*_):
        if self.preview_image and os.path.isfile(self.preview_image):
            self.status.text=fa("فایل آماده است: "+self.preview_image)
        else:
            self.generate_pattern()

    def save_cutout(self,*_):
        if self.source_image is None:
            self.status.text=fa("اول عکس نقش را انتخاب کن.")
            return
        try:
            name=os.path.join(get_app_dir(),"Gafori_cutout_"+datetime.now().strftime("%Y%m%d_%H%M%S")+".png")
            self.source_image.save(name,"PNG")
            self.status.text=fa("نقش با حفظ شفافیت ذخیره شد: "+name)
        except Exception as e:
            self.status.text=fa("خطا در ذخیره نقش: "+str(e)[:100])

    def reset_controls(self,*_):
        self.col_slider.value=2
        self.row_slider.value=7
        self.scale_slider.value=100
        self.gap_slider.value=12
        self.rot_slider.value=0
        self.staggered=True
        self.random_rotation=False
        self.bg_rgb=(238,235,239)
        self.out_w,self.out_h=2400,3600
        self.stagger_btn.text=fa("چیدمان یکی‌درمیان: روشن")
        self.random_btn.text=fa("چرخش تصادفی: خاموش")
        self.status.text=fa("تنظیمات به حالت اولیه برگشت.")

class GaforiStudioApp(App):
    title="Gafori Studio"
    def build(self):
        Window.clearcolor=(.08,.09,.12,1)
        return PatternEditor()

if __name__=="__main__":
    GaforiStudioApp().run()
