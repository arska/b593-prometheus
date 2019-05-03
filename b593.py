#!/usr/bin/env python
"""
Module for getting statistics from a Huawei B593 4G-router
pushed into prometheus
"""

import requests
import xmltodict
import re
from prometheus_client import (
    Gauge,
    Summary,
    CollectorRegistry,
    pushadd_to_gateway,
)
import platform
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json


class HuaweiB593:
    """
    Class for getting stats from the Huawei B593 Router
    """

    BASE_URL = "http://{host}"
    session = None

    def __init__(self, host="192.168.1.1", user="admin", password="admin"):
        """
        Set B593 connection parameters
        """
        self.host = host
        self.user = user
        self.password = password
        self.base_url = self.BASE_URL.format(host=host)
        self.session = requests.Session()

    def status(self):
        """
        Get status endpoint
        """
        status = xmltodict.parse(
            self.session.post(
                self.base_url + "/index/getStatusByAjax.cgi"
            ).text
        )
        return status["Status"]

    def signal(self):
        """
        Parse signal strength indicator 0-5
        """
        #    "SIG": {
        #        18: "off",
        #        19: "1",
        #        20: "2",
        #        21: "3",
        #        22: "4",
        #        23: "5",
        #    },
        return int(self.status().get("SIG")) - 18

    def mode(self):
        """
        get the connection mode (2/3/4g)
        """
        #    "Mode": {
        #        27: "off",
        #        28: "2g",
        #        29: "3g",
        #        30: "4g",
        #        59: "sim_disabled",
        #        60: "2g",
        #        61: "3g",
        #        62: "4g",
        #    },
        return int(self.status().get("Mode"))

    def scrape(self):
        """
        Use phantomjs to log into the router to get more detailed stats
        """
        # PhantomJS files have different extensions
        # under different operating systems
        if platform.system() == "Windows":
            phantomjs_path = "./phantomjs.exe"
        else:
            phantomjs_path = "./phantomjs"

        browser = webdriver.PhantomJS(phantomjs_path)
        browser.get(self.base_url)

        elem = browser.find_element_by_id("txt_Username")
        elem.clear()
        elem.send_keys(self.user)

        elem = browser.find_element_by_id("txt_Password")
        elem.clear()
        elem.send_keys(self.password)

        elem = browser.find_element_by_id("login_btn")
        elem.click()

        #        WanStatistics = {'uprate' : '51736' ,
        #        'downrate' : '389680' ,
        #        'upvolume' : '125004949100' ,
        #        'downvolume' : '1076929187571' ,
        #        'liveTime' : '87921988'};

        stats = re.compile(r"WanStatistics = (\{.+\});")
        stats = json.loads(
            stats.search(browser.page_source).group(1).replace("'", '"')
        )

        browser.get(self.base_url + "/html/management/diagnose.asp")
        elem = browser.find_element_by_id("id_modemRadio")
        elem.click()

        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "tritem_3"))
        )

        #        <table class="table_list" id="id_modemTable">
        #        <tbody>
        #        <tr class="even_tr"><th colspan="3" style="text-align: center;">
        #        Langattoman verkon tila</th></tr>
        #        <tr class="module_content_center odd_tr" id="tritem_1">
        #        <td>1</td><td>PLMN:</td><td>24405</td></tr>
        #        <tr class="module_content_center even_tr" id="tritem_2">
        #        <td>2</td><td>Palvelun tila:</td><td>Kelvollinen palvelu</td></tr>
        #        <tr class="module_content_center odd_tr" id="tritem_3"><td>3</td>
        #        <td>RSSI (dBm):</td><td>-48.0</td></tr>
        #        <tr class="module_content_center even_tr" id="tritem_4"><td>4</td>
        #        <td>RSRP (dBm):</td><td>-76.0</td></tr>
        #        <tr class="module_content_center odd_tr" id="tritem_5"><td>5</td>
        #        <td>RSRQ (dB):</td><td>-8.0</td></tr>
        #        <tr class="module_content_center even_tr" id="tritem_6"><td>6</td>
        #        <td>Verkkovierailu:</td><td>Ei</td></tr>
        #        </tbody></table>

        mapping = {"tritem_3": "rssi", "tritem_4": "rsrp", "tritem_5": "rsrq"}
        soup = BeautifulSoup(browser.page_source, "html.parser")
        for tag in mapping:
            row = soup.find(id=tag).find_all("td")
            stats[mapping[tag]] = row[2].string

        return stats


def main():
    """
    get stats and push to prometheus pushgateway
    """
    b593 = HuaweiB593()
    registry = CollectorRegistry()
    signal = Gauge(
        "b593_signal",
        "Huawei B593 signal strength (0-5, as displayed on the device)",
        registry=registry,
    )
    signal.set_function(b593.signal)
    mode = Gauge(
        "b593_mode", "Huawei B593 signal mode (2g/3g/4g)", registry=registry
    )
    mode.set_function(b593.mode)
    timer = Summary(
        "b593_scrapetime",
        "time to scrape and parse all infos",
        registry=registry,
    )
    with timer.time():
        scrape = b593.scrape()
    gauges = {}
    for i in scrape:
        gauges[i] = Gauge("b593_" + i, "Huawei B593 " + i, registry=registry)
        gauges[i].set(scrape[i])
    pushadd_to_gateway(
        "https://pushgateway-aarno-srf2spotify.appuioapp.ch",
        registry=registry,
        job="b593",
    )


if __name__ == "__main__":
    main()
