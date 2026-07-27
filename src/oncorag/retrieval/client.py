from contextlib import contextmanager

import weaviate
from weaviate.classes.init import AdditionalConfig, Auth, Timeout

from oncorag.config.settings import settings


@contextmanager
def weaviate_client():
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=settings.weaviate_url,
        auth_credentials=Auth.api_key(settings.weaviate_api_key),
        additional_config=AdditionalConfig(timeout=Timeout(init=30, query=60, insert=120)),
    )
    try:
        yield client
    finally:
        client.close()
