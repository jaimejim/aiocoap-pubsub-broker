"""Shared CBOR codec for CoAP PubSub (draft-ietf-core-coap-pubsub-19)."""

import cbor2

TOPIC_KEYS: dict[str, int] = {
    "topic-name":           0,
    "topic-data":           1,
    "resource-type":        2,
    "topic-content-format": 3,
    "topic-type":           4,
    "expiration-date":      5,
    "max-subscribers":      6,
    "observer-check":       7,
    "initialize":           8,
    "conf-filter":          10,
}
TOPIC_KEYS_REV: dict[int, str] = {v: k for k, v in TOPIC_KEYS.items()}

CT_PUBSUB_CBOR = 606
CT_JSON = 50
CT_LINK_FORMAT = 40

IMMUTABLE_FIELDS = {"topic-name", "topic-data", "resource-type"}


def decode_topic_payload(payload: bytes, content_format: int | None = None) -> dict:
    """Decode a topic config payload (CBOR with numeric keys, or JSON fallback)."""
    if content_format == CT_PUBSUB_CBOR:
        raw = cbor2.loads(payload)
        result = {}
        for k, v in raw.items():
            name = TOPIC_KEYS_REV.get(k, str(k))
            if name == "expiration-date" and isinstance(v, cbor2.CBORTag) and v.tag == 1:
                v = v.value
            result[name] = v
        return result
    import json
    return json.loads(payload)


def encode_topic_config(d: dict) -> bytes:
    """Encode a topic config dict to CBOR with numeric keys."""
    cbor_map = {}
    for name, value in d.items():
        if value is None:
            continue
        key = TOPIC_KEYS.get(name)
        if key is None:
            continue
        if name == "expiration-date":
            value = cbor2.CBORTag(1, int(value))
        cbor_map[key] = value
    return cbor2.dumps(cbor_map)
