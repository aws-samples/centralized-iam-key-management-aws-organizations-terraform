

"""Get AWS Partition.

This module grabs the environment partition
and the endpoint resolver
"""

import re
import boto3

def _get_endpoint_resolver():
    session = boto3._get_default_session()
    endpoint_resolver = session._session._get_internal_component(
        'endpoint_resolver')
    return endpoint_resolver


def get_partition_for_region(region_name=None):
    endpoint_resolver = _get_endpoint_resolver()
    for partition in endpoint_resolver._endpoint_data['partitions']:
        if region_name in partition['regions']:
            return partition['partition']
        if 'regionRegex' not in partition:
            continue
        if re.compile(partition['regionRegex']).match(region_name):
            return partition['partition']
    raise ValueError('Invalid region name: {0}'.format(region_name))


def get_partition_name(partition_id=None):
    endpoint_resolver = _get_endpoint_resolver()
    for partition in endpoint_resolver._endpoint_data['partitions']:
        if partition_id == partition['partition']:
            return partition['partitionName']
    raise ValueError('Invalid partition: {0}'.format(partition_id))


def get_iam_region(partition_id=None):
    endpoint_resolver = _get_endpoint_resolver()
    for partition in endpoint_resolver._endpoint_data['partitions']:
        if partition_id == partition['partition']:
            iam = partition['services']['iam']
            partition_endpoint = iam['partitionEndpoint']
            return iam['endpoints'][partition_endpoint]['credentialScope'][
                'region']
    raise ValueError('Invalid partition: {0}'.format(partition_id))


def get_partition_regions(partition_id=None):
    endpoint_resolver = _get_endpoint_resolver()
    for partition in endpoint_resolver._endpoint_data['partitions']:
        if partition_id == partition['partition']:
            regions = partition['regions'].keys()
            return regions
    raise ValueError('Invalid partition: {0}'.format(partition_id))
