import json

from rom_hub_sdk import FetchFile, FetchPlan, ImportProvider

from . import api


class Importer(ImportProvider):
    def __init__(self, ctx):
        self.ctx = ctx

    def _entry(self, torrent_id: int, file_id: int) -> dict:
        # The pinned map is authoritative rather than result.extra: `rom-hub
        # import <slug> "<tid>:<fid>"` builds a SearchResult whose title *is*
        # the source id, so trusting the caller's fields would name the file
        # "124376124:73" and the host would reject it.
        with open(self.ctx.data_asset("sets"), "rb") as handle:
            sets = json.load(handle)
        for platform in (sets.get("platforms") or {}).values():
            if platform.get("torrent_id") != torrent_id:
                continue
            for item in platform.get("files") or []:
                if item["id"] == file_id:
                    return item
        raise ValueError(f"torrent {torrent_id} file {file_id} is not in this plugin's set map")

    def plan(self, result) -> FetchPlan:
        torrent_id, _, file_id = result.source_id.partition(":")
        if not (torrent_id.isdigit() and file_id.isdigit()):
            raise ValueError(f"source_id must be '<torrent_id>:<file_id>', got {result.source_id!r}")

        item = self._entry(int(torrent_id), int(file_id))
        url = api.request_link(self.ctx, int(torrent_id), int(file_id))
        return FetchPlan(
            platform=result.platform or "",
            collection="TorBox",
            files=[FetchFile(url=url, filename=item["file"], size_bytes=item.get("size"))],
        )
