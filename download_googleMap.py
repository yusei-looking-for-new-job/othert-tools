import json
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

#規約的に大丈夫か調べてから
#今のところグレー

# JSONファイルを読み込む
with open("spot_dl.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# 画像保存用のディレクトリを作成
if not os.path.exists("downloaded_images"):
    os.makedirs("downloaded_images")

# WebDriverを起動
driver = webdriver.Chrome()

# 画像をダウンロードする関数
def download_image(name):
    # GoogleマップのURL
    url = f"https://www.google.com/maps/search/{name}"
    
    # GoogleマップのURLを開く
    driver.get(url)
    
    time.sleep(2)  # ページの読み込みが完了するまで待機
    
    try:
        # 画像要素を取得
        image_element = driver.find_element(By.CSS_SELECTOR, "img[src^='https://lh5.googleusercontent.com']")
        image_url = image_element.get_attribute("src")
    except:
        print(f"No image found for {name}")
        return
    
    # 画像をダウンロード
    driver.get(image_url)
    
    # 画像を保存
    image_path = f"downloaded_images/{name}.jpg"
    with open(image_path, "wb") as file:
        file.write(driver.find_element(By.TAG_NAME, "img").screenshot_as_png)

# JSONデータを処理
for spot in data["spots"]:
    if spot["photo"] == "":
        name = spot["name"]
        download_image(name)

# WebDriverを終了
driver.quit()