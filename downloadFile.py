import json
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import re


##サイトの利用規約を読み、スクレイピング可能なサイトでのみ実施すること(自分への注意)！！！
##著作権フリーのサイトで実施すること！！！
##要素は適宜修正すること

# ファイル名から無効な文字を削除する関数
def sanitize_filename(filename):
    # ファイル名に使用できない文字を正規表現で指定
    invalid_chars = re.compile(r'[<>:"/\\|?*\x00-\x1F]')
    # 無効な文字を削除
    sanitized_filename = re.sub(invalid_chars, '', filename)
    # 連続する空白を単一の空白に置き換え
    sanitized_filename = re.sub(r'\s+', ' ', sanitized_filename)
    # 先頭と末尾の空白を削除
    sanitized_filename = sanitized_filename.strip()
    return sanitized_filename

# JSONデータを読み込む
with open("spot_v2.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# 画像を保存するディレクトリを作成
os.makedirs("images2", exist_ok=True)

# 各スポットの写真をダウンロード
for spot in data["spots"]:
    name = spot["name"]
    
    # 検索クエリを作成
    query = quote(name)
    

    #検索対象
    url = f"https://www.photo-ac.com/main/search?exclude_ai=on&personalized=&q={query}&sl=ja&pp=70&qid=&creator=&ngcreator=&nq=&srt=dlrank&orientation=all&sizesec=all&color=all&model_count=-1&age=all&mdlrlrsec=all&prprlrsec=all&type_search=phrase"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # 最初の画像のURLを取得
    preview_img = soup.find("img", id=lambda x: x and x.startswith("jq_thumb_"))
    
    # 画像が見つからない場合の要素を確認
    no_image_text = "該当する写真がありませんでした。ページ下部よりリクエストも受け付けております。"
    no_image_element = soup.find("p", class_="text-center ac-mt-2", text=no_image_text)
    
    if preview_img and not no_image_element:
        image_url = preview_img["src"]
        # 画像をダウンロード
        response = requests.get(image_url)
        
        # ファイル名をサニタイズ
        sanitized_name = sanitize_filename(name)
        
        # 画像を保存
        with open(f"images2/{sanitized_name}.jpg", "wb") as file:
            file.write(response.content)
        
        print(f"{name}の写真をダウンロードしました。")
    else:
        print(f"{name}の写真が見つかりませんでした。")