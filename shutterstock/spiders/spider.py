import os.path

import scrapy
import jsonpath_ng
import pandas as pd
import wget

class SpiderSpider(scrapy.Spider):
    name = 'spider'
    allowed_domains = ['shutterstock.com']
    start_urls = ['http://shutterstock.com/']

    def dowload_file(self, url):
        filename = wget.detect_filename(url=url)

        if not os.path.isfile(filename):
            tmp_file = f"{filename}.tmp"
            local_file = wget.download(url, out=tmp_file)
            os.rename(local_file, filename)

        return filename

    def generate_querires(self):
        """
        data example
        geonameid,name,asciiname,latitude,longitude,population,Country
        3039154,El Tarter,El Tarter,42.57952,1.65362,1052,Andorra
        3039163,Sant Julià de Lòria,Sant Julia de Loria,42.46372,1.49129,8022,Andorra
        3039604,Pas de la Casa,Pas de la Casa,42.54277,1.73361,2363,Andorra
        3039678,Ordino,Ordino,42.55623,1.53319,3066,Andorra
        """
        countries = ["Turkey"]
        url = "https://raw.githubusercontent.com/aljeshishe/all_cities/main/cities500_merged.csv"
        local_file = self.dowload_file(url=url)
        df = pd.read_csv(local_file)
        df = df[df["Country"].isin(countries)]
        for index, row in df.iterrows():
            yield row["asciiname"], row["Country"]

    def start_requests(self):
        for city, country in self.generate_querires():
            query = f"{city}-{country}"
            url = f"https://www.shutterstock.com/_next/data/C9XIXNeuNSgmiYo-YdBAv/en/_shutterstock/search/{query}.json?image_type=photo"
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:107.0) Gecko/20100101 Firefox/107.0"}
            yield scrapy.Request(method="GET", url=url, headers=headers, callback=self.parse, meta=dict(city=city, country=country))

    def parse(self, response):
        meta = response.meta
        data = response.json()
        results = jsonpath_ng.parse("$.pageProps.assets[0].meta.pagination.totalRecords").find(data)
        if results:
            count = int(results[0].value)
        else:
            count = 0
        yield dict(count=count, city=meta["city"], country=meta["country"])


