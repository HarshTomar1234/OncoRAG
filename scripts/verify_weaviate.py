from oncopilot.retrieval.client import weaviate_client


def main() -> None:
    with weaviate_client() as client:
        print("is_ready:", client.is_ready())
        print("weaviate version:", client.get_meta()["version"])


if __name__ == "__main__":
    main()
