import urllib.request
import json
import time
import datetime
import os

WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=8b2dd898-782b-49ec-8cf0-31fb70095f1a"
FALL_24H_THRESHOLD = 5.0
FALL_7D_THRESHOLD = 10.0
HISTORY_FILE = "box_price_history.json"

def send_wechat_alert(message):
    payload = {
        "msgtype": "text",
        "text": {"content": "【BOX基金预警/行情】\n" + message}
    }
    try:
        req_data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            WEBHOOK_URL,
            data=req_data,
            headers={'Content-Type': 'application/json'}
        )
        urllib.request.urlopen(req)
        print("通知已发送")
    except Exception as e:
        print("发送失败：", e)

def fetch_box_price():
    url = "https://api.mixin.one/network/assets/top"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            for asset in data.get('data', []):
                if asset.get('symbol') == 'BOX':
                    return float(asset.get('price_usd', 0)), float(asset.get('change_usd', 0))
    except Exception as e:
        print("获取价格出错：", e)
    return None, None

def check_box_monitor():
    price, change_24h_api = fetch_box_price()
    if price is None:
        return

    # 读取本地历史记录
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            pass

    now = time.time()
    history.append({'timestamp': now, 'price': price})
    
    # 保留 7 天数据
    seven_days_ago = now - 7 * 24 * 3600
    history = [h for h in history if h['timestamp'] >= seven_days_ago]
    
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f)

    # 检查跌幅
    alert_messages = []
    if change_24h_api <= -FALL_24H_THRESHOLD:
        alert_messages.append(f"⚠️ 24小时内暴跌！当前跌幅 {change_24h_api:.2f}%。现价：${price:.4f} USD")

    old_records = [h for h in history if h['timestamp'] <= seven_days_ago + 3600]
    if old_records:
        baseline = old_records[0]['price']
        drop_7d = ((price - baseline) / baseline) * 100
        if drop_7d <= -FALL_7D_THRESHOLD:
            alert_messages.append(f"⚠️ 7天内累计下跌！当前跌幅 {drop_7d:.2f}%。现价：${price:.4f} USD")

    # 无论是否跌破阈值，也发送一条当前的实时行情，确保你能随时收到反馈
    status_msg = f"📊 BOX当前实时价格: ${price:.4f} USD\n📈 24小时涨跌幅: {change_24h_api:.2f}%\n"
    if alert_messages:
        status_msg += "\n" + "\n".join(alert_messages)
    else:
        status_msg += "✅ 当前运行平稳，无跌幅预警。"

    send_wechat_alert(status_msg)

if __name__ == '__main__':
    check_box_monitor()
