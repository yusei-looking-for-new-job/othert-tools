import requests
from bs4 import BeautifulSoup
import json

#サイトの利用規約を読み、スクレイピング可能なサイトでのみ実施すること！！！
#要素などは適宜修正すること


# スクレイピング対象のURL
url = "対象のURL"

# リクエストを送信し、レスポンスを取得
response = requests.get(url)

# BeautifulSoupオブジェクトを作成
soup = BeautifulSoup(response.text, 'html.parser')

# JSONファイルのパスを指定
json_file_path = "C:\\Users\\DELL\\dev\\spot.json"

# JSONファイルを読み込む
with open(json_file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# スポット情報を格納するためのリストを取得
spots = data.get('spots', [])

# 最後のspotIdを取得し、次のspotIdを計算
last_spot_id = int(spots[-1]['spotId']) if spots else 0

# 各スポットの情報を取得
for i, spot in enumerate(soup.find_all('div', class_='spot-list'), start=last_spot_id+1):
    # スポット情報を格納するための空の辞書を作成
    spot_info = {}
    spot_info['spotId'] = str(i)
    spot_info['address'] = spot.find('span', class_='適宜変更').text
    spot_info['name'] = spot.find('div', class_='適宜変更').text
    spot_info['description'] = spot.find('p', class_='適宜変更').text
    spot_info['photo'] = spot.find('img', class_='適宜変更')['src']
    spot_info['favorite'] = spot.find('div', class_='適宜変更') is not None
    spot_info['tags'] = [tag.text for tag in spot.find_all('span', class_='適宜変更')]
    spot_info['latitude'], spot_info['longitude'] = map(float, spot['適宜変更'].split(','))
    # スポット情報をリストに追加
    spots.append(spot_info)

# JSON形式で出力
data['spots'] = spots

# JSONファイルに書き込む
with open(json_file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
