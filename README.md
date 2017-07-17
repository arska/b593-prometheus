= B593-prometheus

Scrape metrics from a Huawei B593 4G-Router and push them to a prometheus metrics pushgateway.

Needs phantomjs (http://phantomjs.org/download.html) in the same directory, e.g for mac os x:
```
wget -O phantomjs-2.1.1-macosx.zip https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-macosx.zip
unzip phantomjs*
mv phantomjs*/bin/phantomjs .
```