import re
import urllib.parse
from pathlib import Path

import pg8000
try:
    from mcp.server.fastmcp import FastMCP as MCPServer
    _KW = dict(name="supabase-readonly",
               instructions="Leitura read-only do Supabase do projeto (via role mcp_readonly). Nunca escreve.")
except ImportError:
    from mcp.server.mcpserver import MCPServer
    _KW = dict(name="supabase-readonly", version="1.0.0",
               description="Leitura read-only do Supabase do projeto (via role mcp_readonly). Nunca escreve.")

BASE = Path(__file__).resolve().parent
DSN_PATT = re.compile(r"^\w+://([^:]*):([^@]*)@([^:/]+)(?::(\d+))?/(\w+)$")
ALLOWED_KEYWORDS = ("SELECT", "WITH", "SHOW", "EXPLAIN", "DESCRIBE", "VALUES")

server = MCPServer(**_KW)


def _dsn():
    env = BASE / ".env"
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("PG_READONLY_DSN="):
            v = line.split("=", 1)[1].strip().strip('"').strip("'")
            if v:
                return v
    raise RuntimeError("PG_READONLY_DSN nao encontrado no .env")


def _connect():
    m = DSN_PATT.match(_dsn())
    if not m:
        raise ValueError("PG_READONLY_DSN malformada")
    user, pw = urllib.parse.unquote(m.group(1)), urllib.parse.unquote(m.group(2))
    host, port, db = m.group(3), int(m.group(4) or 5432), m.group(5)
    conn = pg8000.connect(host=host, port=port, database=db, user=user, password=pw, timeout=15)
    conn.cursor().execute("SET statement_timeout = 5000")
    return conn


def _guard(sql: str) -> str:
    stmt = sql.strip().rstrip(";").strip()
    if not stmt or ";" in stmt:
        raise ValueError("Somente UMA sentenca SELECT e permitida")
    kw = stmt.split(None, 1)[0].upper()
    if kw not in ALLOWED_KEYWORDS:
        raise ValueError(f"Somente leitura e permitida (nao: {kw[:20]})")
    return stmt


def _fmt(cols, rows, cap=100):
    lines = [" | ".join(cols or ())] + [" | ".join("" if c is None else str(c) for c in r) for r in rows[:cap]]
    if len(rows) > cap:
        lines.append(f"... ({len(rows) - cap} linhas suprimidas)")
    return "\n".join(lines) if lines else "(vazio)"


@server.tool()
def db_list_tables() -> str:
    """Lista as tabelas do schema public com a contagem de linhas de cada uma."""
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "select table_name from information_schema.tables "
            "where table_schema='public' and table_type='BASE TABLE' order by 1"
        )
        tables = [r[0] for r in cur.fetchall()]
        out = []
        for t in tables:
            cur.execute(f"select count(*) from {t}")
            out.append(f"{t}: {cur.fetchone()[0]}")
        return "; ".join(out) if out else "(nenhuma tabela)"
    finally:
        conn.close()


@server.tool()
def db_describe(table: str) -> str:
    """Descreve as colunas de uma tabela (nome, tipo, nullable)."""
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table):
        raise ValueError("Nome de tabela invalido")
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(
            "select column_name, data_type, is_nullable from information_schema.columns "
            "where table_schema='public' and table_name=%s order by ordinal_position",
            (table,),
        )
        rows = cur.fetchall()
        return _fmt(["coluna", "tipo", "nullable"], rows) if rows else "(tabela nao encontrada)"
    finally:
        conn.close()


@server.tool()
def db_query(sql: str) -> str:
    """Executa um SELECT read-only no banco e devolve o resultado (no maximo 1000 linhas)."""
    conn = _connect()
    try:
        try:
            stmt = _guard(sql)
        except ValueError as e:
            return f"(negado: {e})"
        cur = conn.cursor()
        cur.execute(stmt)
        cols = [d[0] for d in cur.description] or []
        rows = cur.fetchall()
        return _fmt(cols, rows, cap=1000)
    finally:
        conn.close()


if __name__ == "__main__":
    server.run()