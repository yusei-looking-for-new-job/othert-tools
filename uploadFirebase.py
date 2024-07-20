import json
import firebase_admin
from firebase_admin import credentials, storage
import os

# Firebase SDKの初期化
cred = credentials.Certificate(r'C:jsonのパス 念のためpublicでは非公開')
firebase_admin.initialize_app(cred, {
    'storageBucket': '念のためpublicでは非公開'
})

# アップロードする画像が入っているフォルダのパス
folder_path = r'C:\Users\DELL\dev\downloaded_images2'

# Cloud Storageのリファレンスを取得
bucket = storage.bucket()

# JSONファイルのパス
json_file_path = r'c:\Users\DELL\dev\spot.json'

# JSONファイルを読み込む
with open(json_file_path, 'r', encoding='utf-8') as file:
    data = json.load(file)

# フォルダ内の画像をループ処理
for filename in os.listdir(folder_path):
    if filename.endswith('.jpg') or filename.endswith('.png'):  # 画像ファイルの拡張子を適宜変更
        # 画像のファイルパス
        image_path = os.path.join(folder_path, filename)
        
        try:
            # アップロード先のパスを指定
            blob = bucket.blob(f'spotImages/{filename}')
            
            # 画像をアップロード
            blob.upload_from_filename(image_path)
            
            # アップロードされた画像のパスを取得
            image_url = blob.public_url
            
            print(f'Image uploaded successfully. URL: {image_url}')
            
            # JSONデータ内の一致する要素を探す
            # for spot in data['spots']:
            #     if spot['name'] == os.path.splitext(filename)[0]:
            #         spot['photo'] = image_url
            #         break
            
        except Exception as e:
            print(f'Error uploading {filename}: {str(e)}')

# 更新されたJSONデータを書き込む
with open(json_file_path, 'w', encoding='utf-8') as file:
    json.dump(data, file, ensure_ascii=False, indent=2)