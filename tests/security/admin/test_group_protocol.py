import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from admin_sync.exceptions import SyncError

from aurora.security.admin import GroupProtocol
from testutils.factories import GroupFactory


User = get_user_model()


@pytest.fixture
def group_protocol():
    return GroupProtocol()


@pytest.fixture
def groups_list(db):
    return [
        GroupFactory(name="Group1"),
        GroupFactory(name="Group2"),
        GroupFactory(name="Group3"),
    ]


@pytest.fixture
def groups_queryset(db, groups_list):
    return Group.objects.filter(pk__in=[g.pk for g in groups_list])


def test_group_protocol_collect_with_valid_groups(group_protocol, groups_list):
    result = group_protocol.collect(groups_list)

    assert isinstance(result, list)
    assert len(result) == len(groups_list)
    assert all(isinstance(group, Group) for group in result)


@pytest.mark.django_db
def test_group_protocol_collect_with_queryset(group_protocol, groups_queryset):
    result = group_protocol.collect(groups_queryset)

    assert isinstance(result, list)
    assert len(result) == groups_queryset.count()


def test_group_protocol_collect_with_empty_data(group_protocol):
    with pytest.raises(SyncError, match="Empty queryset"):
        group_protocol.collect(None)

    with pytest.raises(SyncError, match="Empty queryset"):
        group_protocol.collect([])


@pytest.mark.django_db
def test_group_protocol_collect_with_invalid_data_type(group_protocol, user):
    invalid_data = [user]

    with pytest.raises(ValueError, match="GroupProtocol can be used only for Registration"):
        group_protocol.collect(invalid_data)
