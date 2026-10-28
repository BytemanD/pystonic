import sqlite3
from typing import Any

from langchain_core.tools import tool


@tool
def execute_sql(
    db_path: str, sql: str, parameters: tuple[Any, ...] = ()
) -> dict[str, Any]:
    """SQLite 查询工具

    执行任意 SQL 语句（SELECT / INSERT / UPDATE / DELETE / CREATE TABLE 等）。
    自动提交事务，如果尚未连接则自动连接内存数据库。

    Args:
        db_path: 数据库文件路径
        sql: SQL 语句，使用 ? 或 :name 占位符防止注入
        parameters: 可选参数，与占位符匹配

    Returns:
        - 对于 SELECT 语句：返回 {"rows": [...]}
        - 对于非 SELECT 语句：返回 {"affected_rows": 影响行数, "last_row_id": 最后插入行的ID（若适用）}

    Example:
        execute_sql("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        execute_sql("INSERT INTO users (name) VALUES (?)", ("Alice",))
        result = execute_sql("SELECT * FROM users")  # 得到查询结果
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()
    try:
        cursor.execute(sql, parameters or ())

        # 判断是否是 SELECT 查询
        if sql.strip().upper().startswith("SELECT"):
            return {"rows": [dict(x) for x in cursor.fetchall()]}
        else:
            conn.commit()
            last_id = cursor.lastrowid
            return {
                "affected_rows": cursor.rowcount,
                "last_row_id": last_id if last_id != 0 else None,
            }
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"SQL execution failed: {e}") from e
