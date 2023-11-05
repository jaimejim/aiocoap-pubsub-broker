#!/usr/bin/env python3

# aiocoap is implemented by Christian Amsüss <c.amsuess@energyharvesting.at>
# This simple broker script is implemented by Jaime Jiménez, it implements
# https://datatracker.ietf.org/doc/html/draft-ietf-core-coap-pubsub-12

import datetime
import logging
import json
import asyncio
import aiocoap.resource as resource
import aiocoap
import secrets
import cbor2
from aiocoap import Message, BAD_REQUEST
from aiocoap.numbers import ContentFormat

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
    
    def get_topic_resources(self):
        """Return a dictionary of TopicResource instances in the site."""
        return {path: resource for path, resource in self.root._resources.items() if isinstance(resource, TopicResource)}

    def remove_resource(self, path):
        link = f'<{path}>;rt="core.ps.conf"'
        self.content = self.content.replace(link, '')
        if ',,' in self.content:
            self.content = self.content.replace(',,', ',')
        if self.content.startswith(','):
            self.content = self.content[1:]
        if self.content.endswith(','):
            self.content = self.content[:-1]

    # Method for handling POST requests
    async def render_post(self, request):
        print('POST payload: %s' % request.payload)
        data = json.loads(request.payload)

        topic_config_path = f'ps/{secrets.token_hex(3)}'
        topic_data_path = f'ps/data/{secrets.token_hex(3)}d'
        config_path_segments = topic_config_path.split('/')
        data_path_segments = topic_data_path.split('/')

        topic_config_json = {
            "topic-name": data["topic-name"],
            "topic-data": topic_data_path,
            "resource-type": "core.ps.conf",
            "media-type": data.get("media-type", None), # default is None if not provided
            "topic-type": data.get("topic-type", None), # default is None if not provided
            "expiration-date": data.get("expiration-date", None), # default is None if not provided
            "max-subscribers": data.get("max-subscribers", None), # default is None if not provided
            "observer-check": data.get("observer-check", 86400) # default is 86400 if not provided
        }

        self.root.add_resource(config_path_segments, TopicResource(topic_config_json, self.root, config_path_segments))
        self.root.add_resource(data_path_segments, TopicDataResource())

        new_link = f'<{topic_config_path}>;rt="core.ps.conf"'
        if self.content:
            self.content += ',' + new_link
        else:
            self.content = new_link

        json_payload_bytes = json.dumps(topic_config_json).encode('utf-8')
        response = aiocoap.Message(code=aiocoap.CREATED, payload=json_payload_bytes)
        response.opt.location_path = topic_config_path.split('/')
        response.opt.content_format = aiocoap.numbers.media_types_rev["application/json"]

        return response

    # Method for handling GET requests
    async def render_get(self, request):
        response = aiocoap.Message(payload=self.content.encode('UTF-8'))
        response.opt.content_format = aiocoap.numbers.media_types_rev["application/link-format"]
        return response
    
    # Method for handling FETCH requests
    async def render_fetch(self, request):
        try:
            print('FETCH payload: %s' % request.payload)
            
            # Decode the request payload and convert it from CBOR to JSON
            request_data = cbor2.loads(request.payload)

            # Create a list to store the links to the resources that match the filter
            matching_links = []

            # Get the TopicResource instances in the site
            topic_resources = self.get_topic_resources()

            # Check each TopicResource
            for path, resource in topic_resources.items():
                path_str = '/'.join(path)
                # Print the resource and its content
                content = json.loads(resource.content.decode('utf-8'))
                print(f'Resource: {path_str}, Content: {content}')
                # Check if the resource matches the filter
                if resource.matches(request_data):
                    # Add the link to the matching resource to the list
                    matching_links.append(f'<{path_str}>;rt="core.ps.conf"')

            # Convert the list of links to a string
            payload = ','.join(matching_links)
            
            # Debug print statement
            print('Matching links:', matching_links)
            
            # Create the response message
            response = Message(code=aiocoap.CONTENT, payload=payload.encode('utf-8'))
            response.opt.content_format = 40

            return response

        except Exception as e:
            # If there's an error, return a 4.00 Bad Request response
            return Message(code=BAD_REQUEST, payload=str(e).encode('utf-8'))


