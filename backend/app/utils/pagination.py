import base64
import json
from typing import Any, Callable, Sequence, TypeVar

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select


DEFAULT_CURSOR_LIMIT = 25
MAX_CURSOR_LIMIT = 100

T = TypeVar("T")


class CursorPage(BaseModel):
    items: list[Any]
    next_cursor: str | None = None
    has_more: bool = False
    limit: int = DEFAULT_CURSOR_LIMIT


def normalize_limit(limit: int | None, default: int = DEFAULT_CURSOR_LIMIT) -> int:
    if limit is None:
        return default
    return max(1, min(limit, MAX_CURSOR_LIMIT))


def encode_cursor(offset: int) -> str:
    payload = json.dumps({"offset": max(0, offset)}, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(payload).decode("utf-8")


def decode_cursor(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        payload = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
        data = json.loads(payload)
        return max(0, int(data.get("offset", 0)))
    except Exception:
        return 0


async def paginate_select(
    db: AsyncSession,
    stmt: Select,
    *,
    cursor: str | None = None,
    limit: int | None = None,
    serializer: Callable[[T], Any] | None = None,
    unique: bool = False,
) -> CursorPage:
    page_limit = normalize_limit(limit)
    offset = decode_cursor(cursor)
    result = await db.execute(stmt.offset(offset).limit(page_limit + 1))
    rows = result.unique().scalars().all() if unique else result.scalars().all()
    page_items = rows[:page_limit]
    has_more = len(rows) > page_limit
    items = [serializer(item) if serializer else item for item in page_items]
    next_cursor = encode_cursor(offset + page_limit) if has_more else None
    return CursorPage(
        items=items,
        next_cursor=next_cursor,
        has_more=has_more,
        limit=page_limit,
    )


def paginate_sequence(
    items: Sequence[T],
    *,
    cursor: str | None = None,
    limit: int | None = None,
    serializer: Callable[[T], Any] | None = None,
) -> CursorPage:
    page_limit = normalize_limit(limit)
    offset = decode_cursor(cursor)
    page_items = list(items[offset:offset + page_limit + 1])
    visible_items = page_items[:page_limit]
    has_more = len(page_items) > page_limit
    serialized = [serializer(item) if serializer else item for item in visible_items]
    next_cursor = encode_cursor(offset + page_limit) if has_more else None
    return CursorPage(
        items=serialized,
        next_cursor=next_cursor,
        has_more=has_more,
        limit=page_limit,
    )
