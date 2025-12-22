import os
import sys
import glob
import random
import time
import requests

# --- 設定 ---
PHOTOS_DIR = "photos"
IG_USER_ID = os.environ.get("IG_USER_ID")
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN")
# GitHub Actionsが自動で設定する環境変数を使う
GITHUB_REPO = os.environ.get("GITHUB_REPOSITORY") # "User/Repo" の形式
BRANCH_NAME = "main" # もしブランチ名が master ならここを変える
API_VER = "v18.0"

def get_raw_url(image_path):
    """
    GitHubのRaw画像のURLを生成する
    例: https://raw.githubusercontent.com/UmikaiBun/Repo/main/photos/001.jpg
    """
    # Windows/Linuxのパス区切り文字の違いを吸収してスラッシュにする
    clean_path = image_path.replace(os.sep, '/')
    
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{BRANCH_NAME}/{clean_path}"
    print(f"Generated Raw URL: {url}")
    return url

def post_to_instagram(image_url, caption):
    """Instagram Graph APIを叩いて投稿する"""
    
    # 1. コンテナ作成
    create_url = f"https://graph.facebook.com/{API_VER}/{IG_USER_ID}/media"
    payload = {
        'image_url': image_url,
        'caption': caption,
        'access_token': IG_ACCESS_TOKEN
    }
    
    print("Creating Media Container...")
    res = requests.post(create_url, data=payload)
    
    # エラーハンドリング（画像サイズや形式で怒られることがある）
    if res.status_code != 200:
        print(f"Container Creation Failed: {res.text}")
        return False
    
    creation_id = res.json().get('id')
    print(f"Container ID: {creation_id}")

    # APIの処理待ち（重要）
    time.sleep(10) 

    # 2. 投稿公開 (Publish)
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
    # 1. 画像の選定
    files = glob.glob(os.path.join(PHOTOS_DIR, "*.[jJ][pP][gG]")) + \
            glob.glob(os.path.join(PHOTOS_DIR, "*.[pP][nN][gG]")) + \
            glob.glob(os.path.join(PHOTOS_DIR, "*.[jJ][pP][eE][gG]"))
    
    if not files:
        print("No photos found. Exiting.")
        sys.exit(0)

    target_image = random.choice(files)
    print(f"Selected Image: {target_image}")

    filename = os.path.basename(target_image)
    caption = f"{filename}\n.\n.\n#archive #streetphotography #texture"

    # 2. GitHubのRaw URLを取得 (Imgur不要！)
    image_url = get_raw_url(target_image)

    # 3. Instagramへ投稿
    success = post_to_instagram(image_url, caption)

    # 4. 成功したらローカルファイルを削除し、Gitで反映させるための終了コード
    if success:
        print(f"Deleting local file: {target_image}")
        os.remove(target_image)
    else:
        print("Failed to post. File kept.")
        sys.exit(1)

if __name__ == "__main__":
    main()

