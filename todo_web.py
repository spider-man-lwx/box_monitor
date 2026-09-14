import urllib.request
import json
import datetime
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

TODO_FILE = 'todos.txt'
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=8b2dd898-782b-49ec-8cf0-31fb70095f1a"

def send_wechat_notification():
    tasks = load_tasks()
    lines = []
    for t in tasks:
        status = "[x]" if t['completed'] else "[ ]"
        lines.append(f"[{t['date']}] {status} {t['text']}")
    
    content = "【日历待办清单实时更新】\n" + "\n".join(lines) if lines else "【日历待办清单实时更新】\n当前暂无待办事项"
    
    payload = {
        "msgtype": "text",
        "text": {"content": content}
    }
    try:
        req_data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            WEBHOOK_URL, 
            data=req_data, 
            headers={'Content-Type': 'application/json'}
        )
        urllib.request.urlopen(req)
    except Exception as e:
        print("企业微信推送失败：", e)

# 🌙 高级、简约、富有质感的“暗黑极简/现代拟态”设计风格
HTML_TEMPLATE = '''
<!doctype html>
<html>
<head>
    <title>我的个人日历待办管家</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        :root {
            --bg-color: #0f1115;
            --card-bg: #181c24;
            --text-main: #f0f2f5;
            --text-muted: #8b949e;
            --accent: #58a6ff;
            --accent-hover: #1f6feb;
            --success: #3fb950;
            --danger: #f85149;
            --border: #30363d;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            max-width: 540px;
            margin: 0 auto;
            padding: 40px 20px;
            background-color: var(--bg-color);
            color: var(--text-main);
            -webkit-font-smoothing: antialiased;
        }
        h2 {
            font-size: 24px;
            font-weight: 600;
            letter-spacing: -0.5px;
            margin-bottom: 24px;
            color: var(--text-main);
            border-bottom: 1px solid var(--border);
            padding-bottom: 12px;
        }
        form {
            background-color: var(--card-bg);
            padding: 20px;
            border-radius: 12px;
            border: 1px solid var(--border);
            margin-bottom: 30px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.2);
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .form-row {
            display: flex;
            gap: 10px;
        }
        input[type="text"], input[type="date"] {
            background-color: #0d1117;
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text-main);
            padding: 12px 14px;
            font-size: 15px;
            outline: none;
            transition: border-color 0.2s;
        }
        input[type="text"] { flex: 1; }
        input[type="text"]:focus, input[type="date"]:focus {
            border-color: var(--accent);
        }
        button {
            background-color: var(--accent);
            color: #fff;
            border: none;
            border-radius: 8px;
            padding: 12px;
            font-size: 15px;
            font-weight: 500;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        button:hover {
            background-color: var(--accent-hover);
        }
        .date-group {
            margin-bottom: 24px;
        }
        .date-title {
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-muted);
            margin-bottom: 10px;
        }
        ul {
            list-style: none;
            padding: 0;
            margin: 0;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        li {
            background-color: var(--card-bg);
            padding: 16px;
            border-radius: 10px;
            border: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            transition: transform 0.1s;
        }
        li:active {
            transform: scale(0.99);
        }
        .task-info {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 15px;
            flex: 1;
            word-break: break-all;
        }
        .done {
            text-decoration: line-through;
            color: var(--text-muted);
            opacity: 0.7;
        }
        .action-btns {
            display: flex;
            gap: 8px;
        }
        a.btn {
            background-color: #21262d;
            color: var(--text-main);
            border: 1px solid var(--border);
            padding: 6px 12px;
            border-radius: 6px;
            text-decoration: none;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.2s;
        }
        a.btn.done-btn {
            background-color: rgba(63, 185, 80, 0.15);
            color: var(--success);
            border-color: rgba(63, 185, 80, 0.4);
        }
        a.btn.del-btn {
            background-color: rgba(248, 81, 73, 0.15);
            color: var(--danger);
            border-color: rgba(248, 81, 73, 0.4);
        }
        a.btn:hover {
            opacity: 0.85;
        }
    </style>
</head>
<body>
    <h2>📅 日历待办管家</h2>
    
    <form action="/add" method="POST">
        <div class="form-row">
            <input type="text" name="task_text" placeholder="输入新的待办事项..." required autocomplete="off">
            <input type="date" name="task_date" value="{{ today }}" required>
        </div>
        <button type="submit">添加任务</button>
    </form>

    {% for date_str, items in grouped_tasks.items() %}
    <div class="date-group">
        <div class="date-title">📌 {{ date_str }}</div>
        <ul>
            {% for item in items %}
            <li>
                <span class="task-info {% if item.task.completed %}done{% endif %}">
                    {% if item.task.completed %}✅{% else %}⬜{% endif %} {{ item.task.text }}
                </span>
                <div class="action-btns">
                    <a class="btn {% if item.task.completed %}done-btn{% endif %}" href="/toggle/{{ item.global_index }}">
                        {% if item.task.completed %}取消{% else %}完成{% endif %}
                    </a>
                    <a class="btn del-btn" href="/delete/{{ item.global_index }}" onclick="return confirm('确定要删除这个任务吗？');">删除</a>
                </div>
            </li>
            {% endfor %}
        </ul>
    </div>
    {% endfor %}
</body>
</html>
'''

def load_tasks():
    tasks = []
    today_str = datetime.date.today().isoformat()
    try:
        with open(TODO_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    if line.startswith('[') and ']' in line:
                        date_part = line[1:line.index(']')]
                        rest = line[line.index(']')+1:].strip()
                        if rest.startswith('[x]'):
                            tasks.append({'date': date_part, 'text': rest[3:].strip(), 'completed': True})
                        elif rest.startswith('[ ]'):
                            tasks.append({'date': date_part, 'text': rest[3:].strip(), 'completed': False})
                        else:
                            tasks.append({'date': date_part, 'text': rest, 'completed': False})
                    else:
                        if line.startswith('[x]'):
                            tasks.append({'date': today_str, 'text': line[3:].strip(), 'completed': True})
                        else:
                            text = line[3:].strip() if line.startswith('[ ]') else line
                            tasks.append({'date': today_str, 'text': text, 'completed': False})
    except FileNotFoundError:
        pass
    return tasks

def save_tasks(tasks):
    with open(TODO_FILE, 'w', encoding='utf-8') as f:
        for task in tasks:
            status = '[x]' if task['completed'] else '[ ]'
            f.write(f"[{task['date']}] {status} {task['text']}\n")

@app.route('/')
def index():
    tasks = load_tasks()
    today_str = datetime.date.today().isoformat()
    
    grouped = {}
    for idx, task in enumerate(tasks):
        d = task['date']
        if d not in grouped:
            grouped[d] = []
        grouped[d].append({'task': task, 'global_index': idx})
    
    sorted_grouped = dict(sorted(grouped.items()))
    return render_template_string(HTML_TEMPLATE, grouped_tasks=sorted_grouped, today=today_str)

@app.route('/add', methods=['POST'])
def add_task():
    new_text = request.form.get('task_text')
    new_date = request.form.get('task_date')
    if new_text and new_date:
        tasks = load_tasks()
        tasks.append({'date': new_date, 'text': new_text.strip(), 'completed': False})
        save_tasks(tasks)
        send_wechat_notification()
    return redirect(url_for('index'))

@app.route('/toggle/<int:index>')
def toggle(index):
    tasks = load_tasks()
    if 0 <= index < len(tasks):
        tasks[index]['completed'] = not tasks[index]['completed']
        save_tasks(tasks)
        send_wechat_notification()
    return redirect(url_for('index'))

@app.route('/delete/<int:index>')
def delete_task(index):
    tasks = load_tasks()
    if 0 <= index < len(tasks):
        tasks.pop(index)
        save_tasks(tasks)
        send_wechat_notification()
    return redirect(url_for('index'))

import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
