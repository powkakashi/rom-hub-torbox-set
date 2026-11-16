import json
import re

from rom_hub_sdk import SearchProvider, SearchResult

# Region/tag noise that a query never contains but a filename always does.
_TAGS = re.compile(r"\((?:usa|europe|japan|world|asia|korea|china|brazil|australia)[^)]*\)", re.I)
_NONWORD = re.compile(r"[^a-z0-9]+")


def _norm(text: str) -> str:
    return _NONWORD.sub(" ", _TAGS.sub(" ", text).casefold()).strip()


class Search(SearchProvider):
    def __init__(self, ctx):
        self.ctx = ctx

    def _sets(self) -> dict:
        with open(self.ctx.data_asset("sets"), "rb") as handle:
            return json.load(handle)

    def search(self, query: str, platform: str | None, limit: int) -> list[SearchResult]:
        if not platform:
            # no platform means no set to look in; the Hub scores on platform
            # evidence anyway, so an answer here would be noise
            return []
        entry = (self._sets().get("platforms") or {}).get(platform)
        if not entry:
            return []
        wanted = _norm(query)
        if not wanted:
            return []

        rows = []
        for item in entry.get("files") or []:
            haystack = _norm(item["title"])
            if wanted not in haystack:
                continue
            # exact-ish matches first: a query that equals the title beats one
            # that merely contains it, which is what makes "Ai Chou Aniki" win
            # over "Ai Chou Aniki Special" without the host having to re-rank
            rows.append((haystack != wanted, len(haystack), item))
        rows.sort(key=lambda row: (row[0], row[1]))

        cap = min(int(self.ctx.config.get("max_rows") or 20), limit)
        return [
            SearchResult(
                source_id=f"{entry['torrent_id']}:{item['id']}",
                title=item["title"],
                platform=platform,
                size_bytes=item["size"],
                extra={"torrent": str(entry["torrent_id"]), "file": item["file"]},
            )
            for _, _, item in rows[:cap]
        ]
