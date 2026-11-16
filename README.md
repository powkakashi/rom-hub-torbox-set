# TorBox sets — a ROM Hub plugin

Use a torrent set your TorBox account already holds as a ROMarr source. Search
returns one row per file inside the set; the importer asks TorBox for a direct
link to that single file, so the host downloads only the games you picked.

## Why the file list is generated, not fetched

TorBox's `torrents/mylist` needs `Authorization: Bearer <key>`. The Hub gives a
plugin `ctx.http`, which is GET-only with no headers, and TorBox refuses the
token in the query string (`token`, `apikey`, `api_key`, `key` all answer 401;
Bearer answers 200). So the plugin cannot enumerate a torrent itself. `sets.json`
is a [`[[data_assets]]`](https://github.com/) entry: the host fetches it, verifies
its sha256, and hands the plugin a path. Regenerating it is a one-off job, not a
daemon.

`requestdl` *does* take `token=` in the query, which is why the fetch half works.

## Install

    rom-hub plugin install https://github.com/powkakashi/rom-hub-torbox-set
    rom-hub plugin secret set torbox-set api_key --stdin

## Regenerate sets.json

Add the torrent to TorBox (its dashboard, or `POST /torrents/createtorrent`),
wait for `download_state: cached`, then:

    GET /v1/api/torrents/mylist?id=<torrent_id>       # Bearer auth
    -> write {platforms: {<hub slug>: {torrent_id, files: [{id,title,file,size}]}}}

Bump `sha256` and `size_bytes` in `manifest.toml`, push. The next search re-verifies
the asset, so a stale map fails loudly instead of serving wrong ids.
