# main_scrapper.py
from ..scrapping.scrapper import AudibleScrapper
import argparse


def main(limit=10):
    """Scraps more audio-books towards Neo4J."""
    scrapper = AudibleScrapper()
    scrapper.random_walk(limit=limit, verbose=True)
    print(
        "Database now contains {} scrapped books.".format(
            scrapper.data_manager.count_scrapped_books()
        )
    )


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-l", "--limit", help="Max number of books that shoud be scrapped."
    )
    args = parser.parse_args()
    config = vars(args)
    main(limit=int(config["limit"]))
