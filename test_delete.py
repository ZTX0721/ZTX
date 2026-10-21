"""A1 验收测试:delete_todo 与 delete 子命令。

用法:
    1. 复制到 C:\\code\\hello-python\\test_delete.py
    2. 在 todo.py 里实现 delete_todo(),并在 build_parser 里加 delete 子命令
    3. 运行: python test_delete.py

不需要 pytest。
"""
import json
import os
import subprocess
import sys
import tempfile

from todo import delete_todo, load_todos, save_todos, add_todo, next_id


def tmp_path(name: str = "todos.json") -> str:
    return os.path.join(tempfile.mkdtemp(), name)


def make_three() -> list[dict]:
    """造三条待办,id = 1, 2, 3。"""
    return [
        {"id": 1, "text": "买牛奶", "done": False, "created_at": "2026-10-21 02:00:01"},
        {"id": 2, "text": "复习 Git", "done": True, "created_at": "2026-10-21 02:00:02"},
        {"id": 3, "text": "跑步", "done": False, "created_at": "2026-10-21 02:00:03"},
    ]


# ---------- delete_todo ----------

def test_delete_middle() -> None:
    """删中间那条:id,2 消失,1 和 3 原样保留。"""
    todos = make_three()
    assert delete_todo(todos, 2) is True, "找到了就必须返回 True"
    assert len(todos) == 2, f"删完应该剩 2 条,实际 {len(todos)}"
    ids = [t["id"] for t in todos]
    assert ids == [1, 3], f"剩下的应该是 [1, 3],实际 {ids}"
    assert todos[0]["text"] == "买牛奶", "第一条的内容被动了"
    assert todos[1]["text"] == "跑步", "第三条的内容被动了"


def test_delete_first() -> None:
    """删第一条。"""
    todos = make_three()
    assert delete_todo(todos, 1) is True
    assert [t["id"] for t in todos] == [2, 3], f"实际 {[t['id'] for t in todos]}"


def test_delete_last() -> None:
    """删最后一条。"""
    todos = make_three()
    assert delete_todo(todos, 3) is True
    assert [t["id"] for t in todos] == [1, 2], f"实际 {[t['id'] for t in todos]}"


def test_delete_not_found() -> None:
    """ID 不存在:返回 False,列表一个字节都不能变。"""
    todos = make_three()
    snapshot = [dict(t) for t in todos]
    assert delete_todo(todos, 99) is False, "没找到必须返回 False"
    assert todos == snapshot, "没找到时不允许改动列表"


def test_delete_empty_list() -> None:
    """空列表:返回 False,不能崩。"""
    todos: list[dict] = []
    assert delete_todo(todos, 1) is False
    assert todos == []


def test_delete_only_item() -> None:
    """只有一条时删掉它。"""
    todos = [dict(make_three()[0])]
    assert delete_todo(todos, 1) is True
    assert todos == [], f"应该变成空列表,实际 {todos!r}"


def test_delete_modifies_in_place() -> None:
    """★必须原地修改:同一个列表对象,不能返回新列表。"""
    todos = make_three()
    original_id = id(todos)
    result = delete_todo(todos, 2)
    assert result is True
    assert id(todos) == original_id, "list 的 id 变了 -> 你重建了新列表,应该原地改"


def test_delete_all() -> None:
    """连续删光所有三条。"""
    todos = make_three()
    for tid in (1, 2, 3):
        assert delete_todo(todos, tid) is True, f"删除 #{tid} 失败"
    assert todos == [], f"全删完应为空,实际 {todos!r}"


# ---------- 删完之后 next_id 不能重复 ----------

def test_next_id_after_delete_no_collision() -> None:
    """★这是 A1 的核心验收:删除后新增的 ID 不能和现有的撞。"""
    todos = make_three()          # id 1,2,3
    delete_todo(todos, 2)         # 剩 1,3
    new = add_todo(todos, "新任务")
    assert new["id"] == 4, f"新 ID 应为 4(最大 3 + 1),实际 {new['id']}"
    ids = [t["id"] for t in todos]
    assert len(ids) == len(set(ids)), f"ID 出现重复: {ids}"


def test_delete_all_then_add() -> None:
    """全删完之后新增,ID 应该重新从 1 开始。"""
    todos = make_three()
    for tid in (1, 2, 3):
        delete_todo(todos, tid)
    new = add_todo(todos, "重新开始")
    assert new["id"] == 1, f"空列表新增应为 1,实际 {new['id']}"


# ---------- 持久化:删完存盘再读回来 ----------

def test_delete_then_persist() -> None:
    """删完存盘,读回来还是删掉的状态。"""
    p = tmp_path()
    todos = make_three()
    save_todos(todos, p)
    loaded = load_todos(p)
    delete_todo(loaded, 2)
    save_todos(loaded, p)
    again = load_todos(p)
    assert [t["id"] for t in again] == [1, 3], f"实际 {[t['id'] for t in again]}"


# ---------- CLI 集成 ----------

def test_cli_delete() -> None:
    """真跑子进程,验证命令行输出和退出码。"""
    d = tempfile.mkdtemp()
    script = os.path.join(d, "todo.py")
    # 找到真实的 todo.py
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "todo.py")
    with open(src, encoding="utf-8") as f:
        code = f.read()
    with open(script, "w", encoding="utf-8") as f:
        f.write(code)
    # 造数据
    save_todos(make_three(), os.path.join(d, "todos.json"))

    def run(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "todo.py", *args],
                              cwd=d, capture_output=True, text=True, encoding="utf-8")

    r = run("delete", "2")
    assert r.returncode == 0, f"退出码应为 0,实际 {r.returncode};stderr={r.stderr!r}"
    assert "已删除 #2" in r.stdout, f"输出里应有「已删除 #2」,实际 {r.stdout!r}"

    r2 = run("list")
    assert "#1" in r2.stdout and "#3" in r2.stdout, f"list 应还有 1 和 3:{r2.stdout!r}"
    assert "#2" not in r2.stdout, f"#2 应已被删除:{r2.stdout!r}"

    r3 = run("delete", "99")
    assert r3.returncode == 1, f"找不到时退出码应为 1,实际 {r3.returncode}"
    assert "未找到 #99" in r3.stdout, f"输出里应有「未找到 #99」,实际 {r3.stdout!r}"


# ---------- 运行器 ----------

if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    failed = []
    for t in tests:
        try:
            t()
            print(f"  通过  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"★ 失败  {t.__name__}: {e}")
            failed.append(t.__name__)
        except Exception as e:
            print(f"★ 崩溃  {t.__name__}: {type(e).__name__}: {e}")
            failed.append(t.__name__)
    print(f"\n{passed}/{len(tests)} 通过")
    if failed:
        print("未通过: " + ", ".join(failed))
