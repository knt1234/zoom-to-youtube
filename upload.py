#!/usr/bin/env python3
"""
Zoom録画 → YouTube 自動アップロードツール

Usage:
  python3 upload.py config   - 設定ウィザードを起動（初回）
  python3 upload.py setup    - YouTube/Sheets の認証セットアップ
  python3 upload.py sheet    - スプレッドシートにタグのドロップダウンを追加
  python3 upload.py          - アップロード実行
"""

import os
import sys
import json
import pickle
import tempfile
import re
import requests
from datetime import datetime, timezone, timedelta
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

BASE_DIR = os.path.expanduser("~/Documents/movie-upload")
CLIENT_SECRETS = os.path.join(BASE_DIR, "client_secrets.json")
TOKENS_DIR = os.path.join(BASE_DIR, "tokens")
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube"]
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


# ── 設定の読み込み ────────────────────────────────────────────

def load_config():
    if not os.path.exists(CONFIG_PATH):
        print("config.json が見つかりません。先に設定ウィザードを実行してください：")
        print("  python3 upload.py config")
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# ── 設定ウィザード ────────────────────────────────────────────

def run_config_wizard():
    print("=== 設定ウィザード ===\n")

    # スプレッドシートURL
    while True:
        url = input("GoogleスプレッドシートのURLを入力してください:\n> ").strip()
        m = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
        gid_m = re.search(r"gid=(\d+)", url)
        if m:
            spreadsheet_id = m.group(1)
            sheet_id = int(gid_m.group(1)) if gid_m else 0
            break
        print("URLの形式が正しくありません。再入力してください。\n")

    print(f"  スプレッドシートID: {spreadsheet_id}")
    print(f"  シートID: {sheet_id}\n")

    # 最大アップロード件数
    max_uploads = input("1回の実行で最大何件アップロードしますか？（デフォルト: 5）:\n> ").strip()
    max_uploads = int(max_uploads) if max_uploads.isdigit() else 5

    # 列の設定
    print("\n--- 列の設定 ---")
    print("スプレッドシートの列番号を入力してください（A=1, B=2, C=3 ...）")

    def ask_col(label, default):
        val = input(f"  {label}列 (デフォルト: {default}): ").strip()
        return (int(val) - 1) if val.isdigit() else (default - 1)

    columns = {
        "download_url":   ask_col("ダウンロードリンク", 5),
        "youtube_link":   ask_col("YouTubeリンク（自動入力）", 6),
        "date_for_title": ask_col("動画タイトル用の日付", 8),
        "title":          ask_col("動画タイトル", 9),
        "check":          ask_col("チェック（自動入力）", 10),
        "tag":            ask_col("タグ（アップロード先）", 11),
        "uploaded_at":    ask_col("アップロード日時（自動入力）", 12),
    }

    # チャンネル設定
    print("\n--- YouTubeチャンネルの設定 ---")
    num = input("アップロード先のYouTubeチャンネル数を入力してください:\n> ").strip()
    num = int(num) if num.isdigit() else 1

    channels = []
    for i in range(num):
        print(f"\nチャンネル {i + 1} / {num}")
        tag = input("  タグ名（例: ESL, NCA, 自分用）: ").strip()
        name = input("  チャンネルの説明（例: ESL事務局 @ESL-jimukyoku）: ").strip()
        token_file = f"token_{tag.lower().replace(' ', '_')}.pkl"
        channels.append({"tag": tag, "name": name, "token_file": token_file})

    cfg = {
        "spreadsheet_id": spreadsheet_id,
        "sheet_id": sheet_id,
        "max_uploads_per_run": max_uploads,
        "columns": columns,
        "channels": channels,
    }

    save_config(cfg)
    print("\n✓ config.json を保存しました。")
    print("次のステップ: python3 upload.py setup\n")


# ── 認証 ────────────────────────────────────────────────────

def get_credentials(token_file, scopes):
    creds = None
    token_path = os.path.join(TOKENS_DIR, token_file)

    if os.path.exists(token_path):
        with open(token_path, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS, scopes)
            creds = flow.run_local_server(port=0)

        with open(token_path, "wb") as f:
            pickle.dump(creds, f)

    return creds


