import sqlite3

from pathlib import Path
from typing import Literal

MessageRole = Literal["user", "assistant"]

class ConversationMemory:
    def __init__(self, database_path: Path):     #database_path数据库文件的路径
        self.database_path = database_path

        self.database_path.parent.mkdir(    #parent数据库文件所在目录,mkdir创建目录
            parents=True,     #相当于将整条目录都创建,比如a/b/c/data，相当于一次建立a/b/c/data
            exist_ok=True,
        )

        self._initialize_database()    #初始化数据库表

    def _connect(self) -> sqlite3.Connection:   #创建并返回一个数据库连接
        return sqlite3.connect(self.database_path)

    def _initialize_database(self) -> None:   #初始化数据库表
        with self._connect() as connection:    #python的上下文管理器，进入with块自动打开数据库连接，离开with块自动提交事务并关闭连接
            connection.executescript(    #executescript执行sql语句
                """
                CREATE TABLE IF NOT EXISTS messages(      
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                        DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS
                    index_messages_session
                ON messages(session_id, id);
                """
            )
            """id 主键 每条消息唯一编号, session_id 会话id 用来区分不同会话, role 消息角色 只能是user or assistant"""
            """content 消息内容, created_at 创建时间 默认当前时间, text not null 文本字符串且不为空"""
            """INDEX是为session_id 和 id创建索引，加快按会话查询消息的速度"""

    def add_message(
            self,
            session_id: str,
            role: MessageRole,
            content: str,
    ) -> None:
        if role not in ("user", "assistant"):
            raise ValueError(f"不支持的消息角色: {role}")

        if not content.strip():     #content.strip()会去掉首尾空白只留中间字符串
            raise ValueError("消息内容不能为空")

        with self._connect() as connection:
            connection.execute(   #execute执行单挑SQL语句,insert插入数据,?是占位符，防止SQL注入
                """
                INSERT INTO messages(
                    session_id,
                    role,
                    content
                )
                VALUES (?, ?, ?)
                """,
                (
                    session_id,
                    role,
                    content,
                ),
            )

    def get_recent_messages(    #获取最近消息
            self,
            session_id: str,
            limit: int = 10,     #limit限制最多返回多少条，默认为10
    ) -> list[dict[str,str]]:
        safe_limit = max(1, min(limit, 50))

        with self._connect() as connection:
            rows = connection.execute(      #从对话中查询limit条消息，按标注的id进行降序排序
                """
                SELECT role, content
                FROM messages
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (
                    session_id,
                    safe_limit,
                ),
            ).fetchall()

        rows.reverse()   #因为id越大越新，这里进行反转，变成按时间从旧到新排列，方便阅读

        return [
            {
                "role": role,
                "content": content,
            }
            for role,content in rows
        ]

    def get_all_messages(    #获取所有对话，而不是最近limit条对话
            self,
            session_id: str,
    ) -> list[dict[str, str]]:
        with self._connect() as connection:
            rows = connection.execute(   #返回所有消息，按id升序排列，即从旧到新，并且多返回创建时间这个字段
                """
                SELECT role, content, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY id ASC
                """,
                (session_id,),
            ).fetchall()

        return[
            {
                "role": role,
                "content": content,
                "created_at": created_at,
            }
            for role,content,created_at in rows
        ]
    
    def clear_session(self, session_id: str) -> int:    #清空会话
        with self._connect() as connection:
            cursor = connection.execute(     #删除指定会话的所有消息
                """
                DELETE FROM messages
                WHERE session_id = ?
                """,
                (session_id,),
            )

            return cursor.rowcount     #返回被删除的所在行数，即一个数字



#   方法	                           作用
# __init__	                  初始化数据库路径，创建目录，建表
# _connect	                  连接数据库
# _initialize_database	      创建 messages 表和索引
# add_message	              添加一条消息
# get_recent_messages	      获取最近 N 条消息
# get_all_messages	          获取某会话的所有消息
# clear_session	              删除某会话的所有消息