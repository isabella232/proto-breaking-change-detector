# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.api.resource_pb2 import ResourceDescriptor
from typing import Sequence


class ResourceDatabase:
    # Create resource database for file-level and messasge-level resouce definitions.
    # It has two dictionaries: types map and patterns map. Register a resource will put
    # [typeStr, resource_messsage] in types dict, and [pattern0, resource_message]
    # [pattern1, ressource_message] (if it has multiple patterns) in patterns dict."""
    def __init__(self):
        self.types = {}
        self.patterns = {}

    def register_resource(self, resource_message: ResourceDescriptor):
        """ Register a resource in the database. """
        if not resource_message:
            return
        if not resource_message.type or not resource_message.pattern:
            raise TypeError(
                "APIs must define a resource type and resource pattern for each resource in the API."
            )
        self.types[resource_message.type] = resource_message
        self.patterns.update(
            (pattern, resource_message) for pattern in resource_message.pattern
        )

    def get_resource_by_type(self, type):
        """ Query the resource by type. Return None if the resource is not existing. """
        return self.types.get(type, None)

    def get_parent_resources_by_child_type(self, type) -> Sequence[ResourceDescriptor]:
        """Query the resources by child_type. Return [] if the parent resource is not existing."""
        result = []
        if not type:
            return result
        child_resource = self.get_resource_by_type(type)
        # The child_type is not existing in the database.
        if not child_resource or not child_resource.pattern:
            return result
        # For each child_type pattern, split the pattern by '/'
        # and reconstruct the segments. If any parent pattern is existing
        # in the database, put it in the result sequence.
        # For example: `a/{a}` is the parent resource of `a/{a}/b{b}`
        for child_pattern in child_resource.pattern:
            pattern = ""
            for segment in child_pattern.split("/"):
                if pattern != "":
                    pattern = pattern + "/"
                pattern = pattern + segment
                parent = self.get_resource_by_pattern(pattern)
                # Check the parent resource is not child_resource itself.
                if parent and (parent.type != child_resource.type):
                    result.append(parent)
        return result

    def get_resource_by_pattern(self, pattern):
        """ Query the resource by pattern. Return None if the resource is not existing. """
        return self.patterns.get(pattern, None)