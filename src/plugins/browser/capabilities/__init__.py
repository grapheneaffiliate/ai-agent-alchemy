"""Capability mixins used by the modular browser plugin."""

from .content import ContentExtractionMixin
from .interaction import InteractionMixin
from .navigation import NavigationMixin
from .news import NewsMixin

__all__ = [
    "ContentExtractionMixin",
    "InteractionMixin",
    "NavigationMixin",
    "NewsMixin",
]
