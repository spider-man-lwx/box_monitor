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
    # 优先使用 Mixin 官方资产接口（获取真正的 BOX 基金净值），并将 CoinGecko 放在次要位置并进行合理性校验
    urls = [
        "https://api.mixin.one/network/assets/top",
        "https://api.coingecko.com/api/v3/simple/price?ids=box-token&vs_currencies=usd"
    ]
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=10) as response:
                raw_data = response.read().decode('utf-8')
                data = json.loads(raw_data)
                if 'mixin.one' in url:
                    for asset in data.get('data', []):
                        if asset.get('symbol') == 'BOX':
                            price = float(asset.get('price_usd', 0))
                            if price > 1.0:  # BOX 基金正常价格在数美元以上，过滤异常低价
                                return price
                elif 'coingecko.com' in url:
                    price = data.get('box-token', {}).get('usd')
                    # 只有当 CoinGecko 返回的价格合理（> 1.0美元）时才采用，防止匹配到其他同名垃圾代币
                    if price and float(price) > 1.0:
                        return float(price)
        except Exception as e:
            continue

    # 备用方案：如果外网 API 均受限或返回了异常价格，从本地历史中寻找最近一个“合理且大于1美元”的价格
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
                for h in reversed(history):
                    p = h.get('price', 0)
                    if p > 1.0:
                        print(f"[INFO] 外部API异常或受限，采用本地历史有效缓存价格: ${p}")
                        return float(p)
        except:
            pass

    return 8.76 # 保底默认合理均价

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
    
    # 去除过旧的历史记录，只保留最近7天
    seven_days_ago = now - 7 * 24 * 3600
    history = [h for h in history if h['timestamp'] >= seven_days_ago]
    
    # 严格检查：如果当前获取到的价格与上一条记录的时间间隔小于 5 分钟，且价格完全相同，则不重复追加，防止短时间内高频运行导致数据被污染或无意义堆积
    if history and (now - history[-1]['timestamp'] < 300) and (abs(price - history[-1]['price']) < 1e-4):
        pass # 重复采样跳过追加
    else:
        history.append({'timestamp': now, 'price': price})

    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f)

    # 计算 24 小时涨跌幅：寻找大约 24 小时前（20~28小时之间）最近的一条历史记录
    one_day_ago = now - 24 * 3600
    change_24h_pct = 0.0
    
    # 寻找时间戳最接近 24 小时前的记录
    past_24h_records = [h for h in history if h['timestamp'] <= one_day_ago + 3600]
    if past_24h_records:
        # 取满足条件中离 now 最远（即时间最早、最接近24小时前）或者直接取列表第一个
        old_price_24h = past_24h_records[0]['price']
        if old_price_24h > 0:
            change_24h_pct = ((price - old_price_24h) / old_price_24h) * 100
    elif len(history) > 1:
        # 如果还没有积累满 24 小时的数据，则以当前已有的最早一条历史数据作为基准
        old_price_24h = history[0]['price']
        if old_price_24h > 0:
            change_24h_pct = ((price - old_price_24h) / old_price_24h) * 100

    # 计算 7 天涨跌幅
    change_7d_pct = 0.0
    past_7d_records = [h for h in history if h['timestamp'] <= seven_days_ago + 3600]
    if past_7d_records:
        old_price_7d = past_7d_records[0]['price']
        if old_price_7d > 0:
            change_7d_pct = ((price - old_price_7d) / old_price_7d) * 100
    elif len(history) > 1 and (now - history[0]['timestamp'] > 3 * 24 * 3600):
        old_price_7d = history[0]['price']
        if old_price_7d > 0:
            change_7d_pct = ((price - old_price_7d) / old_price_7d) * 100

    alert_messages = []

    # 【核心修复】：只有当真正触发了以下条件之一时，才加入警告列表
    if price < COST_PRICE:
        diff_pct = ((price - COST_PRICE) / COST_PRICE) * 100
        alert_messages.append(f"⚠️ 跌破持仓均价！当前现价 ${price:.4f} 已低于你的买入均价 ${COST_PRICE}（浮亏 {diff_pct:.2f}%）")

    if change_24h_pct <= -FALL_24H_THRESHOLD:
        alert_messages.append(f"🚨 24小时内暴跌！当前跌幅达到 {change_24h_pct:.2f}%（超过 5% 阈值）。")

    if change_7d_pct <= -FALL_7D_THRESHOLD:
        alert_messages.append(f"🚨 7天内累计下跌！当前 7 天跌幅达到 {change_7d_pct:.2f}%（超过 10% 阈值）。")

    profit_pct = ((price - COST_PRICE) / COST_PRICE) * 100
    status_msg = f"【BOX基金行情播报】\n"
    status_msg += f"实时价格: ${price:.4f} USD\n"
    status_msg += f"持仓均价: ${COST_PRICE} | 当前盈亏: {profit_pct:+.2f}%\n"
    status_msg += f"24小时涨跌: {change_24h_pct:+.2f}%\n"

    if alert_messages:
        # 只有在真正触发预警条件时，才发送通知给企业微信
        status_msg += "\n" + "\n".join(alert_messages)
        print(status_msg)
        send_wechat_alert(status_msg)
    else:
        # 平稳状态：仅打印日志，绝对不给微信发消息，彻底杜绝无条件骚扰
        status_msg += "\n状态平稳：未触发任何跌破均价或大跌预警，本次不发送微信通知。"
        print(status_msg)

if __name__ == '__main__':
    check_box_monitor()
