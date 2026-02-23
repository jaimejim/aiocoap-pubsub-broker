#!/usr/bin/env python3

# CoAP Publish-Subscribe Broker — draft-ietf-core-coap-pubsub-19
# Jaime Jiménez <jaimejim@gmail.com>
# Built on aiocoap by Christian Amsüss

import argparse
import asyncio
import logging
import secrets

import aiocoap
import aiocoap.resource as resource
import cbor2
from aiocoap import Message

from codec import (
    TOPIC_KEYS, TOPIC_KEYS_REV,
    CT_PUBSUB_CBOR, CT_LINK_FORMAT,
    IMMUTABLE_FIELDS,
    decode_topic_payload, encode_topic_config,
)


# ---------------------------------------------------------------------------
# CollectionResource  (/ps)
# ---------------------------------------------------------------------------

class CollectionResource(resource.Resource):

    def __init__(self, root):
        super().__init__()
        self.root = root
        self.rt = "core.ps.coll"
        self._links: list[str] = []   # list of link strings

    def get_topic_resources(self) -> dict:
        return {
            path: res
            for path, res in self.root._resources.items()
            if isinstance(res, TopicResource)
        }

    def add_link(self, path: str) -> None:
        link = f'</{path}>;rt="core.ps.conf"'
        if link not in self._links:
            self._links.append(link)

    def remove_link(self, path: str) -> None:
        link = f'</{path}>;rt="core.ps.conf"'
        self._links = [l for l in self._links if l != link]

    @property
    def _link_payload(self) -> bytes:
        return ",".join(self._links).encode("utf-8")

    async def render_post(self, request):
        ct = request.opt.content_format
        try:
            data = decode_topic_payload(request.payload, ct)
        except Exception as e:
            return Message(code=aiocoap.BAD_REQUEST, payload=str(e).encode())

        if "topic-name" not in data:
            return Message(code=aiocoap.BAD_REQUEST, payload=b"topic-name required")

        # Build topic-data URI
        topic_data_path = data.get("topic-data") or f"ps/data/{secrets.token_hex(3)}"
        topic_config_path = f"ps/{secrets.token_hex(3)}"

        # Assemble config (draft-19 §5.2.1)
        config: dict = {
            "topic-name":           data["topic-name"],
            "topic-data":           topic_data_path,
            "resource-type":        "core.ps.conf",
            "topic-content-format": data.get("topic-content-format"),
            "topic-type":           data.get("topic-type"),
            "expiration-date":      data.get("expiration-date"),
            "max-subscribers":      data.get("max-subscribers"),
            "observer-check":       data.get("observer-check", 86400),
        }

        topic_data_res = TopicDataResource(
            max_subscribers=config.get("max-subscribers"),
        )

        # Handle `initialize` — pre-populate topic-data (§5.2.1)
        init_payload = data.get("initialize")
        if init_payload is not None:
            if isinstance(init_payload, bytes):
                topic_data_res.set_content(init_payload)
            else:
                topic_data_res.set_content(str(init_payload).encode())

        self.root.add_resource(
            topic_config_path.split("/"),
            TopicResource(config, self.root, topic_config_path.split("/")),
        )
        self.root.add_resource(
            topic_data_path.split("/"),
            topic_data_res,
        )

        self.add_link(topic_config_path)

        response = Message(
            code=aiocoap.CREATED,
            payload=encode_topic_config(config),
        )
        response.opt.location_path = topic_config_path.split("/")
        response.opt.content_format = CT_PUBSUB_CBOR
        return response

    async def render_get(self, request):
        response = Message(payload=self._link_payload)
        response.opt.content_format = CT_LINK_FORMAT
        return response

    async def render_fetch(self, request):
        try:
            raw = cbor2.loads(request.payload)
        except Exception as e:
            return Message(code=aiocoap.BAD_REQUEST, payload=str(e).encode())

        # conf-filter (key 10): list of numeric property keys to match on
        filter_keys_raw = raw.get(TOPIC_KEYS["conf-filter"], [])
        # Also accept a plain map of key→value pairs for value-based filtering
        filter_map: dict[str, object] = {}
        if isinstance(filter_keys_raw, list):
            filter_names = [TOPIC_KEYS_REV.get(k, str(k)) for k in filter_keys_raw]
        else:
            # Treat as {numeric_key: value} map
            filter_map = {
                TOPIC_KEYS_REV.get(k, str(k)): v for k, v in raw.items()
                if k != TOPIC_KEYS["conf-filter"]
            }
            filter_names = list(filter_map.keys())

        matching: list[str] = []
        for path, res in self.get_topic_resources().items():
            path_str = "/".join(path)
            config = res.config
            if all(name in config for name in filter_names):
                if all(
                    str(config.get(n)) == str(v) for n, v in filter_map.items()
                ):
                    matching.append(f'</{path_str}>;rt="core.ps.conf"')

        payload = ",".join(matching).encode("utf-8")
        response = Message(code=aiocoap.CONTENT, payload=payload)
        response.opt.content_format = CT_LINK_FORMAT
        return response


# ---------------------------------------------------------------------------
# TopicResource  (/ps/<id>)
# ---------------------------------------------------------------------------

class TopicResource(resource.ObservableResource):

    def __init__(self, config: dict, site, path: list[str]):
        super().__init__()
        self.config = {k: v for k, v in config.items() if v is not None}
        self.site = site
        self.path = path
        self.rt = "core.ps.conf"

    async def render_get(self, request):
        response = Message(
            payload=encode_topic_config(self.config),
        )
        response.opt.content_format = CT_PUBSUB_CBOR
        return response

    async def render_post(self, request):
        """Full configuration replacement (draft-19 §5.3.1, replaces PUT)."""
        ct = request.opt.content_format
        try:
            data = decode_topic_payload(request.payload, ct)
        except Exception as e:
            return Message(code=aiocoap.BAD_REQUEST, payload=str(e).encode())

        # Immutable fields cannot be changed after creation
        if any(f in data for f in IMMUTABLE_FIELDS):
            return Message(
                code=aiocoap.BAD_REQUEST,
                payload=b"topic-name, topic-data, resource-type are immutable",
            )

        mutable = {"topic-content-format", "topic-type", "expiration-date",
                   "max-subscribers", "observer-check"}
        for field in mutable:
            if field in data:
                self.config[field] = data[field]

        self.updated_state()
        response = Message(code=aiocoap.CHANGED, payload=encode_topic_config(self.config))
        response.opt.content_format = CT_PUBSUB_CBOR
        return response

    async def render_ipatch(self, request):
        """Partial update (RFC 8473 incremental PATCH)."""
        ct = request.opt.content_format
        try:
            data = decode_topic_payload(request.payload, ct)
        except Exception as e:
            return Message(code=aiocoap.BAD_REQUEST, payload=str(e).encode())

        if any(f in data for f in IMMUTABLE_FIELDS):
            return Message(
                code=aiocoap.BAD_REQUEST,
                payload=b"topic-name, topic-data, resource-type are immutable",
            )

        for field, value in data.items():
            if field in self.config:
                self.config[field] = value
            else:
                return Message(code=aiocoap.NOT_FOUND,
                               payload=f"unknown field: {field}".encode())

        self.updated_state()
        response = Message(code=aiocoap.CHANGED, payload=encode_topic_config(self.config))
        response.opt.content_format = CT_PUBSUB_CBOR
        return response

    async def render_delete(self, request):
        # Remove topic config resource from site
        self.site.remove_resource(self.path)

        # Remove associated topic-data resource
        data_path = self.config.get("topic-data", "").split("/")
        self.site.remove_resource(data_path)

        # Update collection links
        collection = self.site._resources.get(("ps",))
        if collection:
            collection.remove_link("/".join(self.path))

        # Notify topic config observers of deletion
        for obs in list(self._observations):
            obs.trigger(Message(code=aiocoap.NOT_FOUND, payload=b"Topic deleted"), is_last=True)

        return Message(code=aiocoap.DELETED)


# ---------------------------------------------------------------------------
# TopicDataResource  (/ps/data/<id>)
# ---------------------------------------------------------------------------

class TopicDataResource(resource.ObservableResource):

    def __init__(self, max_subscribers: int | None = None):
        super().__init__()
        self._value: bytes | None = None   # None = HALF CREATED state
        self.rt = "core.ps.data"
        self._max_subscribers = max_subscribers

    @property
    def is_fully_created(self) -> bool:
        return self._value is not None

    def set_content(self, content: bytes) -> None:
        self._value = content
        self.updated_state()

    async def render_get(self, request):
        if not self.is_fully_created:
            return Message(code=aiocoap.NOT_FOUND)

        # Enforce max-subscribers when client sends Observe=0 (subscribe)
        if (
            request.opt.observe == 0
            and self._max_subscribers is not None
            and len(self._observations) >= self._max_subscribers
        ):
            # Respond with 2.05 Content but NO Observe option — subscription rejected
            return Message(code=aiocoap.CONTENT, payload=self._value)

        return Message(payload=self._value)

    async def render_put(self, request):
        was_created = not self.is_fully_created
        self.set_content(request.payload)
        code = aiocoap.CREATED if was_created else aiocoap.CHANGED
        return Message(code=code, payload=self._value)

    async def render_delete(self, request):
        """Revert topic to HALF CREATED state (draft-19 §5.4.3)."""
        self._value = None
        # Notify existing subscribers of the state change (they get 4.04)
        for obs in list(self._observations):
            obs.trigger(Message(code=aiocoap.NOT_FOUND, payload=b"Topic data deleted"), is_last=True)
        return Message(code=aiocoap.DELETED)


# ---------------------------------------------------------------------------
# Server setup
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logging.getLogger("coap-server").setLevel(logging.DEBUG)


async def _run(host: str, port: int) -> None:
    root = resource.Site()
    root.add_resource(
        [".well-known", "core"],
        resource.WKCResource(root.get_resources_as_linkheader),
    )
    root.add_resource(["ps"], CollectionResource(root))

    await aiocoap.Context.create_server_context(bind=(host, port), site=root)
    logging.info("CoAP pubsub broker listening on coap://%s:%d/ps", host, port)
    await asyncio.get_running_loop().create_future()


def main_cli() -> None:
    parser = argparse.ArgumentParser(
        description="CoAP Publish-Subscribe Broker (draft-ietf-core-coap-pubsub-19)",
    )
    parser.add_argument("--host", default="localhost", help="Bind host (default: localhost)")
    parser.add_argument("--port", type=int, default=5683, help="Bind port (default: 5683)")
    args = parser.parse_args()
    asyncio.run(_run(args.host, args.port))


if __name__ == "__main__":
    main_cli()
