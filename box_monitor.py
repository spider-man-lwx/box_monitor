import urllib.request
import json
import time
import datetime
import os

WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=8b2dd898-782b-49ec-8cf0-31fb70095f1a"
FALL_24H_THRESHOLD = 5.0   # 24小时内下跌超过 5% 触发告警
FALL_7D_THRESHOLD = 10.0   # 7天内下跌超过 10% 触发告警
COST_PRICE = 7.97          # 你的持仓均价（美元）
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
                    return float(asset.get('price_usd', 0))
    except Exception as e:
        print("获取价格出错：", e)
    return None

def check_box_monitor():
    price = fetch_box_price()
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
    
    # 保留最近 7 天的数据
    seven_days_ago = now - 7 * 24 * 3600
    history = [h for h in history if h['timestamp'] >= seven_days_ago]
    
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f)

    # 1. 计算 24 小时真实涨跌幅
    one_day_ago = now - 24 * 3600
    day_records = [h for h in history if h['timestamp'] <= one_day_ago + 3600]
    
    change_24h_pct = 0.0
    if day_records:
        old_price_24h = day_records[0]['price']
        change_24h_pct = ((price - old_price_24h) / old_price_24h) * 100

    # 2. 计算 7 天真实涨跌幅
    seven_records = [h for h in history if h['timestamp'] <= seven_days_ago + 3600]
    change_7d_pct = 0.0
    if seven_records:
        old_price_7d = seven_records[0]['price']
        change_7d_pct = ((price - old_price_7d) / old_price_7d) * 100

    # 检查各类告警条件
    alert_messages = []
    
    # 检查跌破买入均价
    if price < COST_PRICE:
        diff_pct = ((price - COST_PRICE) / COST_PRICE) * 100
        alert_messages.append(f"🚨 跌破持仓均价！当前现价 ${price:.4f} 已低于你的买入均价 ${COST_PRICE}（浮亏 {diff_pct:.2f}%）")

    # 检查 24h 暴跌
    if change_24h_pct <= -FALL_24H_THRESHOLD:
        alert_messages.append(f"⚠️ 24小时内暴跌！当前跌幅达到 {change_24h_pct:.2f}%（超过 5% 阈值）。")

    # 检查 7d 下跌
    if seven_records and change_7d_pct <= -FALL_7D_THRESHOLD:
        alert_messages.append(f"⚠️ 7天内累计下跌！当前 7 天跌幅达到 {change_7d_pct:.2f}%（超过 10% 阈值）。")

    # 组装推送消息
    profit_pct = ((price - COST_PRICE) / COST_PRICE) * 100
    status_msg = f"📊 BOX当前实时价格: ${price:.4f} USD\n"
    status_msg += f"💰 持仓均价: ${COST_PRICE} | 当前盈亏: {profit_pct:+.2f}%\n"
    status_msg += f"📈 24小时真实涨跌: {change_24h_pct:+.2f}%\n"
    
    if len(history) > 1 and seven_records:
        status_msg += f"📅 7天真实涨跌: {change_7d_pct:+.2f}%\n"
    
    if alert_messages:
        status_msg += "\n" + "\n".join(alert_messages)
    else:
        status_msg += "✅ 价格高于均价且无大跌预警，运行平稳。"

    print(status_msg)
    send_wechat_alert(status_msg)

if __name__ == '__main__':
    check_box_monitor()
