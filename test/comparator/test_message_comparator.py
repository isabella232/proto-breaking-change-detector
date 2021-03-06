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

import unittest
from test.tools.invoker import UnittestInvoker
from src.comparator.message_comparator import DescriptorComparator
from src.comparator.wrappers import FileSet
from src.findings.finding_container import FindingContainer


class DescriptorComparatorTest(unittest.TestCase):
    # This is for tesing the behavior of src.comparator.message_comparator.DescriptorComparator class.
    # We use message_v1.proto and message_v1beta1.proto to mimic the original and next
    # versions of the API definition files (which has only one proto file in this case).
    # UnittestInvoker helps us to execute the protoc command to compile the proto file,
    # get a *_descriptor_set.pb file (by -o option) which contains the serialized data in protos, and
    # create a FileDescriptorSet (_PB_ORIGNAL and _PB_UPDATE) out of it.
    _PROTO_ORIGINAL = "message_v1.proto"
    _PROTO_UPDATE = "message_v1beta1.proto"
    _DESCRIPTOR_SET_ORIGINAL = "message_v1_descriptor_set.pb"
    _DESCRIPTOR_SET_UPDATE = "message_v1beta1_descriptor_set.pb"
    _INVOKER_ORIGNAL = UnittestInvoker([_PROTO_ORIGINAL], _DESCRIPTOR_SET_ORIGINAL)
    _INVOKER_UPDATE = UnittestInvoker([_PROTO_UPDATE], _DESCRIPTOR_SET_UPDATE)
    _PB_ORIGNAL = _INVOKER_ORIGNAL.run()
    _PB_UPDATE = _INVOKER_UPDATE.run()

    def setUp(self):
        # Get `Person` and `AddressBook` DescriptoProto from the
        # original and updated `*_descriptor_set.pb` files.
        self.person_msg = FileSet(self._PB_ORIGNAL).messages_map["Person"]
        self.person_msg_update = FileSet(self._PB_UPDATE).messages_map["Person"]
        self.addressBook_msg = FileSet(self._PB_ORIGNAL).messages_map["AddressBook"]
        self.addressBook_msg_update = FileSet(self._PB_UPDATE).messages_map[
            "AddressBook"
        ]

    def tearDown(self):
        FindingContainer.reset()

    def test_message_removal(self):
        DescriptorComparator(self.person_msg, None).compare()
        finding = FindingContainer.getAllFindings()[0]
        self.assertEqual(finding.message, "A message Person is removed")
        self.assertEqual(finding.category.name, "MESSAGE_REMOVAL")
        self.assertEqual(finding.location.path, "message_v1.proto Line: 5")

    def test_message_addition(self):
        DescriptorComparator(None, self.addressBook_msg).compare()
        finding = FindingContainer.getAllFindings()[0]
        self.assertEqual(finding.message, "A new message AddressBook is added.")
        self.assertEqual(finding.category.name, "MESSAGE_ADDITION")
        self.assertEqual(finding.location.path, "message_v1.proto Line: 27")

    def test_field_change(self):
        # There is field change in message `Person`. Type of field `id`
        # is changed from `int32` to `string`.
        DescriptorComparator(self.person_msg, self.person_msg_update).compare()
        findings_map = {f.message: f for f in FindingContainer.getAllFindings()}
        finding = findings_map[
            "Type of the field is changed, the original is TYPE_INT32, but the updated is TYPE_STRING"
        ]
        self.assertEqual(finding.category.name, "FIELD_TYPE_CHANGE")

    def test_nested_message_change(self):
        # Field `type` in the nested message `PhoneNumber` is removed.
        DescriptorComparator(self.person_msg, self.person_msg_update).compare()
        findings_map = {f.message: f for f in FindingContainer.getAllFindings()}
        finding = findings_map["A Field type is removed"]
        self.assertEqual(finding.category.name, "FIELD_REMOVAL")
        self.assertEqual(finding.location.path, "message_v1.proto Line: 18")

    def test_nested_enum_change(self):
        # EnumValue `SCHOOL` in the nested enum `PhoneType` is added.
        DescriptorComparator(self.person_msg, self.person_msg_update).compare()
        findings_map = {f.message: f for f in FindingContainer.getAllFindings()}
        finding = findings_map["A new EnumValue SCHOOL is added."]
        self.assertEqual(finding.category.name, "ENUM_VALUE_ADDITION")
        self.assertEqual(finding.location.path, "message_v1beta1.proto Line: 14")

    @classmethod
    def tearDownClass(cls):
        cls._INVOKER_ORIGNAL.cleanup()
        cls._INVOKER_UPDATE.cleanup()


if __name__ == "__main__":
    unittest.main()
