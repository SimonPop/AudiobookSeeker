import numpy as np
import re
from docarray import Document


class AudibleBook:
    def __init__(
        self,
        id=None,
        title=None,
        subtitle=None,
        author=None,
        narrator=None,
        stars=None,
        minutes=None,
        hours=None,
        ratings=None,
        links=None,
        link=None,
        recommendation_ids=None,
    ):
        self.id = id
        self.title = title
        self.subtitle = subtitle
        self.author = author
        self.narrator = narrator
        self.hours = hours
        self.minutes = minutes
        self.stars = stars
        self.ratings = ratings
        self.links = links
        self.link = link
        self.recommendation_ids = recommendation_ids

    def __str__(self) -> str:
        return """
        Audible Book : {} - {}
        ID: {}
        Author: {}
        Narrator: {}
        Stars: {}
        Ratings: {}
        Hours: {}
        Minutes: {}
        """.format(
            self.title,
            self.subtitle,
            self.id,
            self.author,
            self.narrator,
            self.stars,
            self.ratings,
            self.hours,
            self.minutes,
        )

    def create_book_from_request(self, r, url):
        self.id = url.split("/")[5].split("?")[0]
        self.link = url
        information_dict = self.parse_book(r)
        self.title = information_dict["title"]
        self.subtitle = information_dict["subtitle"]
        self.author = information_dict["author"]
        self.narrator = information_dict["narrator"]
        self.hours, self.minutes = information_dict["length"]
        self.stars = information_dict["stars"]
        self.links = information_dict["links"]
        self.ratings = information_dict["ratings"]
        self.recommendation_ids = information_dict["recommendations"]
        return self

    def parse_book(self, r):
        """Parse book information from given raw html result."""
        # Links / Recommendations.
        recommendation_ids, recommendation_links = AudibleBook._parse_recommendations(r)

        # Book information
        information_dict = AudibleBook._parse_book_info(r)

        information_dict["id"] = id
        information_dict["recommendations"] = recommendation_ids
        information_dict["links"] = recommendation_links

        # Raw -> Selected
        (
            information_dict["stars"],
            information_dict["ratings"],
        ) = AudibleBook.extract_stars_rating(information_dict["stars"])
        information_dict["length"] = AudibleBook.extract_time(
            information_dict["length"]
        )

        return information_dict

    @staticmethod
    def _parse_book_info(r):
        title = (
            r.html.find(
                ".bc-list.bc-list-nostyle.bc-color-secondary.bc-spacing-s2", first=True
            )
            .find("h1", first=True)
            .text
        )

        subtitle = (
            r.html.find(
                ".bc-list.bc-list-nostyle.bc-color-secondary.bc-spacing-s2", first=True
            )
            .find(".bc-text.bc-size-medium", first=True)
            .text
        )

        author = (
            r.html.find(".bc-list-item.authorLabel", first=True)
            .find("a", first=True)
            .text
        )
        narrator = (
            r.html.find(".bc-list-item.narratorLabel", first=True)
            .find("a", first=True)
            .text
        )
        length = r.html.find(".bc-list-item.runtimeLabel", first=True).text
        ratings = r.html.find(".bc-list-item.ratingsLabel", first=True).text

        return {
            "title": title,
            "subtitle": subtitle,
            "author": author,
            "narrator": narrator,
            "length": length,
            "stars": ratings,
        }

    def to_document(self, tensor=None):
        """Returns a Docarray document."""
        if tensor is None:
            return Document(text=self.title)
        else:
            return Document(text=self.title, tensor=tensor)

    @staticmethod
    def extract_time(x):
        time_pattern = re.compile("Length: ([0-9]*) hrs and ([0-9]*) mins")
        time_res = time_pattern.search(x)
        if time_res is None:
            return np.NaN, np.NaN
        else:
            return float(time_res.group(1)[0]), float(time_res.group(2)[0])

    @staticmethod
    def extract_stars_rating(raw_stars):
        ratings = stars = np.NaN
        if raw_stars is not None and str(raw_stars) != "nan":
            stars = float(
                re.search(r"(^[0-9,.]+) ", raw_stars).group(1).replace(",", ".")
            )
            v1 = re.search(r" ([0-9,]+)$", raw_stars)
            v2 = re.search(r"\(([0-9,]*) ratings\)$", raw_stars)
            ratings = float(
                v1.group(1).replace(",", ".")
                if v1 is not None
                else v2.group(1).replace(",", ".")
            )
        return stars, ratings

    @staticmethod
    def _parse_recommendations(r):
        recommendations = r.html.find(".carousel-product")
        recommendation_ids = []
        recommendation_links = []
        for reco in recommendations:
            reco_links = [s for s in reco.links if s.split("/")[1] == "pd"]
            recommendation_links.extend(reco_links)
            recommendation_ids.extend(
                [s.split("/")[3].split("?")[0] for s in reco_links]
            )
        return recommendation_ids, recommendation_links
