"""آپلود دانش در Supabase:   python ingest.py"""
import re
from pathlib import Path

from rag import db, embed, normalize

MAX_CHARS = 900


def split_body(body: str, max_chars: int) -> list[str]:
    units = []
    for block in re.split(r"\n\s*\n", body):
        if len(block) <= max_chars:
            units.append(block)
        else:  # بلوک خیلی بلند (مثل جدول) را سطر به سطر می‌شکنیم
            units += [line for line in block.split("\n") if line.strip()]
    out, cur = [], ""
    for u in units:
        if cur and len(cur) + len(u) + 1 > max_chars:
            out.append(cur)
            cur = u
        else:
            cur = f"{cur}\n{u}" if cur else u
    if cur:
        out.append(cur)
    return out


def make_chunks(text: str, max_chars: int = MAX_CHARS) -> list[tuple[str, str]]:
    """متن مارک‌داون را بر اساس هدینگ‌ها به (مسیر هدینگ، متن) تقسیم می‌کند."""
    stack: list[tuple[int, str]] = []
    sections: list[tuple[str, list[str]]] = [("", [])]
    for line in normalize(text).splitlines():
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            level, title = len(m.group(1)), m.group(2).strip()
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))
            sections.append((" > ".join(t for _, t in stack), []))
        else:
            sections[-1][1].append(line)
    chunks = []
    for heading, lines in sections:
        body = "\n".join(lines).strip()
        if body:
            chunks += [(heading, piece) for piece in split_body(body, max_chars)]
    return chunks


def main() -> None:
    rows = []
    for path in sorted(Path("data/knowledge").glob("*.md")):
        for heading, content in make_chunks(path.read_text(encoding="utf-8")):
            rows.append({"doc": path.name, "heading": heading, "content": content})
    print(f"{len(rows)} تکه ساخته شد. در حال embedding…")

    for i in range(0, len(rows), 32):
        part = rows[i : i + 32]
        for r, v in zip(part, embed([f"{r['heading']}\n{r['content']}" for r in part])):
            r["embedding"] = v
        print(f"  {min(i + 32, len(rows))}/{len(rows)}")

    db().table("chunks").delete().neq("id", 0).execute()  # پاک‌سازی نسخه‌ی قبلی
    for i in range(0, len(rows), 50):
        db().table("chunks").insert(rows[i : i + 50]).execute()
    print(f"انجام شد: {len(rows)} تکه در Supabase ذخیره شد.")


if __name__ == "__main__":
    main()
