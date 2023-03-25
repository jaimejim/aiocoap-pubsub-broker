#!/usr/bin/env python3

# aiocoap is implemented by Christian Amsüss <c.amsuess@energyharvesting.at>
# This simple broker is implemented by Jaime Jiménez. It is a CoAP server that creates and manages resources for storing data by implementing various Resource classes provided by aiocoap. The script implements https://datatracker.ietf.org/doc/html/draft-ietf-core-coap-pubsub-12

import datetime
import logging
import json
import asyncio
import aiocoap.resource as resource
import aiocoap
import secrets

# Define a collection resource for storing topics
class CollectionResource(resource.Resource):

    # Constructor method
    def __init__(self, root):
        super().__init__()
        self.handle = None
        self.content = ''
        self.root = root

        # Set the content type and resource type attributes
        self.rt = "core.ps.coll"

    # Method for setting content of the resource
    def set_content(self, content):
        self.content = content

    # Method for notifying observers
    def notify(self):
        self.updated_state()
        self.reschedule()

    # Method for rescheduling the observer notification
    def reschedule(self):
        self.handle = asyncio.get_event_loop().call_later(5, self.notify)

    # Method for updating the observation count
    def update_observation_count(self, count):
        if count and self.handle is None:
            print("Starting observation")
            self.reschedule()
        if count == 0 and self.handle:
            print("Stopping observation")
            self.handle.cancel()
            self.handle = None

    # Method for handling POST requests
    async def render_post(self, request):
        print('POST payload: %s' % request.payload)
        data = json.loads(request.payload)

        # Create resources for topic configuration and topic data
        topic_config_path = f'ps/{secrets.token_hex(3)}'
        topic_data_path = f'ps/data/{secrets.token_hex(3)}d'
        config_path_segments = topic_config_path.split('/')
        data_path_segments = topic_data_path.split('/')

        # Create a JSON object for the topic configuration resource
        topic_config_json = {
            "topic_name": data["topic_name"],
            "topic_data": topic_data_path,
            "resource_type": "core.ps.conf"
        }

        # Add the topic configuration and topic data resources to the root resource object
        self.root.add_resource(config_path_segments, TopicResource(topic_config_json))
        self.root.add_resource(data_path_segments, TopicDataResource())

        # Add a link to the new topic configuration resource to the content of this collection resource
        new_link = f'<{topic_config_path}>;rt="core.ps.conf"'
        if self.content:
            self.content += ',' + new_link
        else:
            self.content = new_link

        # Create the response message
        json_payload_bytes = json.dumps(topic_config_json).encode('utf-8')
        response = aiocoap.Message(code=aiocoap.CREATED, payload=json_payload_bytes)
        response.opt.location_path = topic_config_path
        response.opt.content_format = aiocoap.numbers.media_types_rev["application/json"]

        return response

    # Method for handling GET requests
    async def render_get(self, request):
        return aiocoap.Message(payload=self.content.encode('UTF-8'))

# Define a resource class for topic configurations
class TopicResource(resource.ObservableResource):

    # Constructor method
    def __init__(self, content):
        super().__init__()
        self.handle = None
        self.content = json.dumps(content).encode('utf-8')

        # Set the content type and resource type attributes
        self.ct = "application/link-format"
        self.rt = "core.ps.conf"

    # Method for setting content of the resource
    def set_content(self, content):
        self.content = content

    # Method for notifying observers
    def notify(self):
        self.updated_state()
        self.reschedule()

    # Method for rescheduling the observer notification
    def reschedule(self):
        self.handle = asyncio.get_event_loop().call_later(5, self.notify)

    # Method for updating the observation count
    def update_observation_count(self, count):
        if count and self.handle is None:
            print("Starting observation")
            self.reschedule()
        if count == 0 and self.handle:
            print("Stopping observation")
            self.handle.cancel()
            self.handle = None

    # Method for handling GET requests
    async def render_get(self, request):
        if not self.content:
            return aiocoap.Message(code=aiocoap.NOT_FOUND)
        else:
            return aiocoap.Message(payload=self.content)

    # Method for handling DELETE requests
    async def render_delete(self, request):
        # Return a 2.02 Deleted response
        return aiocoap.Message(code=aiocoap.DELETED)

# Define a resource class for topic data
class TopicDataResource(resource.ObservableResource):

    # Constructor method
    def __init__(self):
        super().__init__()
        self.handle = None
        self.content = b''

        # Set the content type and resource type attributes
        self.rt = "core.ps.data"

    # Method for setting content of the resource
    def set_content(self, content):
        self.content = content

    # Method for notifying observers
    def notify(self):
        self.updated_state()
        self.reschedule()

    # Method for rescheduling the observer notification
    def reschedule(self):
        self.handle = asyncio.get_event_loop().call_later(5, self.notify)

    # Method for updating the observation count
    def update_observation_count(self, count):
        if count and self.handle is None:
            print("Starting observation")
            self.reschedule()
        if count == 0 and self.handle:
            print("Stopping observation")
            self.handle.cancel()
            self.handle = None

    # Method for handling PUT requests
    async def render_put(self, request):
        print('PUT payload: %s' % request.payload)
        self.set_content(request.payload)
        return aiocoap.Message(code=aiocoap.CHANGED, payload=self.content)

    # Method for handling GET requests
    async def render_get(self, request):
        if not self.content:
            return aiocoap.Message(code=aiocoap.NOT_FOUND)
        else:
            return aiocoap.Message(payload=self.content)

# Define a resource class for temperature data
class TemperatureResource(resource.ObservableResource):

    # Constructor method
    def __init__(self):
        super().__init__()
        self.handle = None
        self.content = b''

    # Method for setting content of the resource
    def set_content(self, content):
        self.content = content

    # Method for notifying observers
    def notify(self):
        self.updated_state()
        self.reschedule()

    # Method for rescheduling the observer notification
    def reschedule(self):
        self.handle = asyncio.get_event_loop().call_later(5, self.notify)

    # Method for updating the observation count
    def update_observation_count(self, count):
        if count and self.handle is None:
            print("Starting observation")
            self.reschedule()
        if count == 0 and self.handle:
            print("Stopping observation")
            self.handle.cancel()
            self.handle = None

    # Method for handling PUT requests
    async def render_put(self, request):
        print('PUT payload: %s' % request.payload)
        self.set_content(request.payload)
        return aiocoap.Message(code=aiocoap.CHANGED, payload=self.content)

    # Method for handling GET requests
    async def render_get(self, request):
        if not self.content:
            return aiocoap.Message(code=aiocoap.NOT_FOUND)
        else:
            return aiocoap.Message(payload=self.content)

# Configure logging levels for the application
logging.basicConfig(level=logging.INFO)
logging.getLogger("coap-server").setLevel(logging.DEBUG)

async def main():
    # Create a resource tree for the CoAP server
    root = resource.Site()    

    root.add_resource(['.well-known', 'core'], resource.WKCResource(root.get_resources_as_linkheader))
    root.add_resource(['ps'], CollectionResource(root))

    # Start the CoAP server
    await aiocoap.Context.create_server_context(bind=('127.0.0.1',5683),site=root)

    # Run forever
    await asyncio.get_running_loop().create_future()

# Run the application loop
if __name__ == "__main__":
    asyncio.run(main())