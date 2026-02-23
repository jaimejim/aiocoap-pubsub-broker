#!/usr/bin/env python3

# CoAP Publish-Subscribe Client CLI — draft-ietf-core-coap-pubsub-19
# Jaime Jiménez <jaimejim@gmail.com>
# Built on aiocoap by Christian Amsüss

"""
pubsub-client — command-line client for a CoAP pubsub broker

Subcommands:
  create   <broker>  <topic-name>  [options]
  list     <broker>
  fetch    <broker>  --filter <key>[,key...]
  update   <broker>  <topic-url>   <key>=<value> ...
  patch    <broker>  <topic-url>   <key>=<value> ...
  delete   <broker>  <topic-url>
  publish  <data-url>  <payload>  [--format FORMAT]
  read     <data-url>
  sub      <data-url>
  demo     <broker>
"""

import argparse
import asyncio
import json
import sys

import aiocoap
import cbor2

# Re-use codec helpers from broker
CT_PUBSUB_CBOR = 606
CT_LINK_FORMAT = 40

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


def _encode(d: dict) -> bytes:
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


def _decode(payload: bytes) -> dict:
    raw = cbor2.loads(payload)
    result = {}
    for k, v in raw.items():
        name = TOPIC_KEYS_REV.get(k, str(k))
        if name == "expiration-date" and isinstance(v, cbor2.CBORTag) and v.tag == 1:
            v = v.value
        result[name] = v
    return result


def _pretty(d: dict) -> str:
    return json.dumps(d, indent=2, default=str)


def _broker_uri(broker: str) -> str:
    """Ensure broker URL starts with coap://."""
    if not broker.startswith("coap"):
        return f"coap://{broker}"
    return broker


async def _request(
    ctx,
    method: str,
    uri: str,
    payload: bytes = b"",
    content_format: int | None = None,
) -> aiocoap.Message:
    msg = aiocoap.Message(code=getattr(aiocoap.numbers.codes.Code, method), uri=uri)
    if payload:
        msg.payload = payload
    if content_format is not None:
        msg.opt.content_format = content_format
    return await ctx.request(msg).response


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------

async def cmd_list(args) -> None:
    async with aiocoap.Context.create_client_context() as ctx:
        broker = _broker_uri(args.broker)
        r = await _request(ctx, "GET", f"{broker}/ps")
        print(r.payload.decode())


async def cmd_create(args) -> None:
    config: dict = {"topic-name": args.topic_name}
    if args.type:
        config["topic-type"] = args.type
    if args.format is not None:
        config["topic-content-format"] = args.format
    if args.max_subs is not None:
        config["max-subscribers"] = args.max_subs
    if args.expires is not None:
        config["expiration-date"] = args.expires
    if args.init is not None:
        config["initialize"] = args.init.encode() if isinstance(args.init, str) else args.init

    async with aiocoap.Context.create_client_context() as ctx:
        broker = _broker_uri(args.broker)
        r = await _request(ctx, "POST", f"{broker}/ps",
                           payload=_encode(config),
                           content_format=CT_PUBSUB_CBOR)
        if r.code == aiocoap.CREATED:
            loc = "/".join(r.opt.location_path)
            print(f"Created: {broker}/{loc}")
            print(_pretty(_decode(r.payload)))
        else:
            print(f"Error: {r.code}", file=sys.stderr)
            sys.exit(1)


async def cmd_fetch(args) -> None:
    filter_keys = [k.strip() for k in args.filter.split(",")]
    unknown = [k for k in filter_keys if k not in TOPIC_KEYS]
    if unknown:
        print(f"Unknown filter keys: {unknown}", file=sys.stderr)
        sys.exit(1)
    numeric_keys = [TOPIC_KEYS[k] for k in filter_keys]
    payload = cbor2.dumps({TOPIC_KEYS["conf-filter"]: numeric_keys})

    async with aiocoap.Context.create_client_context() as ctx:
        broker = _broker_uri(args.broker)
        msg = aiocoap.Message(code=aiocoap.numbers.codes.Code.FETCH,
                              uri=f"{broker}/ps",
                              payload=payload)
        msg.opt.content_format = CT_PUBSUB_CBOR
        r = await ctx.request(msg).response
        print(r.payload.decode())


async def cmd_update(args) -> None:
    """Full config replacement (POST on topic resource)."""
    updates = _parse_kv(args.fields)
    async with aiocoap.Context.create_client_context() as ctx:
        r = await _request(ctx, "POST", _broker_uri(args.topic_url),
                           payload=_encode(updates),
                           content_format=CT_PUBSUB_CBOR)
        if r.code == aiocoap.CHANGED:
            print(_pretty(_decode(r.payload)))
        else:
            print(f"Error: {r.code}", file=sys.stderr)
            sys.exit(1)


async def cmd_patch(args) -> None:
    """Partial update (iPATCH on topic resource)."""
    updates = _parse_kv(args.fields)
    async with aiocoap.Context.create_client_context() as ctx:
        msg = aiocoap.Message(code=aiocoap.numbers.codes.Code.IPATCH,
                              uri=_broker_uri(args.topic_url),
                              payload=_encode(updates))
        msg.opt.content_format = CT_PUBSUB_CBOR
        r = await ctx.request(msg).response
        if r.code == aiocoap.CHANGED:
            print(_pretty(_decode(r.payload)))
        else:
            print(f"Error: {r.code}", file=sys.stderr)
            sys.exit(1)


async def cmd_delete(args) -> None:
    async with aiocoap.Context.create_client_context() as ctx:
        r = await _request(ctx, "DELETE", _broker_uri(args.topic_url))
        print(f"{r.code}")


async def cmd_publish(args) -> None:
    payload = args.payload.encode() if isinstance(args.payload, str) else args.payload
    ct = args.format  # None means no content-format option set
    async with aiocoap.Context.create_client_context() as ctx:
        r = await _request(ctx, "PUT", _broker_uri(args.data_url),
                           payload=payload,
                           content_format=ct)
        print(f"{r.code}")


async def cmd_read(args) -> None:
    async with aiocoap.Context.create_client_context() as ctx:
        r = await _request(ctx, "GET", _broker_uri(args.data_url))
        if r.code == aiocoap.CONTENT:
            print(r.payload.decode(errors="replace"))
        else:
            print(f"{r.code}", file=sys.stderr)
            sys.exit(1)


async def cmd_sub(args) -> None:
    """Subscribe to a topic-data resource and print updates until Ctrl-C."""
    async with aiocoap.Context.create_client_context() as ctx:
        msg = aiocoap.Message(code=aiocoap.GET, uri=_broker_uri(args.data_url),
                              observe=0)
        req = ctx.request(msg)
        # First response
        r = await req.response
        if r.opt.observe is None:
            print("Subscription rejected (max-subscribers reached or resource not found)")
            print(r.payload.decode(errors="replace"))
            return
        print(f"[subscribe] {r.payload.decode(errors='replace')}")

        try:
            async for obs in req.observation:
                print(f"[update]    {obs.payload.decode(errors='replace')}")
        except aiocoap.error.NotObservable:
            print("[end] Resource no longer observable")
        except KeyboardInterrupt:
            pass
        finally:
            req.observation.cancel()


async def cmd_demo(args) -> None:
    """Full walkthrough of all pubsub operations."""
    broker = _broker_uri(args.broker)
    print(f"\n=== CoAP PubSub Demo — broker: {broker} ===\n")

    async with aiocoap.Context.create_client_context() as ctx:

        # 1. Create a topic
        print("1. Create 'temperature' topic")
        config = {
            "topic-name": "temperature",
            "topic-type": "sensor",
            "topic-content-format": 60,   # application/cbor
            "max-subscribers": 5,
            "observer-check": 3600,
            "initialize": b'{"v":20.0}',
        }
        r = await _request(ctx, "POST", f"{broker}/ps",
                           payload=_encode(config),
                           content_format=CT_PUBSUB_CBOR)
        if r.code != aiocoap.CREATED:
            print(f"  Failed: {r.code}")
            return
        loc = "/".join(r.opt.location_path)
        topic_url = f"{broker}/{loc}"
        topic_config = _decode(r.payload)
        data_url = f"{broker}/{topic_config['topic-data']}"
        print(f"  Topic:      {topic_url}")
        print(f"  Topic-data: {data_url}")

        # 2. List topics
        print("\n2. List all topics")
        r = await _request(ctx, "GET", f"{broker}/ps")
        print(f"  {r.payload.decode()}")

        # 3. Read config
        print("\n3. Read topic configuration")
        r = await _request(ctx, "GET", topic_url)
        print(_pretty(_decode(r.payload)))

        # 4. Read topic-data (pre-populated by initialize)
        print("\n4. Read topic-data (pre-populated by 'initialize')")
        r = await _request(ctx, "GET", data_url)
        print(f"  {r.payload.decode(errors='replace')}")

        # 5. Publish
        print("\n5. Publish sensor reading")
        r = await _request(ctx, "PUT", data_url,
                           payload=b'{"v":22.5}')
        print(f"  {r.code}")

        # 6. Read back
        print("\n6. Read latest value")
        r = await _request(ctx, "GET", data_url)
        print(f"  {r.payload.decode(errors='replace')}")

        # 7. Patch topic config
        print("\n7. Patch: update observer-check to 7200")
        patch = {"observer-check": 7200}
        msg = aiocoap.Message(code=aiocoap.numbers.codes.Code.IPATCH,
                              uri=topic_url,
                              payload=_encode(patch))
        msg.opt.content_format = CT_PUBSUB_CBOR
        r = await ctx.request(msg).response
        print(f"  {r.code} — {_pretty(_decode(r.payload))}")

        # 8. Fetch filter
        print("\n8. FETCH topics with conf-filter [topic-name, topic-type]")
        filt = cbor2.dumps({TOPIC_KEYS["conf-filter"]: [
            TOPIC_KEYS["topic-name"], TOPIC_KEYS["topic-type"]
        ]})
        msg = aiocoap.Message(code=aiocoap.numbers.codes.Code.FETCH,
                              uri=f"{broker}/ps",
                              payload=filt)
        msg.opt.content_format = CT_PUBSUB_CBOR
        r = await ctx.request(msg).response
        print(f"  {r.payload.decode()}")

        # 9. Delete topic-data (revert to HALF CREATED)
        print("\n9. Delete topic-data (revert to HALF CREATED)")
        r = await _request(ctx, "DELETE", data_url)
        print(f"  {r.code}")

        # 10. Verify HALF CREATED
        print("\n10. GET topic-data — should return 4.04 Not Found")
        r = await _request(ctx, "GET", data_url)
        print(f"  {r.code}")

        # 11. Re-publish (FULLY CREATED again)
        print("\n11. Publish again — topic returns to FULLY CREATED")
        r = await _request(ctx, "PUT", data_url, payload=b'{"v":23.1}')
        print(f"  {r.code}")

        # 12. Delete topic
        print("\n12. Delete topic (cascades to topic-data)")
        r = await _request(ctx, "DELETE", topic_url)
        print(f"  {r.code}")

        print("\n=== Demo complete ===\n")


# ---------------------------------------------------------------------------
# Argument parsing helpers
# ---------------------------------------------------------------------------

def _parse_kv(fields: list[str]) -> dict:
    result = {}
    for f in fields:
        if "=" not in f:
            print(f"Invalid field spec: {f!r} (expected key=value)", file=sys.stderr)
            sys.exit(1)
        k, _, v = f.partition("=")
        k = k.strip()
        # Attempt numeric coercion
        if v.isdigit():
            result[k] = int(v)
        else:
            try:
                result[k] = float(v)
            except ValueError:
                result[k] = v
    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pubsub-client",
        description="CoAP Publish-Subscribe client (draft-ietf-core-coap-pubsub-19)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # list
    p = sub.add_parser("list", help="List all topics at broker")
    p.add_argument("broker", help="Broker base URI, e.g. coap://localhost")

    # create
    p = sub.add_parser("create", help="Create a new topic")
    p.add_argument("broker")
    p.add_argument("topic_name", metavar="topic-name")
    p.add_argument("--type", help="topic-type (e.g. temperature)")
    p.add_argument("--format", type=int, dest="format", help="topic-content-format (CoAP CT number)")
    p.add_argument("--max-subs", type=int, dest="max_subs", help="max-subscribers")
    p.add_argument("--expires", type=int, help="expiration-date (epoch int)")
    p.add_argument("--init", help="initialize: initial payload string for topic-data")

    # fetch
    p = sub.add_parser("fetch", help="FETCH topics filtered by property keys")
    p.add_argument("broker")
    p.add_argument("--filter", required=True,
                   help="Comma-separated property names, e.g. topic-name,topic-type")

    # update (full POST replacement)
    p = sub.add_parser("update", help="Full config replacement (POST) on a topic resource")
    p.add_argument("broker", help="Unused, kept for consistency")
    p.add_argument("topic_url", metavar="topic-url", help="Full URI of topic resource")
    p.add_argument("fields", nargs="+", metavar="key=value")

    # patch (iPATCH)
    p = sub.add_parser("patch", help="Partial config update (iPATCH) on a topic resource")
    p.add_argument("broker", help="Unused, kept for consistency")
    p.add_argument("topic_url", metavar="topic-url")
    p.add_argument("fields", nargs="+", metavar="key=value")

    # delete
    p = sub.add_parser("delete", help="Delete a topic resource (cascades to topic-data)")
    p.add_argument("broker", help="Unused, kept for consistency")
    p.add_argument("topic_url", metavar="topic-url")

    # publish
    p = sub.add_parser("publish", help="Publish data to a topic-data resource")
    p.add_argument("data_url", metavar="data-url", help="Full URI of topic-data resource")
    p.add_argument("payload", help="Payload string to publish")
    p.add_argument("--format", type=int, dest="format", help="Content-Format number")

    # read
    p = sub.add_parser("read", help="Read current value from a topic-data resource")
    p.add_argument("data_url", metavar="data-url")

    # sub
    p = sub.add_parser("sub", help="Subscribe to a topic-data resource (Ctrl-C to stop)")
    p.add_argument("data_url", metavar="data-url")

    # demo
    p = sub.add_parser("demo", help="Full walkthrough of all pubsub operations")
    p.add_argument("broker")

    args = parser.parse_args()

    handlers = {
        "list":    cmd_list,
        "create":  cmd_create,
        "fetch":   cmd_fetch,
        "update":  cmd_update,
        "patch":   cmd_patch,
        "delete":  cmd_delete,
        "publish": cmd_publish,
        "read":    cmd_read,
        "sub":     cmd_sub,
        "demo":    cmd_demo,
    }

    asyncio.run(handlers[args.cmd](args))


if __name__ == "__main__":
    main()
