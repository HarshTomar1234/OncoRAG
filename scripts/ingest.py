import logging

from oncorag.ingestion.pipeline import run

logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    run()
