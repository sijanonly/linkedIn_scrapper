# -*- coding: utf-8 -*-
# @Author: Sijan
# @Date:   2017-08-29 09:36:34
# @Last Modified by:   leapfrong
# @Last Modified time: 2017-12-17 09:20:02

import time

from scrapy.contrib.spiders.init import InitSpider
from scrapy.selector import Selector
from scrapy.http import Request

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# from selenium import selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException

from linkedIn_scrapper.items import LinkedInItem


class LinkedInSpider(InitSpider):
    name = "LinkedInSpider"
    allowed_domains = ["www.linkedin.com"]
    handle_httpstatus_list = [999]
    start_urls = [
        'https://www.linkedin.com/search/results/index/?keywords=freelancer%20Nepal%20technology%20software%20',
        'https://www.linkedin.com/search/results/index/?keywords=freelancer%20Nepal%20technology%20developer'
    ]
    login_page = 'https://www.linkedin.com/uas/login'
    # start_urls = [
    #     'https://www.linkedin.com/uas/login'
    # ]

    def init_request(self):
        """This function is called before crawling starts."""
        self.download_delay = 0.25
        _chrome_options = Options()
        _chrome_options.add_argument('disable-infobars')
        _path = '/home/leapfrong/chromedriver'
        # self.driver = webdriver.Chrome('/home/leapfrong/chromedriver')
        self.driver = webdriver.Chrome(
            executable_path=_path, chrome_options=_chrome_options)
        self.driver.maximize_window()
        return Request(url=self.login_page, callback=self.login)

    def login(self, response):
        """Generate a login request."""
        self.driver.get(response.url)
        username = self.driver.find_element_by_name("session_key")
        password = self.driver.find_element_by_name("session_password")
        username.send_keys('sijanonly@gmail.com')
        password.send_keys('passworddd')
        login_attempt = self.driver.find_element_by_id(
            "btn-primary")
        login_attempt.submit()
        time.sleep(5)

        for url in self.start_urls:
            yield Request(
                url,
                # 'https://www.linkedin.com/in/subashkazi/',
                cookies=self.driver.get_cookies(),
                callback=self.parse
                # callback=self.parse_details
            )

    def check_login_response(self, response):
        """Check the response returned by a login request to see if we are
        successfully logged in.
        """
        if "My Network" in response.body.decode('utf-8'):
            print('logged in')
            # Now the crawling can begin..
            return self.initialized()
        else:
            print('not logged in')
            # Something went wrong, we couldn't log in, so nothing happens.

    def parse(self, response):
        self.driver.get(response.url)
        time.sleep(10)
        elm = ec.presence_of_element_located(
            (By.CSS_SELECTOR, 'span.search-results__total'))
        WebDriverWait(self.driver, 10).until(elm)

        selenium_response_text = self.driver.page_source
        selector = Selector(text=selenium_response_text)
        total = selector.xpath(
            "//span[contains(@class,'search-results__total')]/text()").extract_first()
        count_list = total.split()
        page_count = int(count_list[0].replace(',', ''))
        # page_count = 10
        for page in range(1, page_count + 1):
            print('page is', page)
            page_url = response.url + '&page=%s' % page
            yield response.follow(page_url, callback=self.parse_page)

    def parse_page(self, response):
        self.driver.get(response.url)
        for i in range(0, 3):
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

        selenium_response_text = self.driver.page_source
        selector = Selector(text=selenium_response_text)
        freelancers = selector.xpath(
            "//div[contains(@class, 'search-results__cluster-content')]//a[contains(@class, 'search-result__result-link')]/@href").extract()
        for freelancer in freelancers:
            detail_link = "https://www.linkedin.com" + freelancer
            yield response.follow(detail_link, callback=self.parse_details)

    def parse_details(self, response):
        self.driver.get(response.url)
        time.sleep(10)
        name = self.driver.find_element_by_xpath(
            "//h1[contains(@class, 'pv-top-card-section__name')]")
        title = self.driver.find_element_by_xpath(
            "//h2[contains(@class, 'pv-top-card-section__headline')]")
        try:
            description_node = self.driver.find_elements_by_xpath("//div[@class='truncate-multiline--truncation-target']//span")
        except Exception:
            pass
        description = []
        if description_node:
            for item in description_node:
                print(item.get_attribute('innerHTML'))
                description.append(item.text)
        # self.driver.execute_script(
        #     "window.scrollTo(0, document.body.scrollHeight);")

        experience_block = self.driver.find_elements_by_xpath(
            "//section[contains(@class, 'experience-section')]//li[contains(@class, 'pv-profile-section__card-item')]")
            # "//section[contains(@class, 'experience-section')]//div[contains(@class, 'pv-entity__summary-info')]")
        position = None
        company = None
        experiences = []
        for each_block in experience_block:
            experience = {}
            content_block = each_block.find_element_by_xpath(
                ".//div[contains(@class, 'pv-entity__summary-info')]")
            position = content_block.find_element_by_xpath('./h3')
            # position = each_block.find_element_by_xpath('./h3')
            position = position.get_attribute('innerHTML')
            company = content_block.find_element_by_xpath('.//h4/span[2]')
            company = company.get_attribute('innerHTML')

            experience_year = content_block.find_element_by_xpath('.//h4[3]//span[2]')
            experience_year = experience_year.get_attribute('innerHTML')
            experience['company'] = company
            experience['position'] = position
            experience['no_of_yrs'] = experience_year
            if experience not in experiences:
                experiences.append(experience)
        # //ul[contains(@class,'pv-featured-skills-list')]//span[contains(@class, 'pv-skill-entity__skill-name')]

        self.driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(5)
        self.driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight/2);")
        # skills = self.driver.find_element_by_xpath(
        #     "//ul[contains(@class,'pv-featured-skills-list')]")
            # "//ul[contains(@class,'pv-featured-skills-list')]//li//div[contains(@class,'pv-skill-entity__header')]")
            # "//ul[contains(@class,'pv-featured-skills-list')]//span[contains(@class, 'pv-skill-entity__skill-name')]")
        selenium_response_text = self.driver.page_source
        selector = Selector(text=selenium_response_text)
        skill_list = []
        skills = selector.xpath(
            "//ul[contains(@class,'pv-featured-skills-list')]//span[contains(@class, 'pv-skill-entity__skill-name')]/text()")
        for skill in skills:
            skill_list.append(skill.extract())
        item = LinkedInItem(
            name=name.get_attribute('innerHTML'),
            title=title.get_attribute('innerHTML'),
            description=" ".join(description),
            experience=experiences,
            skills=skill_list,
            url=response.url
        )
        yield item
