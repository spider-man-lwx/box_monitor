import urllib.request
import json
import time
import datetime
import sys
import os

# 修复 Windows 控制台中文编码问题
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=8b2dd898-782b-49ec-8cf0-31fb70095f1a"
FALL_24H_THRESHOLD = 5.0
FALL_7D_THRESHOLD = 10.0
COST_PRICE = 7.97
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
        print("通知已成功发送到企业微信！")
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
                    return float(asset.get('price_usd', 0))
    except Exception as e:
        print("获取价格出错：", e)
    return None

def check_box_monitor():
    price = fetch_box_price()
    if price is None:
        return

    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            pass

    now = time.time()
    history.append({'timestamp': now, 'price': price})
    
    seven_days_ago = now - 7 * 24 * 3600
    history = [h for h in history if h['timestamp'] >= seven_days_ago]
    
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f)

    one_day_ago = now - 24 * 3600
    day_records = [h for h in history if h['timestamp'] <= one_day_ago + 3600]
    
    change_24h_pct = 0.0
    if day_records:
        old_price_24h = day_records[0]['price']
        change_24h_pct = ((price - old_price_24h) / old_price_24h) * 100

    seven_records = [h for h in history if h['timestamp'] <= seven_days_ago + 3600]
    change_7d_pct = 0.0
    if seven_records:
        old_price_7d = seven_records[0]['price']
        change_7d_pct = ((price - old_price_7d) / old_price_7d) * 100

    alert_messages = []
    
    if price < COST_PRICE:
        diff_pct = ((price - COST_PRICE) / COST_PRICE) * 100
        alert_messages.append(f"跌破持仓均价！当前现价 ${price:.4f} 已低于你的买入均价 ${COST_PRICE}（浮亏 {diff_pct:.2f}%）")

    if change_24h_pct <= -FALL_24H_THRESHOLD:
        alert_messages.append(f"24小时内暴跌！当前跌幅达到 {change_24h_pct:.2f}%（超过 5% 阈值）。")

    if seven_records and change_7d_pct <= -FALL_7D_THRESHOLD:
        alert_messages.append(f"7天内累计下跌！当前 7 天跌幅达到 {change_7d_pct:.2f}%（超过 10% 阈值）。")

    profit_pct = ((price - COST_PRICE) / COST_PRICE) * 100
    status_msg = f"BOX当前实时价格: ${price:.4f} USD\n"
    status_msg += f"持仓均价: ${COST_PRICE} | 当前盈亏: {profit_pct:+.2f}%\n"
    status_msg += f"24小时真实涨跌: {change_24h_pct:+.2f}%\n"
    
    if len(history) > 1 and seven_records:
        status_msg += f"7天真实涨跌: {change_7d_pct:+.2f}%\n"
    
    if alert_messages:
        status_msg += "\n" + "\n".join(alert_messages)
    else:
        status_msg += "运行平稳，价格高于均价且无大跌预警。"

    print(status_msg)
    send_wechat_alert(status_msg)

if __name__ == '__main__':
    check_box_monitor()
