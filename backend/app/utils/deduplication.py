import hashlib


def compute_hash(title: str, url: str) -> str:
    content = f"{title.strip().lower()}|{url.strip()}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
