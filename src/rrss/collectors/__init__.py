"""Collectors de datos de redes sociales."""

from rrss.collectors.base import CollectorBase
from rrss.collectors.facebook import FacebookCollector
from rrss.collectors.instagram import InstagramCollector
from rrss.collectors.tiktok import TikTokCollector

__all__ = [
    "CollectorBase",
    "InstagramCollector",
    "FacebookCollector",
    "TikTokCollector",
]