def setup_auth(cfg):
    os.makedirs(TOKENS_DIR, exist_ok=True)

    print("=== 認証セットアップ ===\n")
    print("ブラウザが開いたら、指示されたアカウント/チャンネルを選択してください。\n")

    print("【1】Google Sheets 認証")
    print("  → スプレッドシートを管理しているGoogleアカウントでログインしてください")
    input("  Enterキーを押してブラウザを開きます...")
    get_credentials("token_sheets.pkl", SHEETS_SCOPES)
    print("  ✓ 完了\n")

    for i, ch in enumerate(cfg["channels"], 2):
        print(f"【{i}】{ch['name']} の認証")
        print(f"  → {ch['name']} のアカウントでログインしてください")
        input("  Enterキーを押してブラウザを開きます...")
        get_credentials(ch["token_file"], YOUTUBE_SCOPES)
        print(f"  ✓ 完了\n")

    print("=== 全認証完了 ===")
    print("次回から  python3 upload.py  でアップロードできます。\n")


# ── スプレッドシートのドロップダウン設定 ────────────────────

def setup_sheet(cfg):
    sheets_creds = get_credentials("token_sheets.pkl", SHEETS_SCOPES)
    service = build("sheets", "v4", credentials=sheets_creds)

    tag_col = cfg["columns"]["tag"]
    tag_col_letter = chr(ord("A") + tag_col)

    tags = [ch["tag"] for ch in cfg["channels"]]

    service.spreadsheets().values().update(
        spreadsheetId=cfg["spreadsheet_id"],
        range=f"{tag_col_letter}1",
        valueInputOption="RAW",
        body={"values": [["タグ"]]},
    ).execute()

    requests_body = [
        {
            "setDataValidation": {
                "range": {
                    "sheetId": cfg["sheet_id"],
                    "startRowIndex": 1,
                    "endRowIndex": 1000,
                    "startColumnIndex": tag_col,
                    "endColumnIndex": tag_col + 1,
                },
                "rule": {
                    "condition": {
                        "type": "ONE_OF_LIST",
                        "values": [{"userEnteredValue": t} for t in tags],
                    },
                    "showCustomUi": True,
                    "strict": True,
                },
            }
        }
    ]

    service.spreadsheets().batchUpdate(
        spreadsheetId=cfg["spreadsheet_id"],
        body={"requests": requests_body},
    ).execute()

    print(f"✓ タグ列にドロップダウンを追加しました（{' / '.join(tags)}）")


# ── 動画のダウンロード・アップロード ────────────────────────

def download_video(url, output_path):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, stream=True, headers=headers, allow_redirects=True)
    response.raise_for_status()

    total = int(response.headers.get("content-length", 0))
    downloaded = 0

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = int(downloaded / total * 100)
                print(f"\r  ダウンロード中... {pct}%", end="", flush=True)

    print("\r  ダウンロード完了              ")


def upload_to_youtube(creds, title, video_path):
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {"title": title, "description": "", "categoryId": "22"},
        "status": {"privacyStatus": "unlisted"},
    }

    media = MediaFileUpload(
        video_path, mimetype="video/*", chunksize=10 * 1024 * 1024, resumable=True
    )
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"\r  アップロード中... {pct}%", end="", flush=True)

    print("\r  アップロード完了              ")
    return f"https://www.youtube.com/watch?v={response['id']}"


def extract_video_id(url):
    if "watch?v=" in url:
        return url.split("watch?v=")[1].split("&")[0]
    return None


def get_video_processing_status(creds, video_id):
    try:
        youtube = build("youtube", "v3", credentials=creds)
        result = youtube.videos().list(part="processingDetails", id=video_id).execute()
        if not result.get("items"):
            return "not_found"
        processing = result["items"][0].get("processingDetails", {})
        return processing.get("processingStatus", "unknown")
    except Exception:
        return "unknown"


def delete_video(creds, video_id):
    youtube = build("youtube", "v3", credentials=creds)
    youtube.videos().delete(id=video_id).execute()


def do_upload(sheets_service, cfg, row_index, date_h, title_i, tag, download_url, token_file):
    cols = cfg["columns"]
    youtube_creds = get_credentials(token_file, YOUTUBE_SCOPES)

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        download_video(download_url, tmp_path)

        video_title = f"{date_h} {title_i}".strip()
        yt_url = upload_to_youtube(youtube_creds, video_title, tmp_path)
        print(f"  URL: {yt_url}")

        now_str = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M")
        yt_col  = chr(ord("A") + cols["youtube_link"])
        chk_col = chr(ord("A") + cols["check"])
        upl_col = chr(ord("A") + cols["uploaded_at"])

        for col, val in [(yt_col, yt_url), (chk_col, "済"), (upl_col, now_str)]:
            sheets_service.spreadsheets().values().update(
                spreadsheetId=cfg["spreadsheet_id"],
                range=f"{col}{row_index}",
                valueInputOption="RAW",
                body={"values": [[val]]},
            ).execute()

        print("  スプレッドシート更新完了")
        return True

    except Exception as e:
        print(f"  エラー: {e}")
        return False

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ── メイン処理 ───────────────────────────────────────────────

