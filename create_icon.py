from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    # Create a 256x256 image with a blue background
    size = (256, 256)
    bg_color = "#1976D2" # Blue
    text_color = "white"
    
    img = Image.new('RGBA', size, bg_color)
    draw = ImageDraw.Draw(img)
    
    # Draw a circle container
    margin = 20
    draw.ellipse([margin, margin, size[0]-margin, size[1]-margin], outline="white", width=10)
    
    # Draw text "ÖTP"
    try:
        # Try to load a font, otherwise default
        font = ImageFont.truetype("arial.ttf", 80)
    except:
        font = ImageFont.load_default()
        
    text = "ÖTP"
    
    # Calculate text size using textbbox (newer Pillow)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    text_width = right - left
    text_height = bottom - top
    
    position = ((size[0] - text_width) / 2, (size[1] - text_height) / 2 - 10)
    
    draw.text(position, text, fill=text_color, font=font)
    
    # Save
    assets_dir = r"d:\Archive\Yazilim\Ogrenci_Takip_Pro\assets"
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
        
    img.save(os.path.join(assets_dir, "icon.png"))
    print(f"Icon created at {os.path.join(assets_dir, 'icon.png')}")

if __name__ == "__main__":
    create_icon()
