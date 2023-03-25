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

Any client can create a topic as "admin":

```sh
./aiocoap-client -m POST coap://127.0.0.1:5683/ps --payload "{\"topic_name\": \"Room Temperature Sensor\", \"resource_type\": \"core.ps.conf\", \"media_type\": \"application/json\", \"target_attribute\": \"temperature\", \"expiration_date\": \"2023-04-05T23:59:59Z\", \"max_subscribers\": 100}"
```

The broker will create the resource paths for both the topic and topic_data resources. 

### Discover

Discover topics either via `.well-known/core` or by querying the collection resource `ps`.

```sh
./aiocoap-client -m GET coap://127.0.0.1/.well-known/core
./aiocoap-client -m GET coap://127.0.0.1/ps
```

### Publish

A CoAP client can act as publisher by sending a CoAP PUT to a topic_data resource. This initializes the resource into [FULLY CREATED](https://www.ietf.org/archive/id/draft-ietf-core-coap-pubsub-12.html#name-topic-lifecycle-2) state:

```sh
/aiocoap-client -m PUT coap://127.0.0.1:5683/ps/data/225acdd --payload "{"n": "temperature","u": "Cel","t": 1621452122,"v": 21.3}"
```

### Subscribe

Subscribe to a topic by using CoAP Observe:

```sh
./aiocoap-client -m GET --observe coap://127.0.0.1/ps/data/225acdd
```
## Resource Classes

The broker implements the following resource classes:

- CollectionResource: The collection resource `/ps` for storing topics.
- TopicResource: A resource for [topic configurations](https://www.ietf.org/archive/id/draft-ietf-core-coap-pubsub-12.html#name-topic-properties-2).
- TopicDataResource: A resource for topic data and for the [publish-subscribe interactions](https://www.ietf.org/archive/id/draft-ietf-core-coap-pubsub-12.html#name-topic-data-interactions-2) over CoAP.

## Supported operations

- Discovery
  - [x] GET /.well-known/core to discover collection
    - [ ] Use core.ps rt
    - [x] GET topic to discover topic configuration
    - [x] GET /ps to retrieve all topics
    - [ ] Use core.ps.conf rt
    - [ ] Use FETCH
- Configuration
    - [x] POST topic to create topic
    - [x] PUT topic to configure topic
    - [ ] DELETE topic to delete topic
- Topic Data
    - [x] PUT on topic_data to publish
    - [x] GET + observe on topic_data to Subscribe
    - [x] GET on topic_data to get last measurement
    - [ ] Delete to delete topic_data

Disclaimer: There is lots of hardcoded stuff, as this was quickly developed during the IETF116 hackathon.