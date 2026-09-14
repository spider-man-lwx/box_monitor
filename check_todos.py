# 1. 打开我们刚才写的 todos.txt 文件
with open('todos.txt', 'r', encoding='utf-8') as file:
    lines = file.readlines()

# 2. 准备一个空篮子，用来装未完成的事情
unfinished_tasks = []

# 3. 开始逐行检查
for line in lines:
    # 如果这一行包含 '[ ]'（说明没完成）
    if '[ ]' in line:
        # 把这一行放进篮子里
        unfinished_tasks.append(line.strip())

# 4. 打印出来看看筛出来的结果
print("【您的今日未完成待办】")
for task in unfinished_tasks:
    print(task)