def main():
    cfg = load_config()
    cols = cfg["columns"]
    max_uploads = cfg.get("max_uploads_per_run", 5)
    tag_to_channel = {ch["tag"]: ch for ch in cfg["channels"]}

    if not os.path.exists(os.path.join(TOKENS_DIR, "token_sheets.pkl")):
        print("認証が未設定です。先に以下を実行してください：")
        print("  python3 upload.py setup")
        sys.exit(1)

    sheets_creds = get_credentials("token_sheets.pkl", SHEETS_SCOPES)
    sheets_service = build("sheets", "v4", credentials=sheets_creds)

    # 読み込む最終列をuploaded_atの列に合わせる
    last_col = chr(ord("A") + cols["uploaded_at"])
    print("スプレッドシートを読み込み中...")
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=cfg["spreadsheet_id"],
        range=f"A:{last_col}",
    ).execute()

    rows = result.get("values", [])
    upload_count = 0
    now = datetime.now(timezone(timedelta(hours=9)))
    total_cols = cols["uploaded_at"] + 1

    for i, row in enumerate(rows[1:], 2):
        if upload_count >= max_uploads:
            print(f"\n上限（{max_uploads}件）に達したため終了。残りは次回実行時に処理されます。")
            break

        while len(row) < total_cols:
            row.append("")

        download_url  = row[cols["download_url"]]
        youtube_link  = row[cols["youtube_link"]]
        date_h        = row[cols["date_for_title"]]
        title_i       = row[cols["title"]]
        check         = row[cols["check"]]
        tag           = row[cols["tag"]]
        uploaded_at   = row[cols["uploaded_at"]]

        if not title_i or not download_url:
            continue
        if not tag or tag not in tag_to_channel:
            continue

        ch = tag_to_channel[tag]

        # アップロード済み → 24時間経っても処理中なら再アップロード
        if check == "済" and youtube_link and uploaded_at:
            try:
                upload_time = datetime.strptime(uploaded_at, "%Y-%m-%d %H:%M").replace(
                    tzinfo=timezone(timedelta(hours=9))
                )
                if (now - upload_time).total_seconds() / 3600 < 24:
                    continue

                video_id = extract_video_id(youtube_link)
                if not video_id:
                    continue

                yt_creds = get_credentials(ch["token_file"], YOUTUBE_SCOPES)
                if get_video_processing_status(yt_creds, video_id) != "processing":
                    continue

                print(f"\n[行{i}] {date_h} {title_i} → 24時間以上処理中のため再アップロード")
                try:
                    delete_video(yt_creds, video_id)
                except Exception as e:
                    print(f"  削除エラー（続行）: {e}")

                yt_col  = chr(ord("A") + cols["youtube_link"])
                chk_col = chr(ord("A") + cols["check"])
                for col in [yt_col, chk_col]:
                    sheets_service.spreadsheets().values().update(
                        spreadsheetId=cfg["spreadsheet_id"],
                        range=f"{col}{i}",
                        valueInputOption="RAW",
                        body={"values": [[""]]},
                    ).execute()

                if do_upload(sheets_service, cfg, i, date_h, title_i, tag, download_url, ch["token_file"]):
                    upload_count += 1
            except Exception as e:
                print(f"  再試行チェックエラー: {e}")
            continue

        if check == "済":
            continue

        print(f"\n[行{i}] {date_h} {title_i}")
        print(f"  アップロード先: {ch['name']}")

        if do_upload(sheets_service, cfg, i, date_h, title_i, tag, download_url, ch["token_file"]):
            upload_count += 1

    print(f"\n=== 完了: {upload_count}件アップロード ===")


# ── エントリーポイント ────────────────────────────────────────

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""

    if cmd == "config":
        run_config_wizard()
    elif cmd == "setup":
        setup_auth(load_config())
    elif cmd == "sheet":
        setup_sheet(load_config())
    else:
        main()
