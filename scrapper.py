from requests_html import HTMLSession, HTML
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import warnings
from os.path import join
from collections import deque
from time import sleep

warnings.filterwarnings("ignore")

class AudibleScrapper():

    def __init__(self):
        self.base_audible = "https://www.audible.com"
        self.categories_url = 'https://www.audible.com/categories?ref=a_pd_Americ_t1_navTop_pl0cg0c0r5&pf_rd_p=2774f9d8-d3de-47f2-8c6a-6a59524b5923&pf_rd_r=ZS5GW1KHJ8NGV7PSA3N3'
        self.sess = HTMLSession()


    def get_all_categories(self, base_url):
        """Gets links for each category."""
        r = self.sess.get(base_url)

        genres = r.html.find('div.bc-col-responsive.bc-col-3')
        cat_items = []
        cat_names = []

        for genre in genres:
            items = genre.find('ul.bc-list')[0].find('li.bc-list-item')
            cat_items.extend(items)

        cat_names = [item.text.split(' (')[0] for item in cat_items]

        return cat_items, cat_names


    def get_page_list(self, category_link):
        """Gets the link for a page of books a given category."""
        
        r = self.sess.get(category_link)
        all_link = r.html.find('.allInCategoryPageLink', first=True).attrs['href']

        return all_link

    def crawl_category_page(self, category_all_link, page=0):
        """Get the links of all books in a page of a given category."""
        
        r = self.sess.get(category_all_link) #TODO: add page number
        book_links = r.html.find('li.bc-list-item.productListItem', first=False)

        return book_links 

    def parse_page(self, page_link):
        """Parse an audible book's page."""
        r = self.sess.get(page_link)

        # Own ID
        id = r.url.split('/')[5].split('?')[0]

        # Recommendations
        recommendations = r.html.find('.carousel-product')
        recommendation_ids = []
        recommendation_links = []
        for reco in recommendations:
            reco_links = [s for s in reco.links if s.split('/')[1] == "pd"]
            recommendation_links.extend([self.base_audible + r for r in reco_links])
            recommendation_ids.extend([s.split('/')[3].split('?')[0] for s in reco_links])

        # Local information
        local_fields = ['title', 'subtitle', 'author', 'narrator', 'length', 'stars']
        local_info = r.html.find('.bc-list.bc-list-nostyle.bc-color-secondary.bc-spacing-s2')[0].text.split('\n')
        
        information_dict = dict(zip(local_fields,local_info))
        information_dict['id'] = id
        information_dict['recommendations'] = recommendation_ids
        information_dict['links'] = recommendation_links

        return information_dict 

    def close_session(self):
        self.sess.close()

    def random_walk(self, link = None, limit = 10, results = {}, sleep_time = 1):
    
        if link is not None:
            information_dict = self.parse_page(link)
            id = link.split('/')[5].split('?')[0]
            results[id] = information_dict

        next_links = deque()
        for v in results.values():
            next_links.extend(v['links'])
            
        iteration = 0

        while len(next_links) > 0 and iteration < limit:

            link = next_links.pop()
            id = link.split('/')[5].split('?')[0]

            if (id not in results):
                information_dict = self.parse_page(link)
                results[id] = information_dict
                next_links.extend(information_dict['links'])
                iteration += sleep_time
                sleep(1)
                
        return results