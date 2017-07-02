#!/usr/bin/env python
#Ideas from: https://github.com/mehmetkose/python3.5-async-crawler
'''

'''

ERROR_CONDITIONS_TO_NOTE = '''

[2017-06-05 16:52:11.615895] ERROR: /home/uche/.local/pyenv/main/bin/liblink_crawl: Uncaught exception occurred
Traceback (most recent call last):
  File "/home/uche/.local/pyenv/main/lib/python3.5/site-packages/liblinkbots/crawler/framework.py", line 99, in lln_handle_one_link
    async with session.get(link) as resp:
  File "/home/uche/.local/pyenv/main/lib/python3.5/site-packages/aiohttp/client.py", line 626, in __aenter__
    self._resp = yield from self._coro
  File "/home/uche/.local/pyenv/main/lib/python3.5/site-packages/aiohttp/client.py", line 220, in _request
    proxy=proxy, proxy_auth=proxy_auth, timer=timer)
  File "/home/uche/.local/pyenv/main/lib/python3.5/site-packages/aiohttp/client_reqrep.py", line 88, in __init__
    self.update_host(url)
  File "/home/uche/.local/pyenv/main/lib/python3.5/site-packages/aiohttp/client_reqrep.py", line 113, in update_host
    "Could not parse hostname from URL '{}'".format(url))
ValueError: Could not parse hostname from URL 'mailto:?subject=Boca%20Raton%20(Place)%20at%20Anythink%20Libraries&body=I%20found%20this%20resource%20at%20the%20library%20and%20thought%20you%20might%20be%20interested.%0A%0ABoca%20Raton%20(Place)%20at%20Anythink%20Libraries%20%0A-%20http://link.anythinklibraries.org/resource/ewcC8cBWhdU/?share%3Dmail'
[2017-06-05 16:52:11.646990] DEBUG: /home/uche/.local/pyenv/main/bin/liblink_crawl: Above error in context of TASK 19, LINK mailto:?subject=Boca%20Raton%20%28Place%29%20at%20Anythink%20Libraries&body=I%20found%20this%20resource%20at%20the%20library%20and%20thought%20you%20might%20be%20interested.%0A%0ABoca%20Raton%20%28Place%29%20at%20Anythink%20Libraries%20%0A-%20http%3A//link.anythinklibraries.org/resource/ewcC8cBWhdU/%3Fshare%3Dmail


'''

import re
import sys
import random
import asyncio
import async_timeout
#from urllib.parse import urljoin, urldefrag
from enum import Enum #https://docs.python.org/3.4/library/enum.html

import aiohttp

from amara3 import iri
from amara3.uxml import html5
from amara3.uxml.treeutil import descendants, select_elements

from librarylink.util import liblink_set

#Note bug using Timeout: https://github.com/KeepSafe/aiohttp/issues/962

GREENLIGHT_STATUS = [200]#, 301, 301]

LIBRARY_LINK_HEADER = 'X-Library-Link-Network'

#FIXME: of course this does not address links in CSS, invoked by JS, etc.
HTML_LINKS = {
    'a': ['href'],
    'link': ['href'],
    'img': ['src'],
}

#Great source: https://techblog.willshouse.com/2012/01/03/most-common-user-agents/
#See (but way out of date): http://web.archive.org/web/20080913141616/http://www.useragentstring.com/pages/useragentstring.php?typ=Browser
#See (but out of date): http://www.user-agents.org/
#See: https://techblog.willshouse.com/2012/01/03/most-common-user-agents/
#List of string, weight
USER_AGENTS = [
    ('Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20100101 Firefox/10.0', 2),
    ('Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36', 7),
    ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36', 9),
    ('Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36', 8),
    ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36', 7),
    ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36', 4),
    ('Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko', 3),
    ('Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36', 3),
]

UA_SUFFIX = ' (LibLink Nautilus)'

USER_AGENT_STRINGS = [ s + UA_SUFFIX for (s, w) in USER_AGENTS ]
USER_AGENT_WEIGHTS = [ w for (s, w) in USER_AGENTS ]

HTML_CTYPES = ['text/html']

#Choices is new in Python 3.6
STACKED_USER_AGENTS = []

for (s, w) in USER_AGENTS:
    STACKED_USER_AGENTS.extend([s]*w)


def links_from_html(root, baseurl, look_for=HTML_LINKS):
    '''
    '''
    for e in select_elements(descendants(root)):
        if e.xml_name in HTML_LINKS:
            for k, v in e.xml_attributes.items():
                if k in HTML_LINKS[e.xml_name]:
                    #if 'work' in baseurl: print(2, (v, baseurl, iri.absolutize(v, baseurl)))
                    yield iri.absolutize(v, baseurl)


