"""The two API calls this plugin needs, and the reason each one is shaped that way."""

API = "https://api.torbox.app/v1/api/torrents/requestdl"


def _token(ctx) -> str:
    token = (ctx.config.get("api_key") or "").strip()
    if not token:
        raise ValueError("no TorBox API key: set the `api_key` secret for this plugin")
    return token


def request_link(ctx, torrent_id: int, file_id: int) -> str:
    """Ask TorBox for a direct link to one file of a cached torrent.

    `token=` in the query rather than a Bearer header: ctx.http is GET-only and
    header-less by design. TorBox accepts the token this way for requestdl
    (measured), though not for mylist.
    """
    response = ctx.http.get(
        API,
        {"token": _token(ctx), "torrent_id": torrent_id, "file_id": file_id},
    )
    if response.status_code != 200:
        raise RuntimeError(f"TorBox refused the download link ({response.status_code}): {response.text[:160]}")
    payload = response.json() if hasattr(response, "json") else _loads(response.text)
    if not payload.get("success"):
        raise RuntimeError(f"TorBox error: {payload.get('detail') or payload.get('error')}")
    link = payload.get("data")
    if not isinstance(link, str) or not link.startswith("https://"):
        raise RuntimeError(f"TorBox returned no https link: {str(link)[:120]}")
    return link


def _loads(text: str) -> dict:
    import json

    return json.loads(text)
