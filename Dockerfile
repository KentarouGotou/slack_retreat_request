# ベースイメージとして公式のPythonイメージを使用
FROM python:3.9-slim

# 作業ディレクトリを設定
WORKDIR /app

# 必要なシステムパッケージをインストール
RUN apt-get update && apt-get install -y \
    curl \
    vim \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Python用の依存ライブラリをインストール
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ngrokをインストール
RUN curl -s https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip -o ngrok.zip && \
    unzip ngrok.zip && \
    mv ngrok /usr/local/bin && \
    rm ngrok.zip

# ポート設定（必要に応じて変更）
EXPOSE 5000

# アプリケーションの起動コマンド
CMD ["bash"]