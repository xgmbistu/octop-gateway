"""Stable public API / data-contract surface for :mod:`octop_gateway`.

This package is the canonical implementation entry point for the gateway's
interface contract.  It re-exports the symbols that form the supported public
API so hosts can pin against a single import path::

    from octop_gateway.api import ChannelManager, InboundMessage, MessageEvent

The contract is documented in ``.wally/docs/apis/core/ChannelContract.md`` and
verified by ``tests/test_api_contracts.py``.  Re-exported names must stay in
sync with ``octop_gateway.__all__``.
"""

from __future__ import annotations

from octop_gateway.channel import (
    BaseChannel,
    ChannelConfig,
    ChannelCredentialsError,
    MessageProcessor,
)
from octop_gateway.channels import SUPPORTED_CHANNEL_KINDS, ChannelKind
from octop_gateway.manager import ChannelManager
from octop_gateway.media import FileSystemMediaBackend, MediaBackend
from octop_gateway.models import (
    AudioContent,
    ChannelSubject,
    ContentPart,
    ContentType,
    FileContent,
    GroupContext,
    GroupContextMessage,
    ImageContent,
    InboundMessage,
    MessageEvent,
    MessageEventType,
    TextContent,
    VideoContent,
)

__all__ = [
    "SUPPORTED_CHANNEL_KINDS",
    "AudioContent",
    "BaseChannel",
    "ChannelConfig",
    "ChannelCredentialsError",
    "ChannelKind",
    "ChannelManager",
    "ChannelSubject",
    "ContentPart",
    "ContentType",
    "FileContent",
    "FileSystemMediaBackend",
    "GroupContext",
    "GroupContextMessage",
    "ImageContent",
    "InboundMessage",
    "MediaBackend",
    "MessageEvent",
    "MessageEventType",
    "MessageProcessor",
    "TextContent",
    "VideoContent",
]
