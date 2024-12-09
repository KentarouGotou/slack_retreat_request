# slack_retreat_request

## 環境を構築
- docker build -t slack-bot .
- docker run -it -p 5000:5000 -v $(pwd):/app --name slack-bot-container slack-bot