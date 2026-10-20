"""todo.py 的验收测试。全部通过才算完成第一课。

用法:
    1. 把这个文件保存为 C:\\code\\hello-python\\test_todo.py
    2. 在 todo.py 里实现 load_todos / save_todos / next_id / add_todo / mark_done
    3. 运行: python test_todo.py

不需要安装 pytest,直接 python test_todo.py 即可。
"""
import json
import os
import tempfile

from todo import load_todos, save_todos, next_id, add_todo, mark_done


def tmp_path(name: str = "todos.json") -> str:
    """生成一个临时文件路径,避免污染你的真实数据。"""
    return os.path.join(tempfile.mkdtemp(), name)


# ---------- load_todos / save_todos ----------

def test_load_missing_file() -> None:
    """文件不存在 -> 返回空列表,不报错。"""
    result = load_todos(tmp_path("不存在.json"))
    assert result == [], f"期望 [],实际 {result!r}"


def test_load_empty_file() -> None:
    """空文件 -> 返回空列表,不报错。"""
    p = tmp_path()
    open(p, "w", encoding="utf-8").close()
    result = load_todos(p)
    assert result == [], f"期望 [],实际 {result!r}"


def test_load_broken_json() -> None:
    """JSON 损坏 -> 抛 ValueError。"""
    p = tmp_path()
    with open(p, "w", encoding="utf-8") as f:
        f.write("{这不是合法 JSON")
    try:
        load_todos(p)
    except ValueError:
        return
    raise AssertionError("JSON 损坏时必须抛 ValueError")


def test_save_and_load_roundtrip() -> None:
    """存进去再读出来,数据必须一模一样。"""
    p = tmp_path()
    todos = [{"id": 1, "text": "买牛奶", "done": False,
              "created_at": "2026-10-17 01:30:00"}]
    save_todos(todos, p)
    result = load_todos(p)
    assert result == todos, f"往返后数据变了: {result!r}"


def test_save_is_human_readable() -> None:
    """文件必须是缩进的多行 JSON,且中文不转义。"""
    p = tmp_path()
    save_todos([{"id": 1, "text": "买牛奶", "done": False,
                 "created_at": "2026-10-17 01:30:00"}], p)
    raw = open(p, encoding="utf-8").read()
    assert "\n" in raw, "文件应该有多行(要有缩进)"
    assert "买牛奶" in raw, "中文被转义了,去查 json.dump 的参数"
    assert "\\u4e70" not in raw, "中文被转义成 \\uXXXX 了"


# ---------- next_id ----------

def test_next_id_basic() -> None:
    assert next_id([]) == 1, "空列表应该从 1 开始"


def test_next_id_after_delete() -> None:
    """★陷阱测试:删掉中间的待办后,新 ID 不能重复。"""
    assert next_id([{"id": 1}, {"id": 5}]) == 6, "应该取最大 id + 1"
    assert next_id([{"id": 3}]) == 4, "不能用列表长度算"


# ---------- add_todo ----------

def test_add_todo_returns_dict() -> None:
    todos = []
    result = add_todo(todos, "买牛奶")
    assert isinstance(result, dict), "必须返回字典"
    assert len(todos) == 1, "必须追加到原列表"
    assert todos[0] is result, "追加的应该是同一个对象"
    assert result["id"] == 1
    assert result["text"] == "买牛奶"
    assert result["done"] is False
    assert len(result["created_at"]) == 19, "时间格式应为 YYYY-MM-DD HH:MM:SS"


def test_add_todo_strips_whitespace() -> None:
    todos = []
    result = add_todo(todos, "  买牛奶  ")
    assert result["text"] == "买牛奶", f"没去掉空白: {result['text']!r}"


def test_add_todo_rejects_empty() -> None:
    """★空白内容必须抛 ValueError。"""
    for bad in ["", "   ", "\t\n"]:
        try:
            add_todo([], bad)
        except ValueError:
            continue
        raise AssertionError(f"输入 {bad!r} 时必须抛 ValueError")


def test_add_todo_increments_id() -> None:
    todos = []
    add_todo(todos, "第一条")
    add_todo(todos, "第二条")
    assert [t["id"] for t in todos] == [1, 2]


# ---------- mark_done ----------

def test_mark_done_found() -> None:
    todos = [{"id": 1, "text": "a", "done": False, "created_at": "x"},
             {"id": 2, "text": "b", "done": False, "created_at": "x"}]
    assert mark_done(todos, 2) is True
    assert todos[1]["done"] is True
    assert todos[0]["done"] is False, "不该动到别的待办"


def test_mark_done_not_found() -> None:
    todos = [{"id": 1, "text": "a", "done": False, "created_at": "x"}]
    assert mark_done(todos, 99) is False
    assert todos[0]["done"] is False


def test_mark_done_idempotent() -> None:
    """重复标记已完成的不应报错。"""
    todos = [{"id": 1, "text": "a", "done": True, "created_at": "x"}]
    assert mark_done(todos, 1) is True
    assert todos[0]["done"] is True


# ---------- 自制测试运行器(不需要 pytest) ----------

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
