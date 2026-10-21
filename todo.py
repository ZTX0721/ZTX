
import json
import os
import tempfile
from datetime import datetime
import argparse
import sys

#处理函数

"""读取 JSON 文件,返回列表
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

"""写入 JSON 文件,把 todos 列表写入 path 指定的文件
写入 JSON	用 json.dump
缩进 2 空格	文件必须人眼可读,不能挤成一行
保留中文	文件里要看到 买牛奶,不是 \u4e70\u725b\u5976
返回值	None(不要 return 任何东西)
"""
def save_todos(todos: list[dict], path: str = "todos.json") -> None:
    with open(path, "w", encoding="utf-8") as f: 
        json.dump(todos, f, ensure_ascii=False, indent=2)

"""获取下一个待办 ID
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

"""添加新待办事项
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

"""修改待办事项的 done 状态
找到 ID 匹配的待办	把它的 done 改成 True	True
没找到	什么都不做	False
已经是 True 的再标记一次	保持 True	True
"""
def mark_done(todos: list[dict], todo_id: int) -> bool:
    for a in todos:
        if a.get("id") == todo_id:
            a["done"] = bool(1)
            return bool(1)
    return bool(0)

"""从列表中删除指定 ID 的待办。
找到该 ID	从列表里删掉这一条，其他条目原封不动	True
没找到	列表一个字节都不能变	False
空列表	不报错	False
删掉中间那条	剩下的 ID 不变（不是重新编号！）	True
"""
def delete_todo(todos: list[dict], todo_id: int) -> bool:
    for a in todos:
        if a.get("id") == todo_id:
            todos.remove(a)
            return bool(1)
    return bool(0)

#处理命令

def cmd_add(args) -> int:
    原列表=load_todos()
    添加字典=add_todo(原列表, args.text)
    save_todos(原列表)
    print(f"已添加 #{添加字典['id']}: {添加字典['text']}")
    return 0
"""处理 add 子命令。
 1. 读数据(load_todos)
 2. 调 add_todo
 3. 保存(save_todos)
 4. 打印 "已添加 #id: text"
 5. 返回 0
"""

def cmd_list(args) -> int:
    原列表=load_todos()
    if not 原列表:
        print("还没有待办事项")
    else:
        for a in 原列表:
            状态="[x]" if a.get("done") else "[ ]"
            print(f"{状态} #{a.get('id')}: {a.get('text')}")
    return 0
"""处理 list 子命令。
1. 读数据
2. 空 → 打印 "还没有待办事项"
3. 非空 → 逐条打印 "[ ] #1 xxx" 或 "[x] #1 xxx"
4. 返回 0
"""

def cmd_done(args) -> int:
    if args.id <= 0:
        print("ID 应大于 0")
        return 1
    原列表=load_todos()
    目标 = next((t for t in 原列表 if t.get("id") == args.id), None)
    if 目标 is None:
        print(f"未找到 #{args.id}")
        return 1
    else:
        mark_done(原列表, args.id)
        save_todos(原列表)
        print(f"已完成 #{args.id}: {目标.get('text')}")
        return 0
"""处理 done 子命令。
1. 读数据
2. 调 mark_done
3. 成功 → 保存 + 打印 "已完成 #id"
4. 失败 → 打印 "未找到 #id", 返回 1
"""

def cmd_delete(args) -> int:
    if args.id <= 0:
        print("ID 应大于 0")
        return 1
    原列表=load_todos()
    目标 = next((t for t in 原列表 if t.get("id") == args.id), None)
    if 目标 is None:
        print(f"未找到 #{args.id}")
        return 1
    else:
        delete_todo(原列表, args.id)
        save_todos(原列表)
        print(f"已删除 #{args.id}: {目标.get('text')}")
        return 0
"""处理 delete 子命令
"""


def build_parser() -> argparse.ArgumentParser:
    """构造命令行解析器。"""
    解析器 = argparse.ArgumentParser(prog="代办事项管理", description="命令行待办事项工具")
    子命令支持=解析器.add_subparsers(title="子命令列表", dest="cmd")

    子命令_add = 子命令支持.add_parser('add', help='添加一条待办')
    子命令_add.add_argument("text", help="待办内容") 
    子命令_add.set_defaults(func=cmd_add)

    子命令_list = 子命令支持.add_parser('list', help='查看所有事项')
    子命令_list.set_defaults(func=cmd_list)

    子命令_done = 子命令支持.add_parser('done', help='标记事项为完成')
    子命令_done.add_argument("id", type=int, help="待办编号")
    子命令_done.set_defaults(func=cmd_done)

    子命令_delete = 子命令支持.add_parser('delete', help='删除事项')
    子命令_delete.add_argument("id", type=int, help="待删除编号")
    子命令_delete.set_defaults(func=cmd_delete)

    return 解析器


def main(argv: list[str] | None = None) -> int:
    解析器 = build_parser()
    args = 解析器.parse_args(argv)
    if not hasattr(args, "func"):
        解析器.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
