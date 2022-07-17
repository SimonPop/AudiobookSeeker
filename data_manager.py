from neo4j import GraphDatabase

from audible_book import AudibleBook


class DataManager:
    def __init__(self, uri="bolt://localhost:7687", user="simon", password="audible"):
        self.__uri = uri
        self.__user = user
        self.__pwd = password
        self.__driver = None
        try:
            self.__driver = GraphDatabase.driver(
                self.__uri, auth=(self.__user, self.__pwd)
            )
        except Exception as e:
            print("Failed to create the driver:", e)

    def close(self):
        if self.__driver is not None:
            self.__driver.close()

    def query(self, query, db=None):
        assert self.__driver is not None, "Driver not initialized!"
        session = None
        response = None
        try:
            session = (
                self.__driver.session(database=db)
                if db is not None
                else self.__driver.session()
            )
            response = list(session.run(query))
        except Exception as e:
            print("Query failed:", e)
        finally:
            if session is not None:
                session.close()
        return response

    def store_book(self, book: AudibleBook) -> str:
        self.create_place_holder(book.id, book.link)
        self.update_book_with_properties(book)

    def create_place_holder(self, book_id: str, link: str) -> str:
        query = """MERGE (n:Book {{ id: '{}', link: '{}' }})""".format(book_id, link)
        return self.query(query)

    def update_book_with_properties(self, book: AudibleBook) -> str:
        query = """MATCH (n:Book {{id: '{}'}}) SET n += {{title: '{}', subtitle: '{}', ratings: '{}', stars: '{}', hours: '{}', minutes: '{}'}}""".format(
            book.id,
            book.title,
            book.subtitle,
            book.ratings,
            book.stars,
            book.hours,
            book.minutes,
        )
        return self.query(query)

    def create_link(self, id_start: str, id_target: str) -> str:
        query = """MATCH (a:Book), (b:Book) WHERE a.id = '{}' AND b.id = '{}' CREATE (a)-[r:RECOMMENDS]->(b)""".format(
            id_start, id_target
        )
        return self.query(query)

    def get_unscrapped_links(self, limit=1):
        query = """MATCH (n) WHERE NOT EXISTS(n.title) RETURN n.link LIMIT {}""".format(
            limit
        )
        return [r["n.link"] for r in self.query(query)]

    def get_scrapped_ids(self):
        query = """MATCH (n) WHERE EXISTS(n.title) RETURN n.id"""
        return [r["n.id"] for r in self.query(query)]

    def get_connected_scrapped_subgraph(self):
        query = (
            """MATCH (a:Book)-[r:RECOMMENDS]->(b:Book) WHERE EXISTS(b.title) RETURN *"""
        )
        return self.query(query)

    def reset(self):
        return self.query(
            """MATCH (n)
        DETACH DELETE n"""
        )
