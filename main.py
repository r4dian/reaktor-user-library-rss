#!/usr/bin/env python
import sys,os
import urllib.request

# add the path for virtual env for running via cron
os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/lib/python3.9/site-packages/')

from bs4 import BeautifulSoup
import tweepy

#from our keys module (keys.py), import the keys dictionary
# from keys import keys
# CONSUMER_KEY = keys['consumer_key']
# CONSUMER_SECRET = keys['consumer_secret']
# ACCESS_TOKEN = keys['access_token']
# ACCESS_TOKEN_SECRET = keys['access_token_secret']


domain = "http://www.native-instruments.com"
link   = domain+"/en/community/reaktor-user-library/all/all/all/all/all/latest/all/"

def generate(file):
    a = urllib.request.urlopen(link)
    soup = BeautifulSoup(a,features="html.parser")
    t = soup.find_all("div", "description-title")
    c = soup.find_all("div", "caption")
    l = soup.select(".description-title > a")
    i = soup.select(".cover > a > img")
    with open(file, 'w') as f:
        f.write("""<?php header('Content-Type: application/rss+xml; charset=UTF-8'); ?><?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
          <channel>
            <title>Reakor User Library</title>
            <link>http://www.native-instruments.com/en/community/reaktor-user-library</link>
            <atom:link href="<?php echo "http://".$_SERVER['HTTP_HOST'].$_SERVER['REQUEST_URI']; ?>" rel="self" type="application/rss+xml" />
            <description>Reakor User Library</description>
            <language>en</language>
            <docs>https://validator.w3.org/feed/docs/rss2.html</docs>
            <generator>Python</generator><!-- Honest, just serving the otput via php to get the right content-type header served on the SDF. -->
        """)
        for x in range(len(t)):
            f.write("""
            <item>
              <title>%s</title>
              <link>%s</link>
              <guid>%s</guid>
              <description>&lt;img src="%s"&gt; %s</description>
            </item>""" % (t[x].text.strip(), domain+l[x]["href"], domain+l[x]["href"], "http://www.native-instruments.com/"+i[x]["src"], c[x].text.strip()))
        f.write("""    
          </channel>
        </rss>

        """)

def diff(old,new):
    a = set(old.select("item"))
    b = set(new.select("item"))
    c = b-a
    for i in c:
        # tweet(i)
        pass

def tweet(item):
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

    miso = BeautifulSoup(str(item))
    ititle = miso.find("title")
    ilink = miso.find("link")

    # print ("%s - %s" % (ititle.text, ilink.text))

    try:
        s = api.update_status("%s - %s" % (ititle.text, ilink.text))
    except:
        pass



if __name__ == "__main__":
    old = BeautifulSoup(open(sys.argv[1]), features="html.parser")
    generate(sys.argv[1])
    new = BeautifulSoup(open(sys.argv[1]), features="html.parser")
    diff(old,new)

