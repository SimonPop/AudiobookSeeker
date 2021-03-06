from requests_html import HTMLSession
import warnings
from collections import deque
from time import sleep
from ..graph.audible_book import AudibleBook
from ..graph.data_manager import DataManager

warnings.filterwarnings("ignore")


class AudibleScrapper:
    def __init__(self, df_path="audible_raw_data.csv"):
        self.base_audible = "https://www.audible.com"
        self.categories_url = "https://www.audible.com/categories?ref=a_pd_Americ_t1_navTop_pl0cg0c0r5&pf_rd_p=2774f9d8-d3de-47f2-8c6a-6a59524b5923&pf_rd_r=ZS5GW1KHJ8NGV7PSA3N3"
        self.sess = HTMLSession()

        self.data_manager = DataManager()

    def get_all_categories(self, base_url):
        """Gets links for each category."""
        r = self.sess.get(base_url)

        genres = r.html.find("div.bc-col-responsive.bc-col-3")
        cat_items = []
        cat_names = []

        for genre in genres:
            items = genre.find("ul.bc-list")[0].find("li.bc-list-item")
            cat_items.extend(items)

        cat_names = [item.text.split(" (")[0] for item in cat_items]

        return cat_items, cat_names

    def get_page_list(self, category_link):
        """Gets the link for a page of books a given category."""

        r = self.sess.get(category_link)
        all_link = r.html.find(".allInCategoryPageLink", first=True).attrs["href"]

        return all_link

    def crawl_category_page(self, category_all_link, page=0):
        """Get the links of all books in a page of a given category."""

        r = self.sess.get(category_all_link)  # TODO: add page number
        book_links = r.html.find("li.bc-list-item.productListItem", first=False)

        return book_links

    def parse_page(self, page_link):
        """Parse an audible book's page."""
        self.close_session()
        self.sess = HTMLSession()

        r = self.sess.get(page_link, allow_redirects=False)

        return AudibleBook().create_book_from_request(r, page_link)

    def close_session(self):
        self.sess.close()

    def random_walk(
        self, starting_link=None, limit=10, results={}, sleep_time=1, verbose=False
    ):

        if starting_link is None:
            starting_link = self.data_manager.get_unscrapped_links()[0]

        next_links = deque([starting_link])
        scrapped_ids = self.data_manager.get_scrapped_ids()
        results = dict([(i, None) for i in scrapped_ids])
        len_offset = len(results)

        while len(next_links) > 0 and len(results) < limit + len_offset:
            link = next_links.pop()
            if not link.startswith(self.base_audible):
                link = self.base_audible + link

            id = link.split("/")[5].split("?")[0]

            if id not in results:
                if verbose:
                    print("Currently scrapping {}...".format(id))
                try:
                    book = self.parse_page(link)
                    results[id] = book
                    self.store(book)
                    next_links.extend([self.base_audible + l for l in book.links])
                    sleep(sleep_time)
                except:
                    print("Impossible to parse page {}".format(link))
                    results[id] = None

        return results

    def store(self, book: AudibleBook):
        """Stores the book in a Data Base."""
        self.data_manager.store_book(book)
        for target_id, link in zip(book.recommendation_ids, book.links):
            self.data_manager.create_place_holder(target_id, link)
            self.data_manager.create_link(book.id, target_id)
