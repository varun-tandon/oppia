# coding: utf-8
#
# Copyright 2020 The Oppia Authors. All Rights Reserved.
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

"""One-off jobs for suggestions."""

from __future__ import absolute_import  # pylint: disable=import-only-modules
from __future__ import unicode_literals  # pylint: disable=import-only-modules

from core import jobs
from core.platform import models

(
    base_models, config_models, collection_models, exploration_models,
    skill_models, story_models, topic_models,
    question_models
) = models.Registry.import_models([
    models.NAMES.base_model, models.NAMES.config, models.NAMES.collection,
    models.NAMES.exploration, models.NAMES.skill, models.NAMES.story,
    models.NAMES.topic, models.NAMES.question
])

class SnapshotMetadataCommitMsgAuditOneOffJob(
    jobs.BaseMapReduceOneOffJobManager):
    """Job that audits the commit_message field of the
    BaseSnapshotMetadataModels to determine frequency of string sizes.
    """
    @classmethod
    def enqueue(cls, job_id, additional_job_params=None):
        super(SnapshotMetadataCommitMsgAuditOneOffJob, cls).enqueue(
            job_id, shard_count=8)
    
    @classmethod
    def entity_classes_to_map_over(cls):
        return [
            config_models.ConfigPropertySnapshotMetadataModel,
            collection_models.CollectionRightsSnapshotMetadataModel,
            collection_models.CollectionSnapshotMetadataModel,
            exploration_models.ExplorationRightsSnapshotMetadataModel,
            exploration_models.ExplorationSnapshotMetadataModel,
            skill_models.SkillSnapshotMetadataModel,
            story_models.StorySnapshotMetadataModel,
            topic_models.SubtopicPageSnapshotMetadataModel,
            topic_models.TopicRightsSnapshotMetadataModel,
            topic_models.TopicSnapshotMetadataModel,
            question_models.QuestionSnapshotMetadataModel,
        ]

    @staticmethod
    def map(item):
        model_name = item.__class__.__name__
        model_id = item.id
        identifier_message = '%s with id %s' % (model_name, model_id)
        if len(item.commit_message) < 1200:
            yield ('LESS_THAN_1200', identifier_message)
        elif len(item.commit_message) <= 1500:
            yield ('BETWEEN_1200_AND_1500', identifier_message)
        else:
            yield ('GREATER_THAN_1500', identifier_message)

    @staticmethod
    def reduce(key, values):
        if key == 'LESS_THAN_1200':
            yield (key, len(values))
        else:
            yield (key, values)


class SnapshotMetadataCommitMsgMigrationOneOffJob(
    jobs.BaseMapReduceOneOffJobManager):
    """Job that indexes the commit_message field of the
    BaseSnapshotMetadataModels.
    """

    @classmethod
    def enqueue(cls, job_id, additional_job_params=None):
        super(SnapshotMetadataCommitMsgMigrationOneOffJob, cls).enqueue(
            job_id, shard_count=8)

    @classmethod
    def entity_classes_to_map_over(cls):
        return [
            config_models.ConfigPropertySnapshotMetadataModel,
            collection_models.CollectionRightsSnapshotMetadataModel,
            collection_models.CollectionSnapshotMetadataModel,
            exploration_models.ExplorationRightsSnapshotMetadataModel,
            exploration_models.ExplorationSnapshotMetadataModel,
            skill_models.SkillSnapshotMetadataModel,
            story_models.StorySnapshotMetadataModel,
            topic_models.SubtopicPageSnapshotMetadataModel,
            topic_models.TopicRightsSnapshotMetadataModel,
            topic_models.TopicSnapshotMetadataModel,
            question_models.QuestionSnapshotMetadataModel,
        ]

    @staticmethod
    def map(item):
        try:
            item.put(update_last_updated_time=False)
        except Exception as e:
            yield ('FAILURE' + e.strerror, 1)
        else:
            yield ('SUCCESS', 1)

    @staticmethod
    def reduce(key, values):
        yield (key, len(values))
