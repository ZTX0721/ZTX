"""A2 验收测试:edit_todo 与 edit 子命令。

用法:
    1. 复制到 C:\\code\\hello-python\\test_edit.py
    2. 在 todo.py 里实现 edit_todo(),加 cmd_edit,并在 build_parser 里注册 edit
    3. 运行: python test_edit.py
"""
import os
import subprocess
import sys
import tempfile

from todo import edit_todo, load_todos, save_todos


def make_three() -> list[dict]:
    return [
        {"id": 1, "text": "买牛奶", "done": False, "created_at": "2026-10-21 02:00:01"},
        {"id": 2, "text": "复习 Git", "done": True, "created_at": "2026-10-21 02:00:02"},
        {"id": 3, "text": "跑步", "done": False, "created_at": "2026-10-21 02:00:03"},
    ]


def tmp_path(name: str = "todos.json") -> str:
    return os.path.join(tempfile.mkdtemp(), name)


# ---------- edit_todo 基础行为 ----------

def test_edit_basic() -> None:
    """改中间那条,返回 True,内容真的变了。"""
    todos = make_three()
    assert edit_todo(todos, 2, "复习 Git 进阶") is True
    assert todos[1]["text"] == "复习 Git 进阶", f"实际 {todos[1]['text']!r}"


def test_edit_preserves_other_fields() -> None:
    """★核心:只改 text,id / done / created_at 必须一字不动。"""
    todos = make_three()
    before = dict(todos[1])                 # 改之前的快照
    assert edit_todo(todos, 2, "新内容") is True
    after = todos[1]
    assert after["id"] == before["id"], "id 被改了"
    assert after["done"] == before["done"], "done 被改了(已完成状态必须保留)"
    assert after["created_at"] == before["created_at"], "created_at 被改了(创建时间不允许变)"
    assert after["text"] == "新内容"
    assert len(todos) == 3, "列表长度变了"


def test_edit_preserves_object_identity() -> None:
    """★必须原地改字典,不能替换成新字典。"""
    todos = make_three()
    original = todos[1]
    assert edit_todo(todos, 2, "改一下") is True
    assert todos[1] is original, "字典对象被替换了 -> 你写了 目标 = {...},应该写 目标['text'] = ..."


def test_edit_strips_whitespace() -> None:
    """两端空白要清掉。"""
    todos = make_three()
    assert edit_todo(todos, 1, "  买牛奶和鸡蛋  ") is True
    assert todos[0]["text"] == "买牛奶和鸡蛋", f"实际 {todos[0]['text']!r}"


def test_edit_not_found() -> None:
    """ID 不存在:返回 False,列表完全不变。"""
    todos = make_three()
    snapshot = [dict(t) for t in todos]
    assert edit_todo(todos, 99, "随便") is False
    assert todos == snapshot, "没找到时不允许改动任何东西"


def test_edit_empty_raises() -> None:
    """★空白内容必须抛 ValueError,且列表不能变。"""
    for bad in ["", "   ", "\t\n"]:
        todos = make_three()
        snapshot = [dict(t) for t in todos]
        try:
            edit_todo(todos, 1, bad)
        except ValueError:
            assert todos == snapshot, f"输入 {bad!r} 抛异常时不该改动列表"
            continue
        raise AssertionError(f"输入 {bad!r} 时必须抛 ValueError")


def test_edit_empty_list() -> None:
    """空列表:返回 False(不看内容是否为空?不,先校验内容)。"""
    todos: list[dict] = []
    # 内容合法但列表为空 -> False
    assert edit_todo(todos, 1, "正常内容") is False
    assert todos == []


def test_edit_first_and_last() -> None:
    """改第一条和最后一条。"""
    todos = make_three()
    assert edit_todo(todos, 1, "A") is True
    assert edit_todo(todos, 3, "C") is True
    assert todos[0]["text"] == "A"
    assert todos[2]["text"] == "C"
    assert todos[1]["text"] == "复习 Git", "中间那条不该被动"


def test_edit_same_text_twice() -> None:
    """改成相同内容也返回 True。"""
    todos = make_three()
    assert edit_todo(todos, 1, "买牛奶") is True
    assert todos[0]["text"] == "买牛奶"


def test_edit_does_not_change_done() -> None:
    """★把已完成的改成新内容,它仍然是已完成。"""
    todos = make_three()          # #2 是 done=True
    assert edit_todo(todos, 2, "完成过的任务改个名") is True
    assert todos[1]["done"] is True, "done 被重置成 False 了"


# ---------- 持久化 ----------

def test_edit_then_persist() -> None:
    """改完存盘,读回来是新内容。"""
    p = tmp_path()
    todos = make_three()
    save_todos(todos, p)
    loaded = load_todos(p)
    edit_todo(loaded, 2, "改过了")
    save_todos(loaded, p)
    again = load_todos(p)
    assert again[1]["text"] == "改过了", f"实际 {again[1]['text']!r}"
    assert again[1]["done"] is True, "持久化后 done 丢了"


# ---------- CLI ----------

def test_cli_edit() -> None:
    """真跑子进程:正常修改、找不到、空白内容三种情况。"""
    d = tempfile.mkdtemp()
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "todo.py")
    with open(src, encoding="utf-8") as f:
        code = f.read()
    with open(os.path.join(d, "todo.py"), "w", encoding="utf-8") as f:
        f.write(code)
    save_todos(make_three(), os.path.join(d, "todos.json"))

    env = dict(os.environ, PYTHONIOENCODING="utf-8")

    def run(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "todo.py", *args],
            cwd=d, capture_output=True, text=True,
            encoding="utf-8", env=env,
        )

    # 1. 正常修改
    r = run("edit", "2", "复习 Git 进阶")
    assert r.returncode == 0, f"退出码应为 0,实际 {r.returncode};stderr={r.stderr!r}"
    assert "已修改 #2" in r.stdout, f"输出应为「已修改 #2 ...」,实际 {r.stdout!r}"
    assert "复习 Git 进阶" in r.stdout, f"输出里应带新内容,实际 {r.stdout!r}"

    # 2. 确认真的改了,其他没动
    after = load_todos(os.path.join(d, "todos.json"))
    assert after[1]["text"] == "复习 Git 进阶", f"磁盘上实际 {after[1]['text']!r}"
    assert after[1]["done"] is True, "done 丢了"
    assert after[0]["text"] == "买牛奶", "别的待办被改了"

    # 3. 找不到
    r2 = run("edit", "99", "随便")
    assert r2.returncode == 1, f"找不到时退出码应为 1,实际 {r2.returncode}"
    assert "未找到 #99" in r2.stdout, f"实际 {r2.stdout!r}"

    # 4. ★空白内容必须优雅报错,不能 traceback
    r3 = run("edit", "1", "   ")
    assert r3.returncode == 1, f"空白内容退出码应为 1,实际 {r3.returncode}"
    assert "Traceback" not in r3.stdout and "Traceback" not in r3.stderr, \
        f"★不允许 traceback!stdout={r3.stdout!r} stderr={r3.stderr!r}"
    assert "不能为空" in r3.stdout, f"应提示内容不能为空,实际 {r3.stdout!r}"

    # 5. 报错后数据不能被改动
    final = load_todos(os.path.join(d, "todos.json"))
    assert final[0]["text"] == "买牛奶", "空白输入不该改动数据"


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
