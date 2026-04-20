#!/usr/bin/env python3
"""
Zoom録画 → YouTube 自動アップロードツール

Usage:
  python3 upload.py config      - 設定ウィザードを起動（初回）
  python3 upload.py setup       - YouTube/Sheets の認証セットアップ
  python3 upload.py sheet       - スプレッドシートにタグのドロップダウンを追加
  python3 upload.py zoom-setup  - Zoom API設定（Server-to-Server OAuth）
  python3 upload.py sync        - Zoom録画をスプレッドシートに自動転記
  python3 upload.py             - アップロード実行
"""

import os
import sys
import json
import pickle
import tempfile
import re
import base64
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


# ── スプレッドシート ユーティリティ ─────────────────────────

def get_sheet_name(sheets_service, spreadsheet_id, sheet_id):
    """sheet_id（数値）からシート名を取得"""
    meta = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for sheet in meta.get("sheets", []):
        if sheet["properties"]["sheetId"] == sheet_id:
            return sheet["properties"]["title"]
    raise ValueError(f"シートID {sheet_id} が見つかりません")


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


# ── Zoom API ────────────────────────────────────────────────

def setup_zoom(cfg):
    print("=== Zoom API 設定 ===\n")
    print("Zoom Marketplace で Server-to-Server OAuth アプリを作成し、")
    print("以下の情報を入力してください。\n")

    account_id    = input("Account ID    : ").strip()
    client_id     = input("Client ID     : ").strip()
    client_secret = input("Client Secret : ").strip()
    days = input("何日前まで遡って録画を取得しますか？（デフォルト: 30）: ").strip()
    days = int(days) if days.isdigit() else 30

    cfg["zoom"] = {
        "account_id":    account_id,
        "client_id":     client_id,
        "client_secret": client_secret,
        "sync_days":     days,
    }
    save_config(cfg)
    print("\n✓ Zoom設定を保存しました。")
    print("次のステップ: python3 upload.py sync\n")


