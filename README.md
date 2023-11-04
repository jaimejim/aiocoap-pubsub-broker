# aiocoap-pubsub-broker

This is a simple CoAP broker implemented in Python using the [`aiocoap`](https://github.com/chrysn/aiocoap) library. The broker creates and manages resources for storing data by implementing various Resource classes provided by aiocoap. The script follows publish-subscribe architecture for the Constrained Application Protocol (CoAP) defined at [draft-ietf-core-coap-pubsub](https://datatracker.ietf.org/doc/draft-ietf-core-coap-pubsub/).

## Requirements

- Python 3.7 or higher
- `aiocoap` library

## Installation

Install the required Python packages:

```sh
pip install aiocoap
```

## Usage

Run the CoAP broker (I recommend `hupper` if you are developing in python):

```sh
hupper -m broker
```

The broker will start listening on 127.0.0.1:5683.

### Create Topic

Any client can create a topic-configuration as "admin":

```sh
❯ ./client.py -m POST coap://127.0.0.1:5683/ps --payload "{\"topic-name\": \"Room Temperature Sensor\", \"resource-type\": \"core.ps.conf\", \"media-type\": \"application/json\", \"target-attribute\": \"temperature\", \"expiration-date\": \"2023-04-05T23:59:59Z\", \"max-subscribers\": 100}"
Response arrived from different address; base URI is coap://127.0.0.1/ps
Location options indicate new resource: /ps/4fb3de
JSON re-formated and indented
{
    "topic-name": "Room Temperature Sensor",
    "topic-data": "ps/data/a08b18d",
    "resource-type": "core.ps.conf"
}
```

The broker will create the resource paths for both the topic-configuration and topic-data resources.

### Discover

Discover topics either via `.well-known/core` or by querying the collection resource `ps`.

You may discover the following resource types:
- `core.ps.coll` - the topic collection resource.
- `core.ps.conf` - the topic-configuration resource.
- `core.ps.data` - the topic-data resource.

```sh
❯ ./client.py -m GET coap://127.0.0.1/ps
<ps/4fb3de>;rt="core.ps.conf"
```

or

```sh
❯ ./client.py -m GET coap://127.0.0.1/.well-known/core
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
application/link-format content was re-formatted
</ps/dd4494>; ct=None; rt=core.ps.conf; obs,
</ps/cdc49a>; ct=application/json; rt=core.ps.conf; obs
```

or

```sh
❯ ./client.py -m GET 'coap://127.0.0.1/.well-known/core?rt=core.ps.coll'
application/link-format content was re-formatted
</ps>; rt=core.ps.coll
```

### Retrieve a topic-configuration

Any topic-configuration can be retrieved via its corresponding URI.

```sh
❯ ./client.py -m GET coap://127.0.0.1/ps/4fb3de
{"topic-name": "Room Temperature Sensor", "topic-data": "ps/data/a08b18d", "resource-type": "core.ps.conf"}
```

From it, the associated topic-data can be interacted with providing it is FULLY created. For that a publisher needs to publish.

### Publish

A CoAP client can act as publisher by sending a CoAP PUT to a topic-data resource. This initializes the resource into [FULLY CREATED](https://www.ietf.org/archive/id/draft-ietf-core-coap-pubsub-12.html#name-topic-lifecycle-2) state:

```sh
❯ ./client.py -m PUT coap://127.0.0.1:5683/ps/data/a08b18d --payload "{"n": "temperature","u": "Cel","t": 1621452122,"v": 21.3}"
Response arrived from different address; base URI is coap://127.0.0.1/ps/data/a08b18d
{n: temperature,u: Cel,t: 1621452122,v: 21.3}
```

### Subscribe

Subscribe to a topic by using CoAP Observe:

```sh
❯ ./client.py -m GET --observe coap://127.0.0.1:5683/ps/data/a08b18d
Response arrived from different address; base URI is coap://127.0.0.1/ps/data/a08b18d
{n: temperature,u: Cel,t: 1621452122,v: 21.3}
---
{n: temperature,u: Cel,t: 1621452122,v: 21.3}
```
## Resource Classes

The broker implements the following resource classes:

- CollectionResource: The collection resource `/ps` for storing topics.
- TopicResource: A resource for [topic-configurations](https://www.ietf.org/archive/id/draft-ietf-core-coap-pubsub-12.html#name-topic-properties-2).
- TopicDataResource: A resource for topic-data and for the [publish-subscribe interactions](https://www.ietf.org/archive/id/draft-ietf-core-coap-pubsub-12.html#name-topic-data-interactions-2) over CoAP.

## Supported operations

- Discovery
  - [x] GET /.well-known/core to discover collection
    - [x] Well known discovery with rt
    - [x] Topic Collection discovery
    - [x] Update to current list of Topic Properties on draft
    - [x] GET topic to discover topic configuration
    - [x] GET /ps to retrieve all topics
    - [ ] FETCH
    - [ ] multicast
- Configuration
    - [x] POST topic to create topic
    - [x] PUT topic to configure topic
    - [ ] Client defined topic-data url
    - [ ] DELETE topic to delete topic
- Topic Data
    - [x] PUT on topic-data to publish
    - [x] GET + observe on topic-data to Subscribe
    - [x] GET on topic-data to get last measurement
    - [ ] Delete to delete topic-data
- Other
    - [ ] Improve Broker Logic

Disclaimer: There is lots of hardcoded stuff, as this was quickly developed during the IETF116 nad IETF118 hackathons.
