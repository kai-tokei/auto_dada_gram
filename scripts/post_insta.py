import os
import sys
import glob
import random
import time
import requests
from openai import OpenAI

# --- 設定 ---
PHOTOS_DIR = "photos"
IG_USER_ID = os.environ.get("IG_USER_ID")
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN")
GITHUB_REPO = os.environ.get("GITHUB_REPOSITORY")
BRANCH_NAME = "main"
API_VER = "v18.0"

# OpenAIクライアント初期化
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def get_raw_url(image_path):
    """GitHubのRaw画像のURLを生成する"""
    clean_path = image_path.replace(os.sep, '/')
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{BRANCH_NAME}/{clean_path}"
    return url

def generate_caption_by_ai(image_url):
    print("Asking OpenAI to describe the image...")
    
    system_prompt = """
    送られてきた写真に、Instagramのキャプションを生成してください。
    
    # 制約条件
    - トーン：静的、客観的、淡白に。絵文字は使わない。
    - 視点：色彩、光、構造、テクスチャ、都市などに注目する。具体的な広告の記号や地名を積極的に記述せよ。
    - 言語：日本語。
    - 構成：
      1行目：短いタイトル一文。
      2行目：その英語訳
      最後：関連するハッシュタグを5個（英語と日本語を混ぜて）。
    
    # 悪い例
    「きれいな空ですね！」「楽しそう！」（感情的すぎるのはNG）
    
    # 良い例
    「コンクリート」
    「電柱」
    「青山一丁目」
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "text", "text": "Generate a caption for this image."},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]}
            ],
            max_tokens=300
        )
        caption = response.choices[0].message.content
        print(f"Generated Caption:\n{caption}")
        return caption
    except Exception as e:
        print(f"OpenAI Error: {e}")
        # エラー時は無難なデフォルトキャプションを返す
        return "Texture of the city.\n.\n#archive #streetphotography #snapshot #japanphotography"

def post_to_instagram(image_url, caption):
    """Instagram Graph APIを叩いて投稿する"""
    create_url = f"https://graph.facebook.com/{API_VER}/{IG_USER_ID}/media"
    payload = {
        'image_url': image_url,
        'caption': caption,
        'access_token': IG_ACCESS_TOKEN
    }
    
    print("Creating Media Container...")
    res = requests.post(create_url, data=payload)
    
    if res.status_code != 200:
        print(f"Container Creation Failed: {res.text}")
        return False
    
    creation_id = res.json().get('id')
    time.sleep(10) # 処理待ち

    publish_url = f"https://graph.facebook.com/{API_VER}/{IG_USER_ID}/media_publish"
    pub_payload = {
        'creation_id': creation_id,
        'access_token': IG_ACCESS_TOKEN
    }
    
    print("Publishing Media...")
    pub_res = requests.post(publish_url, data=pub_payload)
    
    if pub_res.status_code == 200:
        print(f"Post Success! ID: {pub_res.json().get('id')}")
        return True
    else:
        print(f"Publish Failed: {pub_res.text}")
        return False

def main():
    # 画像選定
    files = glob.glob(os.path.join(PHOTOS_DIR, "*.[jJ][pP][gG]")) + \
            glob.glob(os.path.join(PHOTOS_DIR, "*.[pP][nN][gG]")) + \
            glob.glob(os.path.join(PHOTOS_DIR, "*.[jJ][pP][eE][gG]"))
    
    if not files:
        sys.exit(0)

    target_image = random.choice(files)
    print(f"Selected Image: {target_image}")

    # 1. 画像URL生成
    image_url = get_raw_url(target_image)

    # 2. AIによるキャプション生成 
    caption = generate_caption_by_ai(image_url)

    # 3. 投稿
    success = post_to_instagram(image_url, caption)

    # 4. 削除
    if success:
        print(f"Deleting local file: {target_image}")
        os.remove(target_image)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()

