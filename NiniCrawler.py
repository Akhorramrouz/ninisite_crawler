import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import numpy as np



class NiniSiteForumCrawler:
    """
    A web crawler for NiniSite forums.
    """

    def __init__(self, forum_number):
        """
        Initializes the NiniSiteForumCrawler instance.

        Args:
            forum_number (int): The number of the forum to crawl.
        """
        self.main_link = "https://www.ninisite.com"
        self.forum_link = self.main_link + '/discussion/forum/' + str(forum_number)
        self.initial_response = requests.get(self.forum_link)
        
    def get_number_of_pages_in_forum(self):
        """
        Retrieves the number of pages in the forum.

        Returns:
            int: The number of pages in the forum.
        """
        response = self.initial_response
        if response.status_code == 200:
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            self.number_of_pages = int(soup.find_all('div', {'class': 'text-xs-center text-sm-left'})[0].find_all('li')[-2].text)
        return self.number_of_pages
    
    def topic_header_parser(self, topic):
        """
        Parses the topic header and returns a dictionary containing relevant information.

        Args:
            topic (bs4.element.Tag): The HTML tag representing a topic header.

        Returns:
            dict: Parsed topic information.
        """
        parsed_topic = {
            'subject': topic.find('span', {'class': 'topic_subject'}).text,
            'link': self.main_link + topic.find('a')['href'],
            'creator_username': topic.find('div', {'class': 'col-xs-12 p-x-0 pull-xs-right last-topic-user hidden-sm-down'}).text.split()[-1],
            'creator_userid': topic.find('div', {'class': 'col-xs-12 p-x-0 pull-xs-right last-topic-user hidden-sm-down'}).find('a')['href'].split('/')[2],
            'number_of_replies': int(topic.find('span', {'class': 'topic_number hidden-sm-up'}).text.split()[0])
        }
        return parsed_topic
    
    def crawl_topics_in_forum(self, starting_page=1, number_pages=10):
        """
        Crawls topics in the forum and returns a DataFrame with the topic data.

        Args:
            starting_page (int): The starting page number to crawl (default: 1).
            number_pages (int): The number of pages to crawl (default: 10).

        Returns:
            pandas.DataFrame: A DataFrame containing the crawled topic data.
        """
        self.topics_data = []
        for pg_number in range(starting_page, number_pages):
            print(pg_number)
            html = requests.get(self.forum_link + f'?page={pg_number}').text
            soup = BeautifulSoup(html, 'html.parser')
            topics = soup.find_all('div', {'class': 'col-xs-12 category--header p-x-0'})
            for topic in topics:
                self.topics_data.append(self.topic_header_parser(topic))
                
            time.sleep(1.5) 
        return pd.DataFrame(self.topics_data)
    


class NinisiteTopicCrawler():
    """
    A class for crawling and extracting data from a NiniSite topic.
    """
def __init__(self, topic_id):
    """
    Initializes the NinisiteTopicCrawler instance.

    Args:
        topic_id (int): The ID of the topic to crawl.
    """
    self.topic_id = topic_id
    self.main_link = 'https://www.ninisite.com'
    self.topic_link = self.main_link + '/discussion/topic/' + str(topic_id)
    self.topic_html = requests.get(self.topic_link).text
    self.topic_soup = BeautifulSoup(self.topic_html, 'html.parser')

def topic_parser(self):
    """
    Parses the main topic page and extracts topic details.
    """
    soup = self.topic_soup.find('article', {'id': 'topic'})
    self.topic_detail = {
        'id': self.topic_id,
        'title': soup.find('div', {'class': 'col-xs-12 m-b-1 p-x-1 forum__topic--header'}).find('a').text,
        'text': soup.find('div', {'class': 'post-message topic-post__message col-xs-12 fr-view m-b-1 p-x-1'}).text,
        'date': soup.find('span', {'class': 'date'}).text,
        'username': soup.find('a', {'class': 'col-xs-9 col-md-12 text-md-center text-xs-right nickname'})['href'].split("/")[3],
        'userid': soup.find('a', {'class': 'col-xs-9 col-md-12 text-md-center text-xs-right nickname'})['href'].split("/")[2],
        'number_comments': int(soup.find_all('span', {'class': 'pull-xs-right'})[-1].text.split()[1])
    }
    self.topic_detail['number_pages'] = int(np.ceil(self.topic_detail['number_comments'] / 20))

def comment_parser(self, comment):
    """
    Parses a comment element and extracts comment details.

    Args:
        comment (BeautifulSoup.Tag): The BeautifulSoup tag representing a comment.

    Returns:
        dict: Comment details including id, text, date, username, userid, and isReply.
    """
    self.comment = comment
    comment_detail = {
        'id': comment['id'].split('-')[-1],
        'text': comment.find('div', class_='post-message').text.strip(),
        'date': comment.find('span', class_='date').text.strip(),
        'username': comment.find('a', class_='col-xs-9 col-md-12 text-md-center text-xs-right nickname').text.strip(),
        'userid': comment.find('a', class_='col-xs-9 col-md-12 text-md-center text-xs-right nickname')['href'].split('/')[2],
        'isReply': bool(comment.find('div', {'class': 'reply-message'}))
    }
    return comment_detail

def crawl_comments_in_topic(self):
    """
    Crawls all comments in the topic and returns a DataFrame containing the comment data.

    Returns:
        pd.DataFrame: DataFrame containing the comment data.
    """
    self.topic_parser()
    comments_data = []
    for pg_number in range(1, self.topic_detail['number_pages'] + 1):
        print(pg_number)
        html = requests.get(self.topic_link + f'?page={pg_number}').text
        soup = BeautifulSoup(html, 'html.parser')
        self.comments = soup.find_all('article', class_='topic-post')
        for comment in self.comments[1:]:
            comments_data.append(self.comment_parser(comment))

        time.sleep(1.5)

    return pd.DataFrame(comments_data)
