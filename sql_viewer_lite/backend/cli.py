#!/usr/bin/env python3
"""
SQL-Viewer Lite CLI - 命令行接口

提供非 GUI 的数据库操作功能，用于测试和自动化。
"""

import sys
import argparse
import csv
import json
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

from sql_viewer_lite.core.db_connection import (
    DatabaseConnection,
    DatabaseConnectionError,
    QueryError,
)
from sql_viewer_lite.models.connection import ConnectionConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class CLIError(Exception):
    """CLI 错误"""

    pass


class SQLViewerCLI:
    """SQL-Viewer Lite 命令行接口"""

    def __init__(self):
        self._db_connection = DatabaseConnection()
        self._config: Optional[ConnectionConfig] = None

    def connect(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: Optional[str] = None,
    ):
        """建立数据库连接"""
        self._config = ConnectionConfig(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
        )

        try:
            self._db_connection.connect(self._config)
            print(f"已连接到 {user}@{host}:{port}")
        except DatabaseConnectionError as e:
            raise CLIError(f"连接失败: {e}")

    def disconnect(self):
        """断开连接"""
        self._db_connection.disconnect()

    def list_databases(self):
        """列出所有数据库"""
        try:
            databases = self._db_connection.get_databases()
            print(f"\n数据库列表 ({len(databases)} 个):")
            print("-" * 40)
            for db in databases:
                print(f"  {db}")
            print()
        except QueryError as e:
            raise CLIError(f"获取数据库列表失败: {e}")

    def list_tables(self, database: str):
        """列出指定数据库的表"""
        try:
            tables = self._db_connection.get_tables(database)
            print(f"\n数据库 {database} 的表 ({len(tables)} 个):")
            print("-" * 60)
            print(f"{'表名':<30} {'行数':>10} {'引擎':<10}")
            print("-" * 60)
            for table in tables:
                name = table.get("name", "")
                rows = table.get("rows", 0)
                engine = table.get("engine", "")
                print(f"{name:<30} {rows:>10} {engine:<10}")
            print()
        except QueryError as e:
            raise CLIError(f"获取表列表失败: {e}")

    def execute_query(self, sql: str, output_format: str = "table"):
        """执行 SQL 查询"""
        try:
            result, row_count, message = self._db_connection.execute_query(sql)

            if result is not None:
                print(f"\n{message}")
                if result:
                    self._print_result(result, output_format)
                else:
                    print("(无结果)")
            else:
                print(f"\n{message}")

        except QueryError as e:
            raise CLIError(f"查询执行失败: {e}")

    def export_data(self, sql: str, output_file: str, output_format: str = "csv"):
        """导出查询结果到文件"""
        try:
            result, row_count, message = self._db_connection.execute_query(sql)

            if result is None:
                raise CLIError("查询没有返回结果")

            output_path = Path(output_file)

            if output_format == "csv":
                self._export_csv(result, output_path)
            elif output_format == "json":
                self._export_json(result, output_path)
            elif output_format == "sql":
                self._export_sql(result, output_path, sql)
            else:
                raise CLIError(f"不支持的输出格式: {output_format}")

            print(f"\n已导出 {row_count} 行到 {output_file} ({output_format})")

        except QueryError as e:
            raise CLIError(f"导出失败: {e}")

    def _print_result(self, result: List[Dict[str, Any]], output_format: str):
        """打印查询结果"""
        if not result:
            return

        if output_format == "table":
            self._print_table(result)
        elif output_format == "csv":
            self._print_csv(result)
        elif output_format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            self._print_table(result)

    def _print_table(self, result: List[Dict[str, Any]]):
        """以表格形式打印"""
        if not result:
            return

        columns = list(result[0].keys())

        # 计算列宽
        col_widths = {}
        for col in columns:
            col_widths[col] = max(
                len(str(col)), max(len(str(row.get(col, ""))) for row in result)
            )

        # 打印表头
        header = " | ".join(str(col).ljust(col_widths[col]) for col in columns)
        print(header)
        print("-" * len(header))

        # 打印数据行
        for row in result:
            line = " | ".join(
                str(row.get(col, "")).ljust(col_widths[col]) for col in columns
            )
            print(line)

    def _print_csv(self, result: List[Dict[str, Any]]):
        """以 CSV 格式打印"""
        if not result:
            return

        columns = list(result[0].keys())

        # 打印表头
        print(",".join(columns))

        # 打印数据
        for row in result:
            values = []
            for col in columns:
                value = str(row.get(col, ""))
                if "," in value or '"' in value:
                    value = f'"{value}"'
                values.append(value)
            print(",".join(values))

    def _export_csv(self, result: List[Dict[str, Any]], output_path: Path):
        """导出为 CSV 文件"""
        if not result:
            return

        columns = list(result[0].keys())

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(result)

    def _export_json(self, result: List[Dict[str, Any]], output_path: Path):
        """导出为 JSON 文件"""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    def _export_sql(
        self, result: List[Dict[str, Any]], output_path: Path, original_sql: str
    ):
        """导出为 SQL INSERT 语句"""
        if not result:
            return

        # 从原始 SQL 中提取表名（简化处理）
        table_name = "exported_data"

        columns = list(result[0].keys())

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"-- SQL-Viewer Lite 导出\n")
            f.write(f"-- 原始查询: {original_sql}\n")
            f.write(f"-- 行数: {len(result)}\n\n")

            for row in result:
                values = []
                for col in columns:
                    value = row.get(col)
                    if value is None:
                        values.append("NULL")
                    else:
                        # 转义单引号防 SQL 注入
                        escaped = str(value).replace("'", "''")
                        values.append(f"'{escaped}'")

                columns_str = ", ".join([f"`{col}`" for col in columns])
                values_str = ", ".join(values)
                f.write(
                    f"INSERT INTO `{table_name}` ({columns_str}) VALUES ({values_str});\n"
                )


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog="sql-viewer-cli",
        description="SQL-Viewer Lite 命令行接口",
    )

    # 连接参数
    parser.add_argument(
        "--host", default="localhost", help="数据库主机 (默认: localhost)"
    )
    parser.add_argument(
        "--port", type=int, default=3306, help="数据库端口 (默认: 3306)"
    )
    parser.add_argument("--user", "-u", required=True, help="数据库用户名")
    parser.add_argument("--password", "-p", required=True, help="数据库密码")
    parser.add_argument("--database", "-d", help="默认数据库")

    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # list-db 命令
    subparsers.add_parser("list-db", help="列出所有数据库")

    # list-tables 命令
    list_tables_parser = subparsers.add_parser("list-tables", help="列出指定数据库的表")
    list_tables_parser.add_argument("database", help="数据库名")

    # query 命令
    query_parser = subparsers.add_parser("query", help="执行 SQL 查询")
    query_parser.add_argument("sql", help="SQL 语句")
    query_parser.add_argument(
        "--format", choices=["table", "csv", "json"], default="table", help="输出格式"
    )

    # export 命令
    export_parser = subparsers.add_parser("export", help="导出查询结果到文件")
    export_parser.add_argument("sql", help="SQL 查询语句")
    export_parser.add_argument("--output", "-o", required=True, help="输出文件路径")
    export_parser.add_argument(
        "--format", choices=["csv", "json", "sql"], default="csv", help="输出格式"
    )

    return parser


def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    cli = SQLViewerCLI()

    try:
        # 连接数据库
        cli.connect(args.host, args.port, args.user, args.password, args.database)

        # 执行命令
        if args.command == "list-db":
            cli.list_databases()

        elif args.command == "list-tables":
            cli.list_tables(args.database)

        elif args.command == "query":
            cli.execute_query(args.sql, args.format)

        elif args.command == "export":
            cli.export_data(args.sql, args.output, args.format)

        else:
            parser.print_help()

    except CLIError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.exit(0)

    finally:
        cli.disconnect()


if __name__ == "__main__":
    main()
