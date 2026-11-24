"""Contract checks for the public gateway API and data models.

Verifies the entry points documented in
``.wally/docs/apis/core/ChannelContract.md`` and re-exported by
``octop_gateway.api``.
"""

from octop_gateway import api
from octop_gateway.models import (
    ContentType,
    InboundMessage,
    MessageEvent,
    MessageEventType,
    TextContent,
)


def test_public_api_exports_are_importable() -> None:
    """Every declared public symbol is resolvable from the API entry."""
    for name in api.__all__:
        assert getattr(api, name) is not None


def test_api_exports_match_top_level_package() -> None:
    """The stable API surface is a subset of the package's public symbols."""
    import octop_gateway

    assert set(api.__all__) <= set(octop_gateway.__all__)


def test_content_types_are_stable() -> None:
    """The discriminator values form the documented closed set."""
    assert [content_type.value for content_type in ContentType] == [
        "text",
        "image",
        "video",
        "audio",
        "file",
    ]


def test_message_event_types_cover_stream_contract() -> None:
    """Streaming, terminal and error semantics remain available."""
    assert {event_type.value for event_type in MessageEventType} >= {
        "message",
        "delta",
        "flush",
        "typing",
        "error",
        "completed",
    }


def test_message_event_factories() -> None:
    """Convenience constructors emit the documented event types."""
    assert MessageEvent.text("hi").type == MessageEventType.MESSAGE
    assert MessageEvent.delta("hi").type == MessageEventType.DELTA


def test_inbound_message_text_and_media_contract() -> None:
    """Inbound text is the joined content parts; media flag is derived."""
    message = InboundMessage(
        channel_id="channel-1",
        content=[TextContent(text="hello"), TextContent(text="world")],
    )
    assert message.text == "hello\nworld"
    assert message.has_media is False
