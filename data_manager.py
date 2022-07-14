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

    def store_book_query(self, book: AudibleBook) -> str:
        query = """MERGE (n:Book {{ id: '{}', title: '{}', subtitle: '{}', ratings: '{}', stars: '{}', hours: '{}', minutes: '{}' }})""".format(
            book.id,
            book.title,
            book.subtitle,
            book.ratings,
            book.stars,
            book.hours,
            book.minutes,
        )
        return self.query(query)

    def reset(self):
        return self.query(
            """MATCH (n)
        DETACH DELETE n"""
        )
