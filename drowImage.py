import os
from PIL import Image, ImageDraw, ImageFont

# 入力フォルダのパス
input_folder_path = r"C:\\Users\\DELL\\dev\\downloaded_images"

# 出力フォルダのパス
output_folder_path = r'C:\\Users\\DELL\\dev\\downloaded_images2'

# 出力フォルダが存在しない場合は作成する
os.makedirs(output_folder_path, exist_ok=True)

# 追加するテキスト
text = "写真にテキストをいれる"

# フォントの設定 (UTF-8対応の太字フォントを指定)
font_path = "C:\\Windows\\Fonts\\msgothic.ttc"

# 入力フォルダ内の画像ファイルを処理
for filename in os.listdir(input_folder_path):
    if filename.endswith(".jpg") or filename.endswith(".png"):
        # 画像を開く
        image_path = os.path.join(input_folder_path, filename)
        image = Image.open(image_path)
        
        # 画像のサイズを取得
        width, height = image.size
        
        # 画像のサイズに応じてフォントサイズを設定
        if width <= 400:
            font_size = 5
        else:
            font_size = 9
        
        # 太字フォントを作成
        font = ImageFont.truetype(font_path, font_size)
        font_bold = ImageFont.truetype(font_path, font_size, index=1)
        
        # 文字を描画するためのDrawオブジェクトを作成
        draw = ImageDraw.Draw(image)
        
        # テキストのサイズを取得
        text_bbox = draw.textbbox((0, 0), text, font=font_bold)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # テキストの位置を計算
        x = width - text_width - 23
        y = 10
        
        # 白色で太字の文字を描画
        draw.text((x, y), text, font=font_bold, fill=(255, 255, 255))
        
        # 画像を保存
        output_path = os.path.join(output_folder_path, filename)
        image.save(output_path)