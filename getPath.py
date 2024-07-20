import firebase_admin
from firebase_admin import credentials, storage
import os
import json

# Firebase SDKの初期化
cred = credentials.Certificate(r'C:念のためpublicでは非公開')
firebase_admin.initialize_app(cred, {
    'storageBucket': '念のためpublicでは非公開'
})

# Cloud Storageのリファレンスを取得
bucket = storage.bucket()

# JSONファイルのパス
json_file_path = r'c:\Users\DELL\dev\spot_dl.json'

# JSONファイルを読み込む
with open(json_file_path, 'r', encoding='utf-8') as file:
    data = json.load(file)

# JSONデータ内の各要素に対して処理を行う
for spot in data['spots']:
    # 画像のファイル名を取得
    filename = f"{spot['name']}.jpg"  # 拡張子を適宜変更
    
    try:
        # Cloud Storage内の画像のパスを指定
        blob = bucket.blob(f'spotImages/{filename}')
        
        # 画像が存在するかどうかを確認
        if blob.exists():
            # Cloud Storage内の画像のパスを取得
            image_path = f"spotImages/{filename}"
            
            # JSONデータ内の'photo'を更新
            spot['photo'] = image_path
            print(f"Image path retrieved for {filename}: {image_path}")
        else:
            # 画像が存在しない場合は、'photo'フィールドを空の文字列に設定
            spot['photo'] = ""
            print(f"Image not found for {filename}. Setting 'photo' field to empty string.")
    except Exception as e:
        print(f"Error checking image existence for {filename}: {str(e)}")

# 更新されたJSONデータを書き込む
with open(json_file_path, 'w', encoding='utf-8') as file:
    json.dump(data, file, ensure_ascii=False, indent=2)