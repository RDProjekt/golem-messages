import enum
import functools

from golem_messages import datastructures

from . import base
from . import tasks


CONCENT_MSG_BASE = 4000


class ServiceRefused(base.Message):
    TYPE = CONCENT_MSG_BASE

    @enum.unique
    class Reason(enum.Enum):
        TOO_SMALL_COMMUNICATION_PAYMENT = 'TOO_SMALL_COMMUNICATION_PAYMENT'
        TOO_SMALL_REQUESTOR_DEPOSIT = 'TOO_SMALL_REQUESTOR_DEPOSIT'
        TOO_SMALL_PROVIDER_DEPOSIT = 'TOO_SMALL_PROVIDER_DEPOSIT'
        SYSTEM_OVERLOADED = 'SYSTEM_OVERLOADED'

    ENUM_SLOTS = {
        'reason': Reason,
    }

    __slots__ = [
        'subtask_id',
        'reason',
        'task_to_compute',
    ] + base.Message.__slots__

    def deserialize_slot(self, key, value):
        value = super().deserialize_slot(key, value)
        return tasks.deserialize_task_to_compute(key, value)


class ForceReportComputedTask(base.Message):
    TYPE = CONCENT_MSG_BASE + 1

    __slots__ = [
        'task_to_compute',
        'result_hash',
    ] + base.Message.__slots__

    def deserialize_slot(self, key, value):
        value = super().deserialize_slot(key, value)
        return tasks.deserialize_task_to_compute(key, value)


class AckReportComputedTask(base.Message):
    TYPE = CONCENT_MSG_BASE + 2

    __slots__ = [
        'subtask_id',
        'task_to_compute',
    ] + base.Message.__slots__

    def deserialize_slot(self, key, value):
        value = super().deserialize_slot(key, value)
        return tasks.deserialize_task_to_compute(key, value)


class RejectReportComputedTask(base.Message):
    TYPE = CONCENT_MSG_BASE + 3

    @enum.unique
    class Reason(enum.Enum):
        """
        since python 3.6 it's possible to do this:

        class StringEnum(str, enum.Enum):
            def _generate_next_value_(name: str, *_):
                return name

        @enum.unique
        class Reason(StringEnum):
            TASK_TIME_LIMIT_EXCEEDED = enum.auto()
            SUBTASK_TIME_LIMIT_EXCEEDED = enum.auto()
            GOT_MESSAGE_CANNOT_COMPUTE_TASK = enum.auto()
            GOT_MESSAGE_TASK_FAILURE = enum.auto()
        """
        TASK_TIME_LIMIT_EXCEEDED = 'TASK_TIME_LIMIT_EXCEEDED'
        SUBTASK_TIME_LIMIT_EXCEEDED = 'SUBTASK_TIME_LIMIT_EXCEEDED'
        GOT_MESSAGE_CANNOT_COMPUTE_TASK = 'GOT_MESSAGE_CANNOT_COMPUTE_TASK'
        GOT_MESSAGE_TASK_FAILURE = 'GOT_MESSAGE_TASK_FAILURE'

    ENUM_SLOTS = {
        'reason': Reason,
    }

    __slots__ = [
        'subtask_id',
        'reason',
        'task_to_compute',
        'task_failure',
        'cannot_compute_task',
    ] + base.Message.__slots__

    def deserialize_slot(self, key, value):
        value = super().deserialize_slot(key, value)
        value = tasks.deserialize_task_to_compute(key, value)
        value = deserialize_task_failure(key, value)
        value = deserialize_cannot_compute_task(key, value)
        return value


class VerdictReportComputedTask(base.Message):
    TYPE = CONCENT_MSG_BASE + 4

    __slots__ = [
        'force_report_computed_task',
        'ack_report_computed_task',
    ] + base.Message.__slots__

    def deserialize_slot(self, key, value):
        value = super().deserialize_slot(key, value)
        value = deserialize_force_report_computed_task(key, value)
        value = deserialize_ack_report_computed_task(key, value)
        return value


class FileTransferToken(base.Message):
    TYPE = CONCENT_MSG_BASE + 5

    __slots__ = [
        'subtask_id',
        'token_expiration_deadline',
        'storage_cluster_address',
        'authorized_client_public_key',
        'operation',
        'files',
    ] + base.Message.__slots__

    def deserialize_slot(self, key, value):
        value = super().deserialize_slot(key, value)
        if key == 'files':
            value = [FileTransferToken.FileInfo(f) for f in value]
        return value

    class FileInfo(datastructures.FrozenDict):
        """Represents SUBTASK metadata."""
        ITEMS = {
            'path': '',
            'checksum': '',
            'size': 0,
        }

class SubtaskResultVerify(base.Message):
    """
    Message sent from a Provider to the Concent, requesting additional
    verification in case the result had been rejected by the Requestor

    :param (slot)SubtaskResultRejected subtask_result_rejected:
           the original reject message

    """
    TYPE = CONCENT_MSG_BASE + 6

    __slots__ = [
        'subtask_result_rejected',
    ] + base.Message.__slots__

    def deserialize_slot(self, key, value):
        return base.deserialize_verify(
            key,
            super().deserialize_slot(key, value),
            verify_key='subtask_result_rejected',
            verify_class=tasks.SubtaskResultRejected
        )

class AckSubtaskResultVerify(base.Message):
    """
    Message sent from the Concent to the Provider to acknowledge reception
    of the `SubtaskResultVerify` message
    """
    TYPE = CONCENT_MSG_BASE + 7

    __slots__ = [
        'subtask_result_verify',
    ] + base.Message.__slots__

    def deserialize_slot(self, key, value):
        return base.deserialize_verify(
            key,
            super().deserialize_slot(key, value),
            verify_key='subtask_result_verify',
            verify_class=SubtaskResultVerify
        )

class SubtaskResultSettled(base.Message):
    """
    Message sent from the Concent to both the Provider and the Requestor
    informing of positive acceptance of the results by the Concent and the
    fact that the payment has been force-sent to the Provider

    :param (slot)str origin: the origin of the `SubtaskResultVerify` message
                             that triggered the Concent action

    :param (slot)TaskToCompute task_to_compute: TTF containing the task
                                                that the settlement
                                                pertains to

    """

    TYPE = CONCENT_MSG_BASE + 8

    @enum.unique
    class Origin(enum.Enum):
        ResultsAcceptedTimeout = 'results_accepted_timeout'
        ResultsRejected = 'results_rejected'

    ENUM_SLOTS = {
        'origin': Origin,
    }

    __slots__ = [
        'origin',
        'task_to_compute',
    ] + base.Message.__slots__

    def deserialize_slot(self, key, value):
        return base.deserialize_verify(
            key,
            super().deserialize_slot(key, value),
            verify_key='task_to_compute',
            verify_class=tasks.TaskToCompute,
        )


deserialize_task_failure = functools.partial(
    base.deserialize_verify,
    verify_key='task_failure',
    verify_class=tasks.TaskFailure,
)

deserialize_cannot_compute_task = functools.partial(
    base.deserialize_verify,
    verify_key='cannot_compute_task',
    verify_class=tasks.CannotComputeTask,
)

deserialize_force_report_computed_task = functools.partial(
    base.deserialize_verify,
    verify_key='force_report_computed_task',
    verify_class=ForceReportComputedTask,
)

deserialize_ack_report_computed_task = functools.partial(
    base.deserialize_verify,
    verify_key='ack_report_computed_task',
    verify_class=AckReportComputedTask,
)
