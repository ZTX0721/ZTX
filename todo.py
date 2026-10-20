
import json
import os
import tempfile
from datetime import datetime

"""
文件不存在	返回空列表 [],不报错
文件是空文件(0 字节)	返回空列表 [],不报错
文件内容不是合法 JSON	抛出 ValueError,错误信息里要包含文件名
正常	返回解析后的列表
"""

def load_todos(path: str = "todos.json") -> list[dict]:
    if os.path.isfile(path):
        with open(path,'r', encoding="utf-8") as f:
            text = f.read()
        if not text.strip():
            return list()
        try:
            data = json.loads(text)
        except ValueError:
            raise ValueError(f"文件 {path} 不是合法的 JSON")
        if isinstance(data, list):
            return data
        else:
            return list()
    else:
        return list()

"""
写入 JSON	用 json.dump
缩进 2 空格	文件必须人眼可读,不能挤成一行
保留中文	文件里要看到 买牛奶,不是 \u4e70\u725b\u5976
返回值	None(不要 return 任何东西)
"""

def save_todos(todos: list[dict], path: str = "todos.json") -> None:
    with open(path, "w", encoding="utf-8") as f: 
        json.dump(todos, f, ensure_ascii=False, indent=2)

"""
[]	1
[{"id": 1}, {"id": 2}]	3
[{"id": 1}, {"id": 5}]	6
[{"id": 3}](删掉了 1 和 2)	4
"""

def next_id(todos: list[dict]) -> int:
    a=0
    for b in todos:
        c=b.get("id",0)
        if c>=a:
            a=c
    return a+1

"""
把新待办追加到 todos 列表末尾	直接修改传入的列表,不用返回新列表
返回新建的那个字典	
text 两端的空白要清掉	" 买牛奶 " → "买牛奶"
done 初始为 False	
created_at 用当前时间,格式 YYYY-MM-DD HH:MM:SS	
如果 text 清理后是空字符串	抛出 ValueError
"""

def add_todo(todos: list[dict], text: str) -> dict:
    if not text.strip():
        raise ValueError("待办内容不能为空")
    新增={
    "id": next_id(todos),
    "text": text.strip(),
    "done": bool(0),
    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    todos.append(新增)
    return 新增

"""
找到 ID 匹配的待办	把它的 done 改成 True	True
没找到	什么都不做	False
已经是 True 的再标记一次	保持 True	True
"""

def mark_done(todos: list[dict], todo_id: int) -> bool:
    todo_id = int(todo_id)
    if todo_id <= 0:
        raise ValueError("ID 应大于 0")
    for a in todos:
        if a.get("id") == todo_id:
            a["done"] = bool(1)
            return bool(1)
    return bool(0)
