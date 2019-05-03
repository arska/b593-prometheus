B593-prometheus
===============

Scrape metrics from a Huawei B593 4G-Router and push them to a prometheus metrics pushgateway.

Settings via ENV variables (can be set in a ".env" file:
PROM_GATEWAY: URL for prometheus pushgateway to push the metrics to (including https://...)
B593_HOST: hostname/ip to connect to (default: 192.168.1.1)
B593_USER: username to log in (default: admin)
B593_PASS: password to log in (defaul: admin)

Needs phantomjs (http://phantomjs.org/download.html) in the same directory, e.g for mac os x:
```
wget -O phantomjs-2.1.1-macosx.zip https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-macosx.zip
unzip phantomjs*
mv phantomjs*/bin/phantomjs .
```

For running on a raspberry pi 2 or 3:
```
git clone https://github.com/arska/b593-prometheus
cd b593-prometheus
sudo apt-get install libfontconfig1 libfreetype6
wget https://github.com/fg2it/phantomjs-on-raspberry/releases/download/v2.1.1-wheezy-jessie/phantomjs_2.1.1_armhf.deb
sudo dpkg -i phantomjs_2.1.1_armhf.deb
ln -s /usr/local/bin/phantomjs
```

Add a crontab entry to gather stats every minute:
```
* *     * * *   root    /root/b593-prometheus/venv/bin/python /root/b593-prometheus/b593.py
```