# Define a resource class for topic configurations
class TopicResource(resource.ObservableResource):

    def __init__(self, content, site, path):
        super().__init__()
        self.handle = None
        self.content = json.dumps(content).encode('utf-8')
        self.ct = content.get('media-type', 'application/link-format') # default is 'application/link-format' if not provided
        self.rt = "core.ps.conf"
        self.site = site
        self.path = path
    
    def matches(self, filter):
        # Load the content of the resource as a JSON object
        content = json.loads(self.content.decode('utf-8'))

        print('Content:', content)  # Debug print statement

        # Check each key-value pair in the filter
        for key, value in filter.items():
            # If the key is not in the resource's content or the values don't match, return False
            if key not in content:
                print(f'Key {key} not found in content')  # Debug print statement
                return False
            elif str(content[key]) != str(value):
                print(f'Mismatch: key {key}, content value {content[key]}, filter value {value}')  # Debug print statement
                return False

        print('Match:', content)  # Debug print statement
        # If all key-value pairs in the filter match, return True
        return True

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

    async def render_put(self, request):
        print('PUT payload: %s' % request.payload)
        data = json.loads(request.payload)

        # Check if the immutable parameters are being changed
        if "topic-name" in data or "topic-data" in data or "resource-type" in data:
            return aiocoap.Message(code=aiocoap.BAD_REQUEST)

        # Update the content of the TopicResource
        content_dict = json.loads(self.content.decode('utf-8'))

        if 'media-type' in data:
            content_dict['media-type'] = data['media-type']

        if 'topic-type' in data:
            content_dict['topic-type'] = data['topic-type']

        if 'expiration-date' in data:
            content_dict['expiration-date'] = data['expiration-date']

        if 'max-subscribers' in data:
            content_dict['max-subscribers'] = data['max-subscribers']

        self.content = json.dumps(content_dict).encode('utf-8')

        # Create the response message
        response = aiocoap.Message(code=aiocoap.CHANGED, payload=self.content)
        response.opt.content_format = aiocoap.numbers.media_types_rev["application/json"]

        return response

    async def render_ipatch(self, request):
        try:
            print('iPATCH payload: %s' % request.payload)
            data = json.loads(request.payload)
        except json.JSONDecodeError:
            return aiocoap.Message(code=aiocoap.BAD_REQUEST)

        # Check if the immutable parameters are being changed
        immutable_params = ["topic-name", "topic-data", "resource-type"]
        if any(param in data for param in immutable_params):
            return aiocoap.Message(code=aiocoap.BAD_REQUEST)

        # Update the content of the TopicResource
        try:
            content_dict = json.loads(self.content.decode('utf-8'))
        except json.JSONDecodeError:
            return aiocoap.Message(code=aiocoap.INTERNAL_SERVER_ERROR)

        # Update only the fields that are present in the request
        for field in data:
            if field in content_dict:
                content_dict[field] = data[field]
            else:
                return aiocoap.Message(code=aiocoap.NOT_FOUND)

        self.content = json.dumps(content_dict).encode('utf-8')

        # Create the response message
        response = aiocoap.Message(code=aiocoap.CHANGED, payload=self.content)
        response.opt.content_format = aiocoap.numbers.media_types_rev["application/json"]

        return response


    # Method for handling GET requests
    async def render_get(self, request):
        if not self.content:
            return aiocoap.Message(code=aiocoap.NOT_FOUND)
        else:
            return aiocoap.Message(payload=self.content)

    # Method for handling DELETE requests
    async def render_delete(self, request):
        # Remove this resource from the site
        self.site.remove_resource(self.path)

        # Decode the bytes to a string and then convert it to a dictionary
        content_dict = json.loads(self.content.decode('utf-8'))

        # Remove the associated topic-data resource from the site
        topic_data_path = content_dict['topic-data'].split('/')
        self.site.remove_resource(topic_data_path)
        # Update the CollectionResource
        collection_resource = self.site._resources['ps',]
        collection_resource.remove_resource("/".join(self.path))

        # Unsubscribe all subscribers by removing them from the list of observers
        for observer in self._observations:
            observer.deregister("Resource not found", aiocoap.NOT_FOUND)

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