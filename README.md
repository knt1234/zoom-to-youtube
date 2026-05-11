# Zoom録画 → YouTube 自動アップロードツール

Zoom録画をGoogleスプレッドシートに自動転記し、指定のYouTubeチャンネルへ自動アップロードするツールです。ZapierなどのサービスなしでZoom APIを直接使用します。

---

## 目次

- [このツールでできること](#このツールでできること)
- [費用について](#費用について)
- [セットアップの全体の流れ](#セットアップの全体の流れ)
- [STEP 1: Pythonのインストール確認](#step-1-pythonのインストール確認)
- [STEP 2: ファイルのダウンロード](#step-2-ファイルのダウンロード)
- [STEP 3: ライブラリのインストール](#step-3-ライブラリのインストール)
- [STEP 4: Google Cloudプロジェクトの作成](#step-4-google-cloudプロジェクトの作成)
- [STEP 5: OAuth認証情報の作成](#step-5-oauth認証情報の作成)
- [STEP 6: スプレッドシートの準備](#step-6-スプレッドシートの準備)
- [STEP 7: 設定ウィザードの実行](#step-7-設定ウィザードの実行)
- [STEP 8: 認証セットアップ](#step-8-認証セットアップ)
- [STEP 9: タグのドロップダウン追加](#step-9-タグのドロップダウン追加)
- [STEP 10: Zoom API設定](#step-10-zoom-api設定)
- [毎回の使い方](#毎回の使い方)
- [コマンド一覧](#コマンド一覧)
- [定期自動実行の設定](#定期自動実行の設定)
- [よくある質問・トラブル解決](#よくある質問トラブル解決)
- [セキュリティ](#セキュリティ)

---

## このツールでできること

### できること

- **Zoom録画をスプレッドシートに自動転記**（Zapier不要）
- スプレッドシートのリンクからZoom録画を自動ダウンロード
- 指定したYouTubeチャンネルへ自動アップロード（限定公開）
- アップロード完了後、スプレッドシートにYouTube URLと「済」を自動記入
- 複数のYouTubeチャンネルへの振り分けアップロード
- 24時間以上処理中の動画を自動で再アップロード
- **Zoom上の録画をゴミ箱に移動**（完全削除ではなく復元可能）

### できないこと

- 動画の編集・変換（録画そのままアップロードされます）
- YouTubeへの動画説明文・タグの自動入力（空欄でアップロードされます）
- パソコンの電源が切れている間の自動実行

---

## 費用について

**このツールの利用にかかる費用は基本的に無料です。**

| 項目 | 費用 | 備考 |
|---|---|---|
| Google Cloudプロジェクト | 無料 | |
| YouTube Data API v3 | 無料（上限あり） | 1日10,000クォータまで |
| Google Sheets API | 無料 | |
| このスクリプト | 無料 | オープンソース |

### YouTube APIの無料上限について

- **1日の無料上限**：10,000クォータ
- **動画1本のアップロード**：約1,600クォータ消費
- **1日にアップロードできる目安**：約6本

このツールはデフォルトで1回の実行につき最大5本までに制限しており、無料枠を超えないようにしています。

---

## セットアップの全体の流れ

セットアップは**最初の1回だけ**行えばOKです。以下の順番で進めてください。

1. Pythonのインストール確認
2. ファイルのダウンロード
3. 必要なライブラリのインストール
4. Google Cloudプロジェクトの作成
5. OAuth認証情報の作成（`client_secrets.json` の取得）
6. スプレッドシートの準備
7. 設定ウィザードの実行（`config` コマンド）
8. 認証セットアップ（`setup` コマンド）
9. タグのドロップダウン追加（`sheet` コマンド）
10. Zoom APIの設定（`zoom-setup` コマンド）

---

## STEP 1: Pythonのインストール確認

Pythonはこのツールを動かすために必要なソフトです。まずインストールされているか確認します。

### ターミナルを開く

**Macの場合：**
1. キーボードで `Command（⌘）+ スペース` を同時に押す
2. 検索窓に「ターミナル」と入力してEnterキーを押す
3. 黒または白い画面が開いたらOKです

![Spotlightでターミナルを検索している画面](images/01-01_spotlight_open.png)
*▲ Command+スペースで検索窓を開き「ターミナル」と入力する*

> **ターミナルとは？**
> コンピューターに文字で命令を入力する画面です。マウスで操作する代わりに、キーボードでコマンド（命令文）を入力して操作します。

### Pythonのバージョンを確認する

ターミナルに以下を入力して、Enterキーを押してください。

```
python3 --version
```

**表示結果の確認：**

| 表示された内容 | 対処 |
|---|---|
| `Python 3.10.x` 以上 | そのまま次のSTEPへ進んでOK |
| `Python 3.9.x` 以下 | 動作しますが、できれば最新版に更新推奨 |
| `command not found` | 下記の手順でインストールしてください |

### Pythonをインストールする（まだの場合）

1. ブラウザで [https://www.python.org/downloads/](https://www.python.org/downloads/) を開く
2. 「Download Python 3.xx.x」という黄色いボタンをクリック
3. ダウンロードされたファイルを開いてインストール
4. インストール時に **「Add Python to PATH」にチェックを入れること**（重要）
5. インストール完了後、ターミナルを一度閉じて再度開き、`python3 --version` で確認

---

## STEP 2: ファイルのダウンロード

### GitHubからファイルをダウンロードする

1. ブラウザで [このリポジトリのGitHubページ](https://github.com/knt1234/zoom-to-youtube) を開く

![GitHubリポジトリのトップページ](images/01-02_github_repo.png)
*▲ GitHubリポジトリのトップページ*

2. 緑色の「**Code**」ボタンをクリック → 「**Download ZIP**」をクリック
3. ダウンロードされたZIPファイルをダブルクリックして解凍する（通常は「ダウンロード」フォルダ）

### 保存フォルダを作成してファイルを移動する

ターミナルで以下を入力して、Enterキーを押してください。

```
mkdir -p ~/Documents/movie-upload
```

> `mkdir` はフォルダを作るコマンドです。「ドキュメント」フォルダの中に「movie-upload」というフォルダが作られます。

解凍したフォルダの中にある以下のファイルを、Finder（ファイル管理画面）で `~/Documents/movie-upload/` フォルダに移動してください。

- `upload.py`
- `config.example.json`
- `README.md`

> **Finderでの移動方法：** ファイルを選択して `Command + C` でコピー → 移動先フォルダを開いて `Command + V` で貼り付け

---

## STEP 3: ライブラリのインストール

ターミナルで以下のコマンドを入力して、Enterキーを押してください。

```
pip3 install google-api-python-client google-auth-oauthlib requests
```

完了すると最後に `Successfully installed ...` と表示されます。

> **エラーが出た場合：** `pip3` の代わりに `pip` を使ってみてください。
> ```
> pip install google-api-python-client google-auth-oauthlib requests
> ```

---

## STEP 4: Google Cloudプロジェクトの作成

GoogleのAPIを使うために必要な設定です。費用はかかりません。

### 4-1. Google Cloud Consoleを開く

1. ブラウザで [https://console.cloud.google.com/](https://console.cloud.google.com/) を開く
2. Googleアカウントでログインする（スプレッドシートを管理しているアカウント推奨）

### 4-2. 新しいプロジェクトを作成する

1. 画面上部の「**Google Cloud**」ロゴの右隣にあるプロジェクト名をクリック
2. 右上の「**新しいプロジェクト**」をクリック
3. プロジェクト名に任意の名前（例：`movie-upload`）を入力して「**作成**」をクリック

![新しいプロジェクトを作成するフォーム](images/02-01_gcp_new_project_form.png)
*▲ プロジェクト名を入力して「作成」をクリック*

4. 画面右上に通知が出たら「**プロジェクトを選択**」をクリックして、作ったプロジェクトに切り替える

![プロジェクト選択ダイアログ](images/02-02_gcp_project_select_dialog.png)
*▲ 作成したプロジェクトを選択して切り替える*

### 4-3. YouTube Data APIを有効化する

1. 左上のメニュー（三本線のアイコン）→「**APIとサービス**」→「**ライブラリ**」をクリック
2. 検索ボックスに「YouTube Data API」と入力

![YouTube Data API v3の検索画面](images/02-03_gcp_api_search_youtube.png)
*▲ 検索ボックスに「YouTube Data API」と入力*

3. 「**YouTube Data API v3**」をクリック

![YouTube Data API v3の検索結果](images/02-04_gcp_api_result_youtube.png)
*▲ 「YouTube Data API v3」をクリック*

4. 「**有効にする**」ボタンをクリック

![YouTube Data API v3を有効にする](images/02-05_gcp_youtube_api_enable.png)
*▲ 「有効にする」をクリック*

### 4-4. Google Sheets APIを有効化する

1. 左上のメニュー →「**APIとサービス**」→「**ライブラリ**」をクリック
2. 検索ボックスに「Google Sheets API」と入力

![Google Sheets APIの検索画面](images/02-06_gcp_api_search_sheets.png)
*▲ 「Google Sheets API」と入力して検索*

3. 「**Google Sheets API**」をクリック

![Google Sheets APIの検索結果](images/02-07_gcp_api_result_sheets.png)
*▲ 「Google Sheets API」をクリック*

4. 「**有効にする**」ボタンをクリック

![Google Sheets APIを有効にする](images/02-08_gcp_sheets_api_enable.png)
*▲ 「有効にする」をクリック*

---

## STEP 5: OAuth認証情報の作成

このツールがGoogleのサービスにアクセスするための「鍵ファイル」を作ります。

### 5-1. OAuth同意画面を設定する

1. 左上のメニュー →「**APIとサービス**」→「**OAuth同意画面**」（または「**Google Auth Platform**」）をクリック

![OAuth同意画面がまだ設定されていない状態](images/02-09_gcp_oauth_not_configured.png)
*▲ 初回は「開始」ボタンをクリックして設定を始める*

2. アプリ情報の入力画面が表示される。以下を入力する

![アプリ情報の入力フォーム（入力前）](images/02-10_gcp_oauth_appinfo_empty.png)
*▲ アプリ情報の入力フォーム*

   - **アプリ名**：`Movie Upload Tool`（任意の名前でOK）
   - **ユーザーサポートメール**：自分のGmailアドレスを選択

![アプリ名とメールを入力した状態](images/02-11_gcp_oauth_appinfo_filled.png)
*▲ アプリ名とユーザーサポートメールを入力した状態*

3. 「**次へ**」をクリック

4. **対象ユーザー（Audience）の選択**：「**外部**」を選択して「**作成**」をクリック

![対象ユーザーで「外部」を選択する画面](images/02-12_gcp_oauth_audience_external.png)
*▲ 「外部」を選択して「作成」をクリック*

> **「外部」とは？** 特定のGoogle Workspaceに限定せず、一般のGoogleアカウントで認証できる設定です。個人利用の場合はこちらを選択してください。

5. **連絡先情報**：デベロッパーの連絡先メールアドレス（自分のGmail）を入力して「**次へ**」をクリック

![連絡先メールアドレスの入力画面](images/02-13_gcp_oauth_contact.png)
*▲ 連絡先メールアドレスを入力する*

6. **ポリシー同意**：「Googleのユーザーデータポリシーに同意します」にチェックを入れる

![ポリシー同意画面](images/02-14_gcp_oauth_finish_policy.png)
*▲ ポリシーへの同意にチェックを入れる*

7. すべての項目にチェックが入った状態を確認して「**続行**」をクリック

![全項目チェック済みの確認画面](images/02-15_gcp_oauth_finish_allcheck.png)
*▲ すべての項目にチェックが入っていることを確認して「続行」をクリック*

8. 「OAuth同意画面を作成しました」のトーストが表示されればOK

![作成完了のトースト通知](images/02-16_gcp_oauth_created_toast.png)
*▲ 「OAuth同意画面を作成しました」と表示されれば作成完了*

### 5-2. テストユーザーを追加する

1. 「**対象**」（Audience）タブをクリック

![対象タブの画面（テスト中ステータス）](images/02-17_gcp_oauth_audience_status.png)
*▲ 「対象」タブをクリック。ステータスが「テスト中」になっている*

2. 「**テストユーザー**」セクションで「**ADD USERS**」をクリック
3. アップロードに使う**すべてのGmailアドレスを追加**する（YouTubeチャンネルのオーナーアカウント）

![テストユーザーを追加するダイアログ](images/02-18_gcp_oauth_add_testuser.png)
*▲ 「ADD USERS」をクリックしてメールアドレスを追加する*

> YouTubeチャンネルが複数アカウントにまたがる場合、すべてのアカウントを追加してください

4. 「**保存**」をクリック

### 5-3. OAuthクライアントIDを作成する

1. 左上のメニュー →「**APIとサービス**」→「**認証情報**」をクリック
2. 「**クライアント**」の欄を確認。まだクライアントがない状態

![クライアントがまだない状態](images/02-19_gcp_oauth_clients_empty.png)
*▲ まだクライアントIDが作成されていない状態*

3. 「**＋ クライアントを作成**」（または「認証情報を作成」→「OAuth クライアント ID」）をクリック
4. アプリケーションの種類のメニューをクリック

![アプリケーションの種類メニュー](images/02-20_gcp_oauth_client_type_menu.png)
*▲ アプリケーションの種類のドロップダウンをクリック*

5. 「**デスクトップ アプリ**」を選択

![デスクトップアプリを選択した状態](images/02-21_gcp_oauth_client_desktop.png)
*▲ 「デスクトップ アプリ」を選択する*

6. 名前は何でもOK（例：`movie-upload-client`）→「**作成**」をクリック
7. 作成完了のダイアログが表示される。「**JSONをダウンロード**」をクリック

![クライアントID作成完了のダイアログ](images/02-22_gcp_oauth_client_done.png)
*▲ 「JSONをダウンロード」をクリックしてファイルを保存する（画像内の認証情報はマスク済み）*

8. ダウンロードされたファイルの名前を **`client_secrets.json`** に変更する
   > ファイル名を右クリック →「名前を変更」で変更できます

9. `client_secrets.json` を `~/Documents/movie-upload/` フォルダに移動する

![Finderでclient_secrets.jsonが確認できる状態](images/02-23_finder_json_file.png)
*▲ movie-uploadフォルダにclient_secrets.jsonが入っていればOK*

---

## STEP 6: スプレッドシートの準備

以下の列構成でGoogleスプレッドシートを新規作成してください。

| 列 | ヘッダー名 | 内容 | 入力方法 |
|---|---|---|---|
| A | 日付 | 録画日 | ⚙️ 自動入力 |
| B | ID | Zoom録画の識別ID | ⚙️ 自動入力 |
| C | 共有リンク | ZoomのURL | ⚙️ 自動入力 |
| D | ダウンロードリンク | 動画のダウンロードURL | ⚙️ 自動入力 |
| E | YouTubeリンク | アップロード後に自動入力 | ⚙️ 自動入力 |
| F | 備考 | メモなど（自由記入） | ✏️ 手動（任意） |
| G | 日付（タイトル用） | YouTubeタイトルに使う日付 | ⚙️ 自動入力 |
| **H** | **動画タイトル** | **YouTubeのタイトルになる** | **✏️ 手動（必須）** |
| I | 処理完了 | アップロード後に「済」が入る | ⚙️ 自動入力 |
| **J** | **タグ** | **アップロード先チャンネルを指定** | **✏️ 手動（必須）** |
| K | アップロード日時 | 完了日時が自動入力 | ⚙️ 自動入力 |
| L | Zoom削除フラグ | 「削除OK」と入れると録画をゴミ箱へ | ✏️ 手動（任意） |

> **⚙️ 自動入力の列は触らなくてOKです。**
> **✏️ 手動入力が必要な列は H列（動画タイトル）と J列（タグ）です。**

![完成したスプレッドシートの1行目の画面](images/03-01_spreadsheet_header.png)
*▲ 1行目にこの通りヘッダーを入力した状態*

### スプレッドシートのURLを確認する

スプレッドシートのURLには「スプレッドシートID」と「シートID」が含まれています。

```
https://docs.google.com/spreadsheets/d/【スプレッドシートID】/edit?gid=【シートID】
```

設定ウィザード実行時にこのURLをそのまま貼り付けると、スプレッドシートIDとシートIDが自動で読み取られます。

> 複数のシート（タブ）がある場合、URLの `gid=XXXXX` の部分でどのシートを使うか指定できます。

---

## STEP 7: 設定ウィザードの実行

ターミナルで以下を実行してください。

```
python3 ~/Documents/movie-upload/upload.py config
```

画面の指示に従って以下の情報を入力します。

**① スプレッドシートのURL**

GoogleスプレッドシートをブラウザのURLバーからコピーして貼り付けてください。

> **ターミナルへの貼り付け方：** `Command + V` で貼り付けできます。

**② 1回の実行で最大何件アップロードするか**

`5` を推奨します。Enterキーをそのまま押すとデフォルトの5になります。

**③ 各列の番号**

スプレッドシートの列番号を入力します（A=1、B=2、C=3...）。
STEP 6の表の通りに作った場合の入力値：

| 質問 | 入力する番号 |
|---|---|
| ダウンロードリンク列 | `4`（D列） |
| YouTubeリンク列 | `5`（E列） |
| 動画タイトル用の日付列 | `7`（G列） |
| 動画タイトル列 | `8`（H列） |
| チェック列 | `9`（I列） |
| タグ列 | `10`（J列） |
| アップロード日時列 | `11`（K列） |

**④ YouTubeチャンネルの数と情報**

アップロード先のYouTubeチャンネルの数を入力し、各チャンネルの情報を入力します。

- **タグ名**：スプレッドシートのJ列に入力する識別名（例：`ESL`、`NCA`）
- **チャンネルの説明**：自分がわかりやすい名前（例：`ESL事務局 @ESL-jimukyoku`）

完了すると `config.json が保存されました` と表示されます。

![設定ウィザードの実行画面と完了メッセージ](images/04-01_terminal_setup_run.png)
*▲ 各項目を入力していくと最後に「config.json を保存しました」と表示される*

---

## STEP 8: 認証セットアップ

各YouTubeチャンネルへのアクセス権を設定します。

```
python3 ~/Documents/movie-upload/upload.py setup
```

チャンネルの数だけブラウザが自動で開きます。それぞれ対応するGoogleアカウントでログインしてください。

### 「このアプリはGoogleで確認されていません」と表示された場合

個人利用アプリのため正常な表示です。以下の手順で続行してください。

1. 「**詳細**」をクリック
2. 「**（アプリ名）に移動（安全ではないページ）**」をクリック
3. 「**続行**」をクリック

認証が完了するとブラウザに「The authentication flow has completed.」と表示されます。その画面は閉じてOKです。

すべてのチャンネルで認証が完了すると、ターミナルに `全認証完了` と表示されます。

![全認証完了の画面](images/04-02_terminal_setup_done.png)
*▲ ターミナルに「全認証完了」と出ればOK*

---

## STEP 9: タグのドロップダウン追加

スプレッドシートのJ列にチャンネル選択用のドロップダウンを追加します。

```
python3 ~/Documents/movie-upload/upload.py sheet
```

完了後、スプレッドシートを開いてJ列のセルをクリックするとドロップダウンが表示されるようになります。

---

## STEP 10: Zoom API設定

Zoom録画をスプレッドシートに自動転記するための設定です。

### 10-1. Zoom Marketplaceでアプリを作成する

1. ブラウザで [https://marketplace.zoom.us/](https://marketplace.zoom.us/) を開く
2. Zoomアカウントでログインする
3. 右上の「**Develop**」をクリック →「**Build App**」をクリック
4. 一覧の中から「**Server-to-Server OAuth**」を見つけて「**Create**」をクリック

![アプリタイプ選択画面（Server-to-Server OAuthを選ぶ）](images/05-01_zoom_app_type_select.png)
*▲ 「Server-to-Server OAuth」の「Create」をクリック*

5. アプリ名に任意の名前（例：`zoom-auto-sync`）を入力して「**Create**」をクリック

![アプリ名の入力画面](images/05-02_zoom_app_name_input.png)
*▲ アプリ名を入力して「Create」をクリック*

### 10-2. アプリ情報を入力する（必須項目）

アプリ作成後、**Basic Information** タブで以下の入力が必要です。

- **Short Description**（必須）：短い説明文を入力してください（例：`Zoom録画を自動転記するツール`）
- **Company Name**（必須）：会社名。個人の場合は自分の名前や屋号でOKです

![Basic Informationの入力画面](images/05-04_zoom_information.png)
*▲ Short DescriptionとCompany Nameは必ず入力する*

入力後「**Continue**」をクリックして次に進む。

### 10-3. 認証情報をメモする

左メニューの「**App Credentials**」をクリックします。以下の3つをメモしておいてください（後でコマンドに入力します）。

- **Account ID**
- **Client ID**
- **Client Secret**（「Show」ボタンを押すと表示されます）

![App Credentialsの画面](images/05-03_zoom_credentials.png)
*▲ 3つの情報をコピーしておく（画像では値をマスクしています）*

> **コピーの際の注意：** 前後に半角スペースが入らないように注意してください。ペースト後に余分なスペースがあるとエラーになります。

### 10-4. スコープ（権限）を追加する

1. 左メニューの「**Scopes**」をクリック
2. 「**+ Add Scopes**」をクリック
3. 検索ボックスに「`recording`」と入力

![スコープ検索画面](images/05-05_zoom_scopes_search.png)
*▲ 「recording」と検索して絞り込む*

4. 以下の **2つ** にチェックを入れる

| スコープ名 | 用途 |
|---|---|
| `cloud_recording:read:list_user_recordings:admin` | Zoom録画の一覧をスプレッドシートに転記する |
| `cloud_recording:delete:meeting_recording:admin` | Zoom録画をゴミ箱に移動する |

![録画一覧取得スコープにチェックを入れた状態](images/05-06_zoom_scope_list_read_checked.png)
*▲ `cloud_recording:read:list_user_recordings:admin` にチェック*

![録画削除スコープにチェックを入れた状態](images/05-07_zoom_scope_delete_checked.png)
*▲ `cloud_recording:delete:meeting_recording:admin` にチェック*

5. 「**Done**」をクリックして保存

![スコープが追加された状態](images/05-08_zoom_scopes_added.png)
*▲ 2つのスコープが追加された状態*

> **注意：** `cloud_recording:delete:recording_file:admin`（ファイル単位の削除）と間違えないようにしてください。ミーティング全体をゴミ箱に移動するには `cloud_recording:delete:meeting_recording:admin` が必要です。

### 10-5. アプリを有効化する

1. 左メニューの「**Activation**」をクリック
2. 「**Activate your app**」ボタンをクリック

![Activateボタンの画面](images/05-09_zoom_activation_ready.png)
*▲ 「Activate your app」をクリック*

3. ステータスが「**Activated**」になればOK

![Activatedになった画面](images/05-10_zoom_activation_done.png)
*▲ 「Activated」と表示されれば有効化完了*

> **スコープを変更した後は必ず「Deactivate」→「Activate」を行ってください。** これをしないと変更が反映されません。

### 10-6. Zoom設定をツールに保存する

ターミナルで以下を実行してください。

```
python3 ~/Documents/movie-upload/upload.py zoom-setup
```

STEP 10-3でメモした **Account ID・Client ID・Client Secret** をそれぞれ入力して完了です。

![zoom-setupコマンドの実行画面](images/05-11_terminal_zoom_setup.png)
*▲ Account ID・Client ID・Client Secretの入力を求められる（入力値はマスク済み）*

---

## 毎回の使い方

### ① Zoom録画をスプレッドシートに転記する（sync）

```
python3 ~/Documents/movie-upload/upload.py sync
```

過去30日間のZoom録画が自動的にスプレッドシートに転記されます。

> **コマンドが「見つからない」と言われる場合：**
> ターミナルで先に以下を実行してください。
> ```
> cd ~/Documents/movie-upload
> ```
> その後 `python3 upload.py sync` と入力してください。

### ② スプレッドシートでH列とJ列を入力する

スプレッドシートを開いて、アップロードしたい行に入力してください。

| 列 | 入力内容 |
|---|---|
| **H列（動画タイトル）** | YouTubeにアップロードする際のタイトル（**必須**） |
| **J列（タグ）** | アップロード先チャンネルのタグ名（**必須**）。ドロップダウンから選択 |

> **H列（動画タイトル）が空欄の行はスキップされます。** 必ず入力してください。

### ③ YouTubeにアップロードする

```
python3 ~/Documents/movie-upload/upload.py
```

J列にタグが入力されている行が順番にアップロードされます。完了するとE列にYouTube URLが、I列に「済」が自動入力されます。

### ④ Zoom録画をゴミ箱に移動する

Zoomのクラウドレコーディングに溜まった録画をゴミ箱に移動できます（完全削除ではなく、Zoom上のゴミ箱から復元可能です）。

**手順：**

1. スプレッドシートのL列で「**削除OK**」を選択する

![L列のドロップダウンで削除OKを選ぶ画面](images/06-01_spreadsheet_trash_dropdown.png)
*▲ L列のセルをクリックすると「削除OK」「削除済」を選べる*

2. ターミナルでアップロードコマンドを実行する

```
python3 ~/Documents/movie-upload/upload.py
```

3. 「✓ ゴミ箱に移動しました」と表示されれば完了。L列が「削除済」に自動更新されます。

![ゴミ箱移動が成功したターミナル画面](images/06-02_terminal_trash_run.png)
*▲ 「✓ ゴミ箱に移動しました」と表示されれば成功*

4. Zoomのクラウドレコーディング画面で「ゴミ箱」を確認すると、録画が移動されています。

![Zoomのゴミ箱に録画が移動した画面](images/06-03_zoom_trash_result.png)
*▲ Zoomのクラウドレコーディング→ゴミ箱に移動されている*

> **ゴミ箱の録画を完全に削除したい場合** は、Zoomの管理画面から手動で操作してください。

---

## コマンド一覧

すべてのコマンドは `~/Documents/movie-upload/` フォルダで実行してください。

```
cd ~/Documents/movie-upload
```

| コマンド | 内容 | 実行タイミング |
|---|---|---|
| `python3 upload.py` | アップロード実行 ＋ Zoom削除処理 | 毎回 |
| `python3 upload.py sync` | Zoom録画をスプレッドシートに転記 | 毎回（アップロード前） |
| `python3 upload.py config` | 設定ウィザードを起動 | 初回のみ |
| `python3 upload.py setup` | Google認証セットアップ | 初回のみ |
| `python3 upload.py sheet` | J列にドロップダウンを追加 | 初回のみ |
| `python3 upload.py zoom-setup` | Zoom API設定 | 初回のみ |

---

## 定期自動実行の設定

Macの **cron**（クーロン）という機能を使うと、決まった日時に自動でスクリプトを実行できます。
毎回ターミナルを開いてコマンドを入力する手間がなくなります。

> **注意：パソコンの電源が入っていて、スリープ解除されている必要があります。**
> 電源オフ・スリープ中は実行されません。

---

### 設定手順

#### 1. ターミナルを開いて以下を入力する

```
crontab -e
```

初回起動時に「どのエディタを使うか」を聞かれる場合があります。番号で選択してください（`nano` を選ぶのがおすすめです）。

#### 2. 以下の1行を追加する

```
0 9 5,10,15,20,25,30 * * /usr/bin/python3 /Users/あなたのユーザー名/Documents/movie-upload/upload.py >> /Users/あなたのユーザー名/Documents/movie-upload/log.txt 2>&1
```

> **「あなたのユーザー名」の確認方法：** ターミナルで `echo $HOME` と入力すると `/Users/xxx` の形式で表示されます。`xxx` の部分がユーザー名です。

**設定例（ユーザー名が `Kenta` の場合）：**

```
0 9 5,10,15,20,25,30 * * /usr/bin/python3 /Users/Kenta/Documents/movie-upload/upload.py >> /Users/Kenta/Documents/movie-upload/log.txt 2>&1
```

この設定の意味：
- **毎月 5・10・15・20・25・30日 の朝9時**にアップロードを自動実行
- 実行結果は `log.txt` に記録される

#### 3. 保存して終了する

`nano` の場合：`Ctrl + X` → `Y` → `Enter` で保存して終了します。

#### 4. 設定を確認する

```
crontab -l
```

追加した行が表示されれば設定完了です。

---

### 実行スケジュールのカスタマイズ

「もっと頻繁に実行したい」「別の曜日にしたい」場合は、上記のコマンドの日付部分を変更します。

| やりたいこと | 設定例 |
|---|---|
| 毎日朝9時 | `0 9 * * *` |
| 毎週月曜日の朝9時 | `0 9 * * 1` |
| 毎月1日と15日の朝8時 | `0 8 1,15 * *` |

---

### 実行ログの確認

自動実行の結果は `log.txt` に記録されます。

```
cat ~/Documents/movie-upload/log.txt
```

エラーが出ていないか定期的に確認することをおすすめします。

---

### 自動実行を止めたい場合

```
crontab -e
```

で設定ファイルを開き、追加した行を削除して保存してください。

---

### よくある問題

**自動実行されない**

以下を確認してください。

1. **パソコンがスリープしていないか** — 実行時間にスリープ解除されている必要があります
2. **ターミナルにフルディスクアクセス権限があるか** — Mac のシステム設定 → プライバシーとセキュリティ → フルディスクアクセス → ターミナルにチェックが入っているか確認してください
3. **`crontab -l` で設定が表示されるか** — 設定が正しく保存されているか確認してください

**「Operation not permitted」エラーが log.txt に出る**

ターミナルのフルディスクアクセス権限が付与されていません。上記 2. の手順で権限を付与してください。

---

## よくある質問・トラブル解決

### 🔵 Zoom設定について

---

**Q. Zoom Marketplaceでアプリ作成時に「Short Description」「Company Name」の入力を求められる**

A. どちらも入力必須です。
- **Short Description**：短い説明文でOKです（例：`Zoom録画の自動転記ツール`）
- **Company Name**：個人事業主や個人利用の場合は自分の名前や屋号を入力してください

---

**Q. スコープ（権限）を追加したのに、同じエラーが出る**

A. スコープを変更した後は **アプリの再起動が必要** です。
1. Zoom Marketplace で対象アプリを開く
2. 「Activation」メニューの「**Deactivate**」ボタンをクリック
3. 続けて「**Activate**」ボタンをクリック

この手順を行わないとスコープの変更が反映されません。

---

**Q. `cloud_recording:delete:recording_file:admin` と `cloud_recording:delete:meeting_recording:admin` のどちらを追加すればいいか**

A. **`cloud_recording:delete:meeting_recording:admin`** を追加してください。
- `recording_file:admin`：特定の1ファイルだけを削除するスコープ（こちらではゴミ箱移動が完全に動きません）
- `meeting_recording:admin`：ミーティングの録画全体（動画・音声まとめて）をゴミ箱に移動するスコープ（**こちらが正解**）

---

**Q. Zoomの録画が取得できない（syncで0件と表示される）**

A. 以下を確認してください。
- Zoomのクラウドレコーディング機能が有効になっているか（Zoomの設定→録画）
- `zoom-setup` コマンドで入力したAccount ID・Client ID・Client Secretが正しいか（コピー時に余分なスペースが入っていないか）
- Zoom Marketplaceのアプリが「Activated」状態になっているか

---

### 🟢 Google認証について

---

**Q. 「このアプリはGoogleで確認されていません」という警告が出る**

A. 個人利用アプリのため正常な表示です。以下の手順で続行してください。
1. 「**詳細**」をクリック
2. 「**（アプリ名）に移動（安全ではないページ）**」をクリック
3. 「**続行**」をクリック

---

**Q. `invalid_grant` というエラーが出る**

A. 認証トークンの有効期限が切れています。以下の手順でリセットしてください。
1. Finder で `~/Documents/movie-upload/tokens/` フォルダを開く
2. フォルダの中の `.pkl` ファイルをすべて削除する
3. 再度 `python3 upload.py setup` を実行して認証をやり直す

---

**Q. テストユーザーを追加し忘れた**

A. Google Cloud Console → OAuth同意画面 →「テストユーザー」タブからいつでも追加できます。追加後すぐに反映されます。

---

### 🟡 アップロードについて

---

**Q. アップロードが0件で終わる**

A. 以下を順番に確認してください。

| 確認項目 | 確認方法 |
|---|---|
| H列（動画タイトル）が入力されているか | 空欄の行はスキップされます |
| J列（タグ）が正しく入力されているか | 大文字・小文字・スペースに注意。設定したタグと完全一致が必要 |
| D列（ダウンロードリンク）が入力されているか | syncを実行すると自動入力されます |
| I列（処理完了）が「済」になっていないか | 「済」の行は再アップロードされません |

---

**Q. 1日にアップロードできる件数に上限はある？**

A. YouTube APIの無料枠の関係で、1日に約6本が目安です。`config.json` を開き `max_uploads_per_run` の数字を変更することで1回の実行あたりの上限を変えられます。上限を超えた分は次回実行時に処理されます。

---

**Q. ダウンロードが0%のまま止まる**

A. ZoomのダウンロードURLの有効期限が切れている可能性があります。
1. `python3 upload.py sync` を再実行して最新のURLを取得する
2. その後 `python3 upload.py` でアップロードを再実行する

---

**Q. アップロードが途中で止まった**

A. 次回実行時に自動的に再開されます。24時間以上処理中の動画がある場合は自動で再アップロードされます。

---

**Q. 動画はパソコンに保存される？**

A. 保存されません。一時的にダウンロードしてYouTubeにアップロードした後、自動で削除されます。

---

### 🔴 Zoom削除機能について

---

**Q. L列を「削除OK」にしたのに何も起きない**

A. L列を「削除OK」にしただけでは処理は実行されません。**ターミナルで `python3 upload.py` を実行する必要があります**。実行後にターミナルに「✓ ゴミ箱に移動しました」と表示されれば成功です。

---

**Q. スプレッドシートでは「削除済」になっているのに、Zoomに録画が残っている**

A. 古いバージョンのスクリプトで発生していたバグです。**最新版のスクリプトで再度実行**してください。
1. L列の「削除済」を「削除OK」に書き直す
2. `python3 upload.py` を実行する

---

**Q. 動画ファイルだけが消えて、音声ファイルが残った**

A. 古いバージョンのスクリプトで発生していたバグです。音声ファイルはZoomのゴミ箱に移動しているか確認してください。移動していない場合は最新版のスクリプトで再度実行してください（上記と同様の手順）。

---

**Q. 「ゴミ箱に移動」とは何？完全に削除されるの？**

A. Zoomのゴミ箱に移動するだけで、**完全削除ではありません**。Zoomのクラウドレコーディング画面から「ゴミ箱」を開くと確認・復元できます。完全に削除したい場合はZoomの管理画面から手動で操作してください。

---

### ⚪ その他

---

**Q. GitHubのページが更新されたのに自分の環境に反映されない**

A. このツールはダウンロードしたローカルのファイルで動作します。GitHubを更新しても手動で再ダウンロードしない限り自分の環境には反映されません。最新版を使いたい場合は STEP 2 の手順でZIPを再ダウンロードして `upload.py` を上書きしてください（`config.json` や `tokens/` フォルダはそのままでOKです）。

---

**Q. スプレッドシートのURLに `gid=` がある。どうすればいい？**

A. `gid=` の後の数字は「シートID」です。スプレッドシートに複数のタブ（シート）がある場合、このIDで対象シートを指定できます。設定ウィザード（`config` コマンド）でスプレッドシートのURLをそのまま貼り付けると、シートIDも自動で読み取られます。

---

**Q. `python3 upload.py` を実行すると「config.jsonが見つかりません」と表示される**

A. ターミナルで実行するフォルダが違う可能性があります。以下を実行してから再度お試しください。

```
cd ~/Documents/movie-upload
python3 upload.py
```

---

## セキュリティ

以下のファイルには認証情報が含まれるため、`.gitignore` により自動的にGitの管理対象から除外されています。**他人に渡したり、インターネット上に公開しないよう注意してください。**

- `client_secrets.json`：Google APIの鍵ファイル
- `config.json`：スプレッドシートIDやZoomのAPI情報
- `tokens/` フォルダ：認証トークン（ログイン情報）

これらのファイルを誤って共有してしまった場合は、すぐにGoogle Cloud ConsoleおよびZoom Marketplaceで認証情報を再発行してください。
