from collections import defaultdict

from django.conf import settings

from .constants import ApiPath


class HostAllowList:
    @staticmethod
    def extend(hosts: list[str], *extra: str | None) -> list[str]:
        allowed = list(hosts)
        for host in extra:
            if host and host not in allowed:
                allowed.append(host)
        return allowed


class ScriptPrefix:
    @classmethod
    def configured(cls) -> str:
        return (getattr(settings, "FORCE_SCRIPT_NAME", None) or "").strip("/")

    @classmethod
    def public_prefixes(cls) -> list[str]:
        prefixes = [ApiPath.SCRIPT_PREFIX]
        configured = cls.configured()
        if configured and configured not in prefixes:
            prefixes.append(configured)
        return prefixes

    @classmethod
    def openapi_root(cls) -> str:
        """Public prefix Ninja prepends to operation paths.

        FORCE_SCRIPT_NAME already includes ``/api``, so OpenAPI must mount at
        ``/v1`` under that script name, not ``/api/v1``.
        """
        configured = cls.configured()
        if configured:
            return f"{configured}/{ApiPath.VERSION}"
        return ApiPath.ROOT


class OrderedUniqueMap:
    """Preserve first-seen order of values grouped by key."""

    def __init__(self) -> None:
        self._items: dict[str, list[str]] = {}
        self._seen: dict[str, set[str]] = defaultdict(set)

    def add(self, key: str, value: str) -> None:
        if not value or value in self._seen[key]:
            return
        self._seen[key].add(value)
        self._items.setdefault(key, []).append(value)

    def as_dict(self) -> dict[str, list[str]]:
        return self._items
