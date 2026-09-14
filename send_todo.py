import urllib.request
import json

# 1. 打开 todos.txt 文件筛选未完成待办
with open('todos.txt', 'r', encoding='utf-8') as file:
    lines = file.readlines()

unfinished_tasks = []
for line in lines:
    if '[ ]' in line:
        unfinished_tasks.append(line.strip())

# 2. 拼装要发送的晨报内容
if unfinished_tasks:
    content = "【您的今日未完成待办晨报】\n" + "\n".join(unfinished_tasks)
else:
    content = "【您的今日未完成待办晨报】\n太棒了，所有待办都已完成！"

# 3. 准备发给企业微信的数据包
webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=8b2dd898-782b-49ec-8cf0-31fb70095f1a"
payload = {
    "msgtype": "text",
    "text": {
        "content": content
    }
}

# 4. 发送网络请求
req_data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(
    webhook_url, 
    data=req_data, 
    headers={'Content-Type': 'application/json'}
)

try:
    response = urllib.request.urlopen(req)
    result = response.read().decode('utf-8')
    print("推送结果：", result)
    print("成功！请检查您的企业微信，看看是否收到了待办晨报！")
except Exception as e:
    print("发送失败，错误原因：", e)