class crawltask(object):
    def __init__(self, task_id, front_page, sink, linkset_q, seen, idle_flags, logger):
        self._task_id = task_id
        self._sink = sink
        self._logger = logger
        #linkset_q and self._seen are shared across all tasks
        self._linkset_q = linkset_q
        self._seen = seen
        self._idle_flags = idle_flags
        self._front_page = front_page

    async def lln_handle_one_link(self, source, link):
        _, fphost, _, _, _ = iri.split_uri_ref(self._front_page)
        connector = aiohttp.TCPConnector(verify_ssl=False)
        #FIXME: Switch to the line below when we can use 3.6 across the board
        uastring = random.choice(STACKED_USER_AGENTS)
        #uastring = random.choices(USER_AGENT_STRINGS, USER_AGENT_WEIGHTS)
        headers = {'User-Agent': uastring, 'Referer': source}
        if not source:
            del headers['Referer']
        body = None
        try:
            async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
                try:
                    async with session.get(link) as resp:
                        #self._logger.debug('[TASK {}] Content type ({}): {}'.format(self._task_id, link, resp.headers.get('CONTENT-TYPE')))
                        if resp.status == 200 and resp.headers.get('CONTENT-TYPE') in HTML_CTYPES:
                            #with async_timeout.timeout(10):
                            respurl = str(resp.url)
                            #Handle possible redirection
                            if respurl not in self._seen:
                                body = await resp.text() #.read()
                except (aiohttp.ClientOSError, aiohttp.ClientResponseError, aiohttp.client_exceptions.ServerDisconnectedError) as e:
                    self._logger.debug('Error: {} [TASK {}] -> {}'.format(link, self._task_id, repr(e)))

            if body:
                ls = self._sink.send((body, respurl, resp.headers, source, self._task_id))
                #Trim links which have already been seen when queued (saves memory)
                if ls:
                    #XXX: Use set intersection?
                    self._linkset_q.put_nowait((respurl, liblink_set( link for link in ls if link not in self._seen )))
        except Exception as e:
            self._logger.exception()
            self._logger.debug('Above error in context of TASK {}, LINK {}, source {}'.format(self._task_id, link, source))


    async def crawl_for_ld(self, mainloop_log_interval=20, mainloop_wait=2):
        '''
        linkset_queue - basically the inbound queue; URLs to be crawled (actually a set of links to be crawled in a single session)
        action_queue - basically the outbound queue; HTTP responses to be processed

        >>> from liblinkbots.crawler.simplelinkchecker import lln_crawl
        '''
        #front_page - URL of LLN site front page, e.g. 'http://link.cuyahogalibrary.org/', used to check local pages
        funcname = 'crawl_for_ld'
        #url_hub = [root_url, "%s/sitemap.xml" % (root_url), "%s/robots.txt" % (root_url)]

        #FIXME: incorporate a termination signal

        self._logger.debug('Launching {} [TASK {}].'.format(funcname, self._task_id))
        wakeup_counter = 0

        try:
            #Stop when all tasks have no more work to do
            while not(all(self._idle_flags)):
                wakeup_counter += 1
                if wakeup_counter % mainloop_log_interval == 0:
                    #TWEET_URL_PATTERN.format()
                    self._logger.debug('{} [TASK {}] still alive and has lived its main loop {} times. {} links seen.'.format(funcname, self._task_id, wakeup_counter, len(self._seen)))
                while not self._linkset_q.empty():
                    #More work to do; not idle
                    self._idle_flags[self._task_id] = False
                    (source, linkset) = await self._linkset_q.get()
                    #self._logger.debug('{} [TASK {}] dequeued source: {} linkset: {}.'.format(funcname, self._task_id, source, linkset))
                    tasks = []
                    #Filter links again in case another worker has handled it since it was queued
                    for link in (link for link in linkset if link not in self._seen):
                        await self.lln_handle_one_link(source, link)
                        self._seen.add(link)

                #Flag self as idle
                self._idle_flags[self._task_id] = True
                await asyncio.sleep(mainloop_wait)
        except Exception as e:
            self._logger.debug('Error in {} [TASK {}]: {}.'.format(funcname, self._task_id, repr(e)))
        self._logger.debug('[{}] All tasks idle; TASK {} finishing.'.format(funcname, self._task_id))


class base_sink(object):
    @staticmethod
    def update_cmdline_parser(parser):
        return

    @classmethod
    def setparams(cls, pagesperfile, logger):
        cls.pagesperfile = pagesperfile
        cls.logger = logger
        pass

    @classmethod
    def close(cls):
        pass

    def __init__(self, frontpage, **kwargs):
        self._frontpage = frontpage
        return

    #FIXME: Or do we make this a coroutine?
    def send(self, data):
        raise NotImplementedError

    def _queue_links(self, root, respurl):
        linkset = liblink_set()
        for link in links_from_html(root, respurl):
            #If you wanted to not even visit any resources outside this domain, here is how
            #_, linkhost, _, _, _ = iri.split_uri_ref(link)
            #if self._fphost == linkhost:
            #    link, frag = iri.split_fragment(link)
            #    linkset.add(link)

            link, frag = iri.split_fragment(link)
            linkset.add(link)
        return linkset
