# aiocoap-pubsub-broker

This is a simple CoAP broker implemented in Python using the [`aiocoap`](https://github.com/chrysn/aiocoap) library. The broker creates and manages resources for storing data by implementing various Resource classes provided by aiocoap. The script follows publish-subscribe architecture for the Constrained Application Protocol (CoAP) defined at [draft-ietf-core-coap-pubsub](https://datatracker.ietf.org/doc/draft-ietf-core-coap-pubsub/).

![arch](./arch.svg)


## Requirements

- Python 3.12 or higher
- `aiocoap` library
- `cbor2` library
- `cbor-diag` requires Rust and Cargo
- You need to install the latest development version of aiocoap, which supports iPATCH.

```sh
pip3 install --upgrade "git+https://github.com/chrysn/aiocoap#egg=aiocoap[all]"
```

- I have an entry from the broker uri on `/etc/hosts` for demo purposes, you may want to have the same:

```sh
127.0.0.1	iot.dev
```

## Usage

Run the CoAP broker:

```sh
python3 broker.py
```

The broker will start listening on `127.0.0.1:5683`.

You can use `poetry` to manage dependencies. Simply run `poetry install` to install all required packages, and then use `poetry run python3 broker.py` to start the broker.

### Create Topic

The broker hosts topic resources on which topic-data resources that clients can subscribe/publish to rest.

![topics](./topics.svg)

A client can create a topic as "admin":

```sh
./client.py -m POST coap://127.0.0.1:5683/ps --payload "{\"topic-name\": \"Room Temperature Sensor\", \"resource-type\": \"core.ps.conf\", \"media-type\": \"application/json\", \"topic-type\": \"temperature\", \"expiration-date\": \"2023-04-05T23:59:59Z\", \"max-subscribers\": 200, \"observer-check\": 86400}"
```

```js
Response arrived from different address; base URI is coap://127.0.0.1/ps
Location options indicate new resource: /ps/e99889
JSON re-formated and indented
{
    "topic-name": "Room Temperature Sensor",
    "topic-data": "ps/data/08dd75d",
    "resource-type": "core.ps.conf",
    "media-type": "application/json",
    "topic-type": "temperature",
    "expiration-date": "2023-04-05T23:59:59Z",
    "max-subscribers": 200,
    "observer-check": 86400
}
```

The broker will create the resource paths for both the topic and topic-data resources.

### Discover

Discover topics either via `.well-known/core` or by querying the collection resource `ps`.

You may discover the following resource types:
- `core.ps.coll` - the topic collection resource.
- `core.ps.conf` - the topic resource.
- `core.ps.data` - the topic-data resource.

```sh
❯ ./client.py -m GET coap://127.0.0.1/ps
<ps/4fb3de>;rt="core.ps.conf"
```

or

```sh
./client.py -m GET coap://127.0.0.1/.well-known/core
```

```js
application/link-format content was re-formatted
</.well-known/core>; ct=40,
</ps>; rt=core.ps.coll,
</ps/4fb3de>; ct=application/link-format; rt=core.ps.conf; obs,
</ps/data/a08b18d>; rt=core.ps.data; obs,
<https://christian.amsuess.com/tools/aiocoap/#version-0.4.4.post0>; rel=impl-info
```

or by `rt`

```sh
./client.py -m GET 'coap://127.0.0.1/.well-known/core?rt=core.ps.conf'
```

```js
application/link-format content was re-formatted
</ps/dd4494>; ct=None; rt=core.ps.conf; obs,
</ps/cdc49a>; ct=application/json; rt=core.ps.conf; obs
```

or

```sh
./client.py -m GET 'coap://127.0.0.1/.well-known/core?rt=core.ps.coll'
```

```js
application/link-format content was re-formatted
</ps>; rt=core.ps.coll
```

### Retrieve a topic

Any topic can be retrieved via its corresponding URI.

```sh
./client.py -m GET 'coap://127.0.0.1/ps/e99889'
```

```js
{"topic-name": "Room Temperature Sensor", "topic-data": "ps/data/08dd75d", "resource-type": "core.ps.conf", "media-type": "application/json", "topic-type": "temperature", "expiration-date": "2023-04-05T23:59:59Z", "max-subscribers": 200, "observer-check": 86400}
```

From it, the associated topic-data can be interacted with providing it is FULLY created. For that a publisher needs to publish.

### Update a topic with PUT

Properties of a topic can be updated on its corresponding URI.

```sh
./client.py -m PUT coap://127.0.0.1:5683/ps/b616a3 --payload "{\"max-subscribers\": 200}"
```

```js
Response arrived from different address; base URI is coap://127.0.0.1/ps/b616a3
JSON re-formated and indented
{
    "topic-name": "Room Temperature Sensor",
    "topic-data": "ps/data/957d7fd",
    "resource-type": "core.ps.conf",
    "media-type": "application/json",
    "topic-type": "temperature",
    "expiration-date": "2023-04-05T23:59:59Z",
    "max-subscribers": 200,
    "observer-check": 86400
}
```

### Update a topic with iPATCH

Properties of a topic can be updated on its corresponding URI.

```sh
./client.py -m iPATCH coap://127.0.0.1/ps/e99889 --payload "{\"max-subscribers\": 300}"
```

```js
JSON re-formated and indented
{
    "topic-name": "Room Temperature Sensor",
    "topic-data": "ps/data/08dd75d",
    "resource-type": "core.ps.conf",
    "media-type": "application/json",
    "topic-type": "temperature",
    "expiration-date": "2023-04-05T23:59:59Z",
    "max-subscribers": 300,
    "observer-check": 86400
}
```

### FETCH a topics by Properties

A client can filter a collection of topics with a topic filter in a FETCH request to the topic collection URI.

```sh
./client.py -m FETCH 'coap://127.0.0.1/ps' --content-format 'application/cbor' --payload '{"max-subscribers": 300}'
```

```js
application/link-format content was re-formatted
<ps/e99889>; rt=core.ps.conf
```

### Publish

A CoAP client can act as publisher by sending a CoAP PUT to a topic-data resource. This initializes the resource into [FULLY CREATED](https://www.ietf.org/archive/id/draft-ietf-core-coap-pubsub-12.html#name-topic-lifecycle-2) state:

```sh
./client.py -m PUT coap://127.0.0.1:5683/ps/data/08dd75d --payload "{"n": "temperature","u": "Cel","t": 1621452122,"v": 21.3}"
```

```js
Response arrived from different address; base URI is coap://127.0.0.1/ps/data/08dd75d
{n: temperature,u: Cel,t: 1621452122,v: 21.3}
```

### Subscribe

Subscribe to a topic by using CoAP Observe:

```sh
./client.py -m GET --observe coap://127.0.0.1:5683/ps/data/08dd75d
```

```js
Response arrived from different address; base URI is coap://127.0.0.1/ps/data/08dd75d
{n: temperature,u: Cel,t: 1621452122,v: 21.3}
---
{n: temperature,u: Cel,t: 1621452122,v: 21.3}
```

## Resource Classes

The broker implements the following resource classes:

- CollectionResource: The collection resource `/ps` for storing topics.
- TopicResource: A resource for [topics](https://www.ietf.org/archive/id/draft-ietf-core-coap-pubsub-12.html#name-topic-properties-2).
- TopicDataResource: A resource for topic-data and for the [publish-subscribe interactions](https://www.ietf.org/archive/id/draft-ietf-core-coap-pubsub-12.html#name-topic-data-interactions-2) over CoAP.

## Supported operations

- Discovery
  - [x] GET /.well-known/core to discover collection
    - [x] Well known discovery with rt
    - [x] Topic Collection discovery
    - [x] Update to current list of Topic Properties on draft
    - [x] GET topic to discover topic configuration
    - [x] GET /ps to retrieve all topics
    - [x] FETCH
    - [ ] multicast
- Configuration
    - [x] POST topic to create topic
    - [x] PUT to update topic configuration
    - [x] iPATCH to partially update topic configuration
    - [x] DELETE topic to delete topic
    - [ ] Client defined topic-data url
- Topic Data
    - [x] PUT on topic-data to publish
    - [x] GET + observe on topic-data to Subscribe
    - [x] GET on topic-data to get last measurement
    - [ ] Delete to delete topic-data
- Other
    - [ ] Improve Broker Logic
    - [ ] Fix Scripts 

Disclaimer: There is lots of hardcoded stuff, as this was quickly developed during the IETF116 nad IETF118 hackathons.
