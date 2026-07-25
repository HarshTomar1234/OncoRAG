from contextlib import contextmanager

import weaviate
from weaviate.classes.init import Auth

from oncopilot.config.settings import settings


@contextmanager
def weaviate_client():
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=settings.weaviate_url,
        auth_credentials=Auth.api_key(settings.weaviate_api_key),
    )
    try:
        yield client
    finally:
        client.close()
