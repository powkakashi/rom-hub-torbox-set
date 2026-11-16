"""TorBox as a ROMarr source: search a set the account already holds, fetch one file.

Why the file list is an asset rather than an API call: the Hub hands a plugin
`ctx.http`, which exposes only `get(url, params)` -- no headers. TorBox's
`torrents/mylist` requires `Authorization: Bearer` and refuses a token in the
query string, so a plugin cannot enumerate a torrent. `requestdl` does accept
`token=`, which is the one call made at fetch time.
"""
