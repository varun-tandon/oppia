# coding: utf-8
#
# Copyright 2014 The Oppia Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for core.storage.feedback.gae_models."""

import types

from core.domain import feedback_services
from core.platform import models
from core.tests import test_utils
import feconf

(feedback_models,) = models.Registry.import_models([models.NAMES.feedback])

CREATED_ON_FIELD = 'created_on'
LAST_UPDATED_FIELD = 'last_updated'
DELETED_FIELD = 'deleted'
FIELDS_NOT_REQUIRED = [CREATED_ON_FIELD, LAST_UPDATED_FIELD, DELETED_FIELD]


class FeedbackThreadModelTest(test_utils.GenericTestBase):
    """Tests for the GeneralFeedbackThreadModel class."""

    def test_put_function(self):
        feedback_thread_model = feedback_models.GeneralFeedbackThreadModel(
            entity_type=feconf.ENTITY_TYPE_EXPLORATION, entity_id='exp_id_1',
            subject='dummy subject', message_count=0)
        
        feedback_thread_model.put()

        last_updated = feedback_thread_model.last_updated

        # If we do not wish to update the last_updated time, we should set
        # the update_last_updated_time argument to False in the put function.
        feedback_thread_model.put(update_last_updated_time=False)
        self.assertEqual(feedback_thread_model.last_updated, last_updated)

        # If we do wish to change it however, we can simply use the put function
        # as the default value of update_last_updated_time is True.
        feedback_thread_model.put()
        self.assertNotEqual(feedback_thread_model.last_updated, last_updated)

    def test_raise_exception_by_mocking_collision(self):
        feedback_thread_model_cls = feedback_models.GeneralFeedbackThreadModel
        # Test create method.
        with self.assertRaisesRegexp(
            Exception, 'Feedback thread ID conflict on create.'):
            # Swap dependent method get_by_id to simulate collision every time.
            with self.swap(
                feedback_thread_model_cls, 'get_by_id',
                types.MethodType(
                    lambda x, y: True,
                    feedback_thread_model_cls)):
                feedback_thread_model_cls.create(
                    'exploration.exp_id.thread_id')

        # Test generate_new_thread_id method.
        with self.assertRaisesRegexp(
            Exception,
            'New thread id generator is producing too many collisions.'):
            # Swap dependent method get_by_id to simulate collision every time.
            with self.swap(
                feedback_thread_model_cls, 'get_by_id',
                types.MethodType(
                    lambda x, y: True,
                    feedback_thread_model_cls)):
                feedback_thread_model_cls.generate_new_thread_id(
                    'exploration', 'exp_id')

    def test_export_data_nontrivial(self):
        # Set up testing varibles
        TEST_EXPORT_ENTITY_TYPE = feconf.ENTITY_TYPE_EXPLORATION
        TEST_EXPORT_ENTITY_ID = 'exp_id_2'
        TEST_EXPORT_AUTHOR_ID = 'user_1'
        TEST_EXPORT_STATUS = 'open'
        TEST_EXPORT_SUBJECT = 'dummy subject'
        TEST_EXPORT_HAS_SUGGESTION = True
        TEST_EXPORT_SUMMARY = 'This is a great summary.'
        TEST_EXPORT_MESSAGE_COUNT = 0

        feedback_thread_model = feedback_models.GeneralFeedbackThreadModel(
            entity_type=TEST_EXPORT_ENTITY_TYPE, 
            entity_id=TEST_EXPORT_ENTITY_ID,
            original_author_id=TEST_EXPORT_AUTHOR_ID,
            status=TEST_EXPORT_STATUS,
            subject=TEST_EXPORT_SUBJECT,
            has_suggestion=TEST_EXPORT_HAS_SUGGESTION,
            summary=TEST_EXPORT_SUMMARY,
            message_count=TEST_EXPORT_MESSAGE_COUNT
        )
        
        feedback_thread_model.put()
        last_updated = feedback_thread_model.last_updated

        user_data = feedback_models.GeneralFeedbackThreadModel.export_data('user_1')
        test_data = {
            str(feedback_thread_model.id): {
                'entity_type': TEST_EXPORT_ENTITY_TYPE,
                'entity_id': TEST_EXPORT_ENTITY_ID,
                'status': TEST_EXPORT_STATUS,
                'subject': TEST_EXPORT_SUBJECT,
                'has_suggestion': TEST_EXPORT_HAS_SUGGESTION,
                'summary': TEST_EXPORT_SUMMARY,
                'message_count': TEST_EXPORT_MESSAGE_COUNT,
                'last_updated': feedback_thread_model.last_updated
            }
        }
        self.assertEqual(user_data, test_data)

class GeneralFeedbackMessageModelTests(test_utils.GenericTestBase):
    """Tests for the GeneralFeedbackMessageModel class."""

    def test_raise_exception_by_mocking_collision(self):
        with self.assertRaisesRegexp(
            Exception, 'Feedback message ID conflict on create.'):
            # Swap dependent method get_by_id to simulate collision every time.
            with self.swap(
                feedback_models.GeneralFeedbackMessageModel, 'get_by_id',
                types.MethodType(
                    lambda x, y: True,
                    feedback_models.GeneralFeedbackMessageModel)):
                feedback_models.GeneralFeedbackMessageModel.create(
                    'thread_id', 'message_id')

    def test_get_all_messages(self):
        thread_id = feedback_services.create_thread(
            'exploration', '0', None, 'subject 1', 'text 1')

        feedback_services.create_message(
            thread_id, None, 'open', 'subject 2', 'text 2')

        model = feedback_models.GeneralFeedbackMessageModel.get(
            thread_id, 0)
        self.assertEqual(model.entity_type, 'exploration')

        all_messages = (
            feedback_models.GeneralFeedbackMessageModel
            .get_all_messages(2, None))

        self.assertEqual(len(all_messages[0]), 2)

        self.assertEqual(all_messages[0][0].thread_id, thread_id)
        self.assertEqual(all_messages[0][0].entity_id, '0')
        self.assertEqual(all_messages[0][0].entity_type, 'exploration')
        self.assertEqual(all_messages[0][0].text, 'text 2')
        self.assertEqual(all_messages[0][0].updated_subject, 'subject 2')

        self.assertEqual(all_messages[0][1].thread_id, thread_id)
        self.assertEqual(all_messages[0][1].entity_id, '0')
        self.assertEqual(all_messages[0][1].entity_type, 'exploration')
        self.assertEqual(all_messages[0][1].text, 'text 1')
        self.assertEqual(all_messages[0][1].updated_subject, 'subject 1')

    def test_get_most_recent_message(self):
        thread_id = feedback_services.create_thread(
            'exploration', '0', None, 'subject 1', 'text 1')

        feedback_services.create_message(
            thread_id, None, 'open', 'subject 2', 'text 2')

        model1 = feedback_models.GeneralFeedbackMessageModel.get(
            thread_id, 0)

        self.assertEqual(model1.entity_type, 'exploration')

        message = (
            feedback_models.GeneralFeedbackMessageModel
            .get_most_recent_message(thread_id))

        self.assertEqual(message.thread_id, thread_id)
        self.assertEqual(message.entity_id, '0')
        self.assertEqual(message.entity_type, 'exploration')
        self.assertEqual(message.text, 'text 2')
        self.assertEqual(message.updated_subject, 'subject 2')


class FeedbackThreadUserModelTest(test_utils.GenericTestBase):
    """Tests for the FeedbackThreadUserModel class."""

    def test_create_new_object(self):
        feedback_models.GeneralFeedbackThreadUserModel.create(
            'user_id', 'exploration.exp_id.thread_id')
        feedback_thread_user_model = (
            feedback_models.GeneralFeedbackThreadUserModel.get(
                'user_id', 'exploration.exp_id.thread_id'))

        self.assertEqual(
            feedback_thread_user_model.id,
            'user_id.exploration.exp_id.thread_id')
        self.assertEqual(
            feedback_thread_user_model.message_ids_read_by_user, [])

    def test_get_object(self):
        feedback_models.GeneralFeedbackThreadUserModel.create(
            'user_id', 'exploration.exp_id.thread_id')
        expected_model = feedback_models.GeneralFeedbackThreadUserModel(
            id='user_id.exploration.exp_id.thread_id',
            message_ids_read_by_user=[])

        actual_model = (
            feedback_models.GeneralFeedbackThreadUserModel.get(
                'user_id', 'exploration.exp_id.thread_id'))

        self.assertEqual(actual_model.id, expected_model.id)
        self.assertEqual(
            actual_model.message_ids_read_by_user,
            expected_model.message_ids_read_by_user)

    def test_get_multi(self):
        feedback_models.GeneralFeedbackThreadUserModel.create(
            'user_id', 'exploration.exp_id.thread_id_1')
        feedback_models.GeneralFeedbackThreadUserModel.create(
            'user_id', 'exploration.exp_id.thread_id_2')

        expected_model_1 = feedback_models.GeneralFeedbackThreadUserModel(
            id='user_id.exploration.exp_id.thread_id_1',
            message_ids_read_by_user=[])
        expected_model_2 = feedback_models.GeneralFeedbackThreadUserModel(
            id='user_id.exploration.exp_id.thread_id_2',
            message_ids_read_by_user=[])

        actual_models = (
            feedback_models.GeneralFeedbackThreadUserModel.get_multi(
                'user_id',
                ['exploration.exp_id.thread_id_1',
                 'exploration.exp_id.thread_id_2']))

        actual_model_1 = actual_models[0]
        actual_model_2 = actual_models[1]

        self.assertEqual(actual_model_1.id, expected_model_1.id)
        self.assertEqual(
            actual_model_1.message_ids_read_by_user,
            expected_model_1.message_ids_read_by_user)

        self.assertEqual(actual_model_2.id, expected_model_2.id)
        self.assertEqual(
            actual_model_2.message_ids_read_by_user,
            expected_model_2.message_ids_read_by_user)


class UnsentFeedbackEmailModelTest(test_utils.GenericTestBase):
    """Tests for FeedbackMessageEmailDataModel class."""

    def test_new_instances_stores_correct_data(self):
        user_id = 'A'
        message_reference_dict = {
            'exploration_id': 'ABC123',
            'thread_id': 'thread_id1',
            'message_id': 'message_id1'
        }
        email_instance = feedback_models.UnsentFeedbackEmailModel(
            id=user_id, feedback_message_references=[message_reference_dict])
        email_instance.put()

        retrieved_instance = (
            feedback_models.UnsentFeedbackEmailModel.get_by_id(id=user_id))

        self.assertEqual(
            retrieved_instance.feedback_message_references,
            [message_reference_dict])
        self.assertEqual(retrieved_instance.retries, 0)
