# aiocoap-pubsub-broker

A CoAP Publish-Subscribe broker implementing [draft-ietf-core-coap-pubsub-19](https://datatracker.ietf.org/doc/draft-ietf-core-coap-pubsub/), built on the [`aiocoap`](https://github.com/chrysn/aiocoap) library.

Topics are CBOR-encoded resources (application/core-pubsub+cbor). JSON is accepted as a fallback for tools that don't speak CBOR.

![architecture](./arch.svg)

## Requirements

- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/)

## Installation

```sh
git clone https://github.com/your-org/aiocoap-pubsub-broker
cd aiocoap-pubsub-broker
uv sync
```

This installs two commands into the project virtual environment:

| Command | Description |
|---------|-------------|
| `pubsub-broker` | Runs the CoAP pubsub broker |
| `pubsub-client` | Client CLI for all pubsub operations |

To install the commands globally:

```sh
uv tool install .
```

## Running the broker

```sh
uv run pubsub-broker                         # localhost:5683
uv run pubsub-broker --host 0.0.0.0          # listen on all interfaces
uv run pubsub-broker --host 0.0.0.0 --port 5684
```

## Topic structure

A topic collection lives at `/ps`. Each topic has two associated resources:

| Resource | Path | Type |
|----------|------|------|
| Collection | `/ps` | `core.ps.coll` |
| Topic config | `/ps/<id>` | `core.ps.conf` |
| Topic data | `/ps/data/<id>` | `core.ps.data` |

Topics have a lifecycle:
- **HALF CREATED** — topic config exists but no data has been published yet (GET on topic-data returns 4.04)
- **FULLY CREATED** — data has been published at least once (subscribers receive 2.05 with Observe)

## Topic properties (CBOR numeric keys)

| Property | CBOR key | Type | Description |
|----------|----------|------|-------------|
| `topic-name` | 0 | string | Human-readable identifier (immutable) |
| `topic-data` | 1 | string | URI of topic-data resource (immutable) |
| `resource-type` | 2 | string | Always `core.ps.conf` (immutable) |
| `topic-content-format` | 3 | uint | CoAP content-format of published data |
| `topic-type` | 4 | string | Application-level type (e.g. `temperature`) |
| `expiration-date` | 5 | CBOR tag 1 | Epoch-based expiry (RFC 8949) |
| `max-subscribers` | 6 | uint | Maximum concurrent subscribers |
| `observer-check` | 7 | uint | Max seconds between confirmable notifications (default: 86400) |
| `initialize` | 8 | bytes | Initial payload — pre-populates topic-data at creation time |

---

## Client usage

```sh
uv run pubsub-client --help
```

### Create a topic

```sh
uv run pubsub-client create coap://localhost temperature \
    --type sensor --format 60 --max-subs 10
```

Create with initial data (topic enters FULLY CREATED immediately):

```sh
uv run pubsub-client create coap://localhost humidity \
    --type sensor --init '{"v":55.2}'
```

Response (CBOR decoded):
```json
{
  "topic-name": "temperature",
  "topic-data": "ps/data/a3f1b2",
  "resource-type": "core.ps.conf",
  "topic-type": "sensor",
  "topic-content-format": 60,
  "max-subscribers": 10,
  "observer-check": 86400
}
```

### List topics

```sh
uv run pubsub-client list coap://localhost
# </ps/3a1b2c>;rt="core.ps.conf",</ps/4d5e6f>;rt="core.ps.conf"
```

### Discover via .well-known/core

```sh
uv run pubsub-client read coap://localhost/.well-known/core
```

Filter by resource type:

```sh
uv run pubsub-client read 'coap://localhost/.well-known/core?rt=core.ps.conf'
```

### Read topic configuration

```sh
uv run pubsub-client read coap://localhost/ps/3a1b2c
```

### FETCH — filter topics by property

```sh
uv run pubsub-client fetch coap://localhost --filter topic-name,topic-type
```

### Full config replacement (POST)

```sh
uv run pubsub-client update coap://localhost coap://localhost/ps/3a1b2c \
    max-subscribers=50 observer-check=3600
```

### Partial update (iPATCH)

```sh
uv run pubsub-client patch coap://localhost coap://localhost/ps/3a1b2c \
    observer-check=7200
```

### Delete topic

Deletes the topic config and its associated topic-data resource. Active subscribers receive 4.04.

```sh
uv run pubsub-client delete coap://localhost coap://localhost/ps/3a1b2c
```

---

## Publish and subscribe

### Publish

```sh
uv run pubsub-client publish coap://localhost/ps/data/a3f1b2 '{"v":22.5}'
# 2.04 Changed
```

First publication returns 2.01 Created and transitions the topic to FULLY CREATED.

### Read latest value

```sh
uv run pubsub-client read coap://localhost/ps/data/a3f1b2
# {"v":22.5}
```

### Subscribe (Observe)

```sh
uv run pubsub-client sub coap://localhost/ps/data/a3f1b2
# [subscribe] {"v":22.5}
# [update]    {"v":23.1}
# ^C
```

If `max-subscribers` is reached, the broker responds without the Observe option — the client sees `Subscription rejected`.

### Delete topic-data

Reverts the topic to HALF CREATED. Active subscribers receive 4.04.

```sh
uv run pubsub-client delete coap://localhost coap://localhost/ps/data/a3f1b2
```

---

## Interactive demo

Runs a full walkthrough of all protocol operations against a running broker:

```sh
uv run pubsub-broker &
uv run pubsub-client demo coap://localhost
```

---

## Resource types

| Type | Meaning |
|------|---------|
| `core.ps` | Publish-subscribe broker |
| `core.ps.coll` | Topic collection |
| `core.ps.conf` | Topic resource (configuration) |
| `core.ps.data` | Topic-data resource |

---

## Supported operations (draft-19)

- Discovery
  - [x] `GET /.well-known/core` with `rt` filtering
  - [x] `GET /ps` to list all topics
  - [x] `FETCH /ps` with `conf-filter` property filtering
  - [ ] Multicast discovery
- Topic configuration
  - [x] `POST /ps` — create topic
  - [x] `POST /ps/<id>` — full config replacement
  - [x] `iPATCH /ps/<id>` — partial config update
  - [x] `DELETE /ps/<id>` — delete topic (cascades to topic-data)
  - [x] `initialize` property — pre-populate topic-data at creation
  - [x] Client-provided `topic-data` URI
- Topic data
  - [x] `PUT` on topic-data — publish (2.01 Created first time, 2.04 Changed after)
  - [x] `GET + Observe=0` on topic-data — subscribe
  - [x] `GET` on topic-data — read latest value
  - [x] `DELETE` on topic-data — revert to HALF CREATED
  - [x] `max-subscribers` enforcement (subscribe rejected without Observe option)
- Encoding
  - [x] `application/core-pubsub+cbor` (CT 606) with numeric CBOR keys
  - [x] JSON fallback accepted on input
  - [x] CBOR tag 1 for `expiration-date` (RFC 8949 epoch)

---

## Architecture

Built on [`aiocoap`](https://github.com/chrysn/aiocoap) by Christian Amsüss. Broker and client developed by Jaime Jiménez during IETF hackathons and updated to draft-19.
