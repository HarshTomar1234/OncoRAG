from oncorag.retrieval.client import weaviate_client
from oncorag.retrieval.schema import create_collections


def main() -> None:
    with weaviate_client() as client:
        create_collections(client)
        print("Collections created:", client.collections.list_all().keys())


if __name__ == "__main__":
    main()
