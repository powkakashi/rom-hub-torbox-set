import json

from rom_hub_sdk import FetchFile, FetchPlan, ImportProvider

from . import api


class Importer(ImportProvider):
    def __init__(self, ctx):
        self.ctx = ctx

    def plan(self, result) -> FetchPlan:
        torrent_id, _, file_id = result.source_id.partition(":")
        if not file_id.isdigit() or not torrent_id.isdigit():
            raise ValueError(f"source_id must be '<torrent_id>:<file_id>', got {result.source_id!r}")

        url = api.request_link(self.ctx, int(torrent_id), int(file_id))
        name = result.extra.get("file") or f"{result.title}"
        return FetchPlan(
            platform=result.platform or "",
            collection="TorBox",
            files=[FetchFile(url=url, filename=name, size_bytes=result.size_bytes)],
        )
