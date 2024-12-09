import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import hashlib
import hmac
from flask import Flask, request
from dotenv import load_dotenv
from cryptography.fernet import Fernet

# 環境変数を読み込む
load_dotenv()

app = Flask(__name__)
client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")

encryption_key = Fernet.generate_key()
cipher_suite = Fernet(encryption_key)

def encrypt_user_id(user_id):
    return cipher_suite.encrypt(user_id.encode()).decode()

def decrypt_user_id(encrypted_id):
    return cipher_suite.decrypt(encrypted_id.encode()).decode()

def sanitize_text(text):
    # 最大200文字まで許可し、特殊文字をエスケープ
    return text[:200].replace('<', '&lt;').replace('>', '&gt;')

def verify_slack_request():
    timestamp = request.headers['X-Slack-Request-Timestamp']
    body = request.get_data().decode('utf-8')
    sig_basestring = f'v0:{timestamp}:{body}'
    my_signature = 'v0=' + hmac.new(
        bytes(SLACK_SIGNING_SECRET, 'utf-8'),
        bytes(sig_basestring, 'utf-8'),
        hashlib.sha256
    ).hexdigest()

    slack_signature = request.headers['X-Slack-Signature']
    if not hmac.compare_digest(my_signature, slack_signature):
        return False
    return True

# 許可されたチャンネルIDを設定（例: #合宿要望）
ALLOWED_CHANNEL_ID = "C1234567890"

# 投稿者情報を記録する辞書
post_data = {}

@app.route('/post_request', methods=['POST'])
def post_request():
    """
    Slackの専用コマンドで要望を投稿するエンドポイント
    """
    # リクエストを検証
    if not verify_slack_request():
        return "Unauthorized request", 403
    data = request.form
    user_id = encrypt_user_id(data['user_id'])  # 投稿者IDを暗号化
    text = sanitize_text(data['text'])  # 投稿内容をサニタイズ
    channel_id = data['channel_id']  # コマンドを実行したチャンネルのID
    
    # チャンネルIDをチェック
    if channel_id != ALLOWED_CHANNEL_ID:
        return "このコマンドは特定のチャンネルでのみ使用できます。", 403

    try:
        # 匿名化して指定したチャンネルに投稿
        response = client.chat_postMessage(
            channel="#合宿要望",  # 投稿先のチャンネル名
            text=f"要望: {text}"
        )
        # 投稿タイムスタンプとユーザーIDを記録
        post_data[response['ts']] = user_id
        return "要望を投稿しました！", 200
    except SlackApiError as e:
        return f"Error: {e.response['error']}", 400

@app.route('/vote_summary', methods=['GET'])
def vote_summary():
    """
    要望の投票結果を集計する（管理者用）
    """
    data = request.form
    channel_id = data['channel_id']  # コマンドを実行したチャンネルのID
    # チャンネルIDをチェック
    if channel_id != ALLOWED_CHANNEL_ID:
        return "このコマンドは特定のチャンネルでのみ使用できます。", 403
    
    try:
        # チャンネルのメッセージ履歴を取得
        response = client.conversations_history(channel="#合宿要望")
        messages = response["messages"]
        summary = []

        for msg in messages:
            reactions = msg.get("reactions", [])
            total_votes = sum([reaction["count"] for reaction in reactions])
            summary.append({
                "text": msg.get("text"),
                "votes": total_votes
            })

        # 集計結果を返す
        return {"summary": summary}, 200
    except SlackApiError as e:
        return f"Error: {e.response['error']}", 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