def get_zoom_token(zoom_cfg):
    credentials = base64.b64encode(
        f"{zoom_cfg['client_id']}:{zoom_cfg['client_secret']}".encode()
    ).decode()
    resp = requests.post(
        "https://zoom.us/oauth/token",
        params={"grant_type": "account_credentials", "account_id": zoom_cfg["account_id"]},
        headers={"Authorization": f"Basic {credentials}"},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def fetch_zoom_recordings(access_token, from_date, to_date):
    resp = requests.get(
        "https://api.zoom.us/v2/users/me/recordings",
        params={"from": from_date, "to": to_date, "page_size": 300},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    resp.raise_for_status()
    return resp.json()


def pick_mp4_file(recording_files):
    """優先順位: shared_screen_with_speaker_view > active_speaker > gallery_view > 任意MP4"""
    for priority in ["shared_screen_with_speaker_view", "active_speaker", "gallery_view"]:
        for f in recording_files:
            if f.get("file_type") == "MP4" and f.get("recording_type") == priority:
                return f
    for f in recording_files:
        if f.get("file_type") == "MP4":
            return f
    return None


def sync_zoom(cfg):
    if "zoom" not in cfg:
        print("Zoom設定が未設定です。先に以下を実行してください：")
        print("  python3 upload.py zoom-setup")
        sys.exit(1)

    zoom_cfg = cfg["zoom"]
    print("Zoom アクセストークンを取得中...")
    access_token = get_zoom_token(zoom_cfg)

    days = zoom_cfg.get("sync_days", 30)
    to_date   = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    print(f"{from_date} 〜 {to_date} の録画を取得中...")

    data = fetch_zoom_recordings(access_token, from_date, to_date)
    meetings = data.get("meetings", [])
    if not meetings:
        print("録画が見つかりませんでした。")
        return

    print(f"{len(meetings)}件のミーティングが見つかりました。\n")

    sheets_creds   = get_credentials("token_sheets.pkl", SHEETS_SCOPES)
    sheets_service = build("sheets", "v4", credentials=sheets_creds)
    sheet_name     = get_sheet_name(sheets_service, cfg["spreadsheet_id"], cfg["sheet_id"])

    cols     = cfg["columns"]
    last_col = chr(ord("A") + cols["uploaded_at"])
    result   = sheets_service.spreadsheets().values().get(
        spreadsheetId=cfg["spreadsheet_id"],
        range=f"'{sheet_name}'!A:{last_col}",
    ).execute()
    existing_rows = result.get("values", [])

    # 既存のダウンロードURL（ベース部分）を収集して重複チェック
    existing_urls = set()
    for row in existing_rows[1:]:
        if len(row) > cols["download_url"] and row[cols["download_url"]]:
            existing_urls.add(row[cols["download_url"]].split("?")[0])

    share_url_col = cols["download_url"] - 1  # D列（共有リンク）
    num_cols      = cols["uploaded_at"] + 1
    added         = 0

    for meeting in meetings:
        video_file = pick_mp4_file(meeting.get("recording_files", []))
        if not video_file:
            continue

        download_url = video_file.get("download_url", "")
        if not download_url or download_url.split("?")[0] in existing_urls:
            continue

        start_time     = meeting.get("start_time", "")
        date_str       = start_time[:10] if start_time else ""
        try:
            date_fmt = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y/%m/%d")
        except ValueError:
            date_fmt = date_str

        topic     = meeting.get("topic", "")
        share_url = meeting.get("share_url", "")

        new_row = [""] * num_cols
        new_row[0]                      = date_fmt       # A: 日付
        new_row[share_url_col]          = share_url      # D: 共有リンク
        new_row[cols["download_url"]]   = download_url   # E: ダウンロードリンク（トークンなし）
        new_row[cols["date_for_title"]] = date_fmt       # H: 日付（タイトル用）
        new_row[cols["title"]]          = topic          # I: 動画タイトル

        sheets_service.spreadsheets().values().append(
            spreadsheetId=cfg["spreadsheet_id"],
            range=f"'{sheet_name}'!A:A",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [new_row]},
        ).execute()

        print(f"  追加: {date_fmt} {topic}")
        existing_urls.add(download_url.split("?")[0])
        added += 1

    print(f"\n✓ {added}件を追加しました。")
    if added > 0:
        print("K列にタグを入力してから  python3 upload.py  でアップロードできます。")


# ── 動画のダウンロード・アップロード ────────────────────────

def download_video(url, output_path, auth_headers=None):
    headers = {"User-Agent": "Mozilla/5.0"}
    if auth_headers:
        headers.update(auth_headers)
    response = requests.get(url, stream=True, headers=headers, allow_redirects=True, timeout=30)
    response.raise_for_status()

    content_type = response.headers.get("content-type", "")
    if "text/html" in content_type:
        raise ValueError(f"動画ではなくHTMLが返されました（認証エラーの可能性）: {url}")

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

    file_size = os.path.getsize(output_path)
    if file_size < 1024 * 100:  # 100KB未満は異常
        raise ValueError(f"ダウンロードしたファイルが小さすぎます（{file_size}バイト）。URLを確認してください。")


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


def do_upload(sheets_service, cfg, row_index, date_h, title_i, tag, download_url, token_file, auth_headers=None, sheet_name=None):
    cols = cfg["columns"]
    youtube_creds = get_credentials(token_file, YOUTUBE_SCOPES)

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        download_video(download_url, tmp_path, auth_headers=auth_headers)

        video_title = f"{date_h} {title_i}".strip()
        yt_url = upload_to_youtube(youtube_creds, video_title, tmp_path)
        print(f"  URL: {yt_url}")

        now_str = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M")
        yt_col  = chr(ord("A") + cols["youtube_link"])
        chk_col = chr(ord("A") + cols["check"])
        upl_col = chr(ord("A") + cols["uploaded_at"])

        prefix = f"'{sheet_name}'!" if sheet_name else ""
        for col, val in [(yt_col, yt_url), (chk_col, "済"), (upl_col, now_str)]:
            sheets_service.spreadsheets().values().update(
                spreadsheetId=cfg["spreadsheet_id"],
                range=f"{prefix}{col}{row_index}",
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
    sheet_name = get_sheet_name(sheets_service, cfg["spreadsheet_id"], cfg["sheet_id"])

    # 読み込む最終列をuploaded_atの列に合わせる
    last_col = chr(ord("A") + cols["uploaded_at"])
    print("スプレッドシートを読み込み中...")
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=cfg["spreadsheet_id"],
        range=f"'{sheet_name}'!A:{last_col}",
    ).execute()

    rows = result.get("values", [])
    upload_count = 0
    now = datetime.now(timezone(timedelta(hours=9)))
    total_cols = cols["uploaded_at"] + 1
    zoom_token = None  # Zoom URLのダウンロード時に必要なら遅延取得

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
            if title_i or download_url:  # どちらか片方だけある行は報告
                print(f"  [行{i}] スキップ: タイトル={repr(title_i)} / URL={repr(download_url[:40] if download_url else '')}")
            continue
        if not tag or tag not in tag_to_channel:
            print(f"  [行{i}] スキップ: タグ={repr(tag)}（未設定または不一致）")
            continue

        ch = tag_to_channel[tag]

        # Zoom URLはダウンロード時に認証が必要なためトークンを取得（1回だけ）
        auth_headers = None
        if "zoom.us" in download_url and "zoom" in cfg:
            if zoom_token is None:
                print("Zoom アクセストークンを取得中...")
                zoom_token = get_zoom_token(cfg["zoom"])
            auth_headers = {"Authorization": f"Bearer {zoom_token}"}

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
                prefix  = f"'{sheet_name}'!"
                for col in [yt_col, chk_col]:
                    sheets_service.spreadsheets().values().update(
                        spreadsheetId=cfg["spreadsheet_id"],
                        range=f"{prefix}{col}{i}",
                        valueInputOption="RAW",
                        body={"values": [[""]]},
                    ).execute()

                if do_upload(sheets_service, cfg, i, date_h, title_i, tag, download_url, ch["token_file"], auth_headers=auth_headers, sheet_name=sheet_name):
                    upload_count += 1
            except Exception as e:
                print(f"  再試行チェックエラー: {e}")
            continue

        if check == "済":
            continue

        print(f"\n[行{i}] {date_h} {title_i}")
        print(f"  アップロード先: {ch['name']}")

        if do_upload(sheets_service, cfg, i, date_h, title_i, tag, download_url, ch["token_file"], auth_headers=auth_headers, sheet_name=sheet_name):
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
    elif cmd == "zoom-setup":
        cfg = load_config()
        setup_zoom(cfg)
    elif cmd == "sync":
        sync_zoom(load_config())
    else:
        main()
