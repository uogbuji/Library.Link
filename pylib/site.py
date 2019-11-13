'''

'''

import re
import http
import asyncio
import tempfile
from itertools import *

import aiohttp

from versa.driver import memory
from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET, ATTRIBUTES
from versa.reader import rdfalite
from versa.reader.rdfalite import RDF_NS, SCHEMAORG_NS
from versa import util as versautil

from amara3 import iri
from amara3.asynctools import AIOHTTP_ERROR_MENAGERIE
from amara3.uxml import xmliter
from amara3.uxml.treeutil import *

RDFTYPE = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
SCHEMAORG = 'http://schema.org/'

LL_RESOURCE_BASE = 'http://library.link/resource/'
LL_ISBN_STEMPLATE = 'http://library.link/id/isbn/{isbn}/brief.json'
OPENLIBRARY_TITLESEARCHBASE = 'http://openlibrary.org/search.json'


class llsite:
    '''
    High-level (sitemap-style) information about a Library.Link site
    
    >>> from librarylink.site import llsite
    >>> s = llsite('http://link.worthingtonlibraries.org')
    >>> s.url
    'http://link.worthingtonlibraries.org'
    >>> s.host
    'link.worthingtonlibraries.org'
    >>> s.sitemap
    'http://link.worthingtonlibraries.org/harvest/sitemap.xml'
    >>> s.lastmod
    '2018-04-26T22:58:59Z'
    '''
    def __init__(self, baseurl=None):
        if baseurl:
            model, _ = load_rdfa_page(baseurl)
            if not model:
                raise RuntimeError(baseurl, 'doesn\'t appear to be a Library.Link site')
            #<dd property="dcterms:modified">2018-04-17T04:17:32Z</dd>
            
            self.lastmod = next(versautil.lookup(model, None, 'http://purl.org/dc/terms/modified'), None)
            self.sitemap = iri.absolutize('/harvest/sitemap.xml', baseurl)
            self.url = baseurl
            protocol, self.host, path, query, fragment = iri.split_uri_ref(baseurl)


async def enq_all_sites(outq, session=None, cache=None, max_retries=1,
    sitemap_url='http://library.link/harvest/full-sitemap.xml'
    ):
    '''
    Push all sites in the Library.Link master sitemap to a provided queue
    Args:
        outq - asyncio.Queue instance on which to push site nodes
        session - optional aiohttp session to reuse
        cache - optional cache for Web requests
        max_retries - number of times to retry Web requests
        sitemap_url - optional overridden LLN master sitemap URL (e.g. to use a mirror). Note 'http://library.link/harvest/sitemap.xml is the subset in the syndication feed

    Return:
        None

    >>> import asyncio
    >>> from amara3.asynctools import go_async
    >>> from librarylink.site import enq_all_sites
    >>>
    >>> site_q = asyncio.Queue()
    >>>
    >>> async def site_handler(site_q):
    ...     while True:
    ...         s = await site_q.get()
    ...         if s is None: break
    ...         if 'denverlibrary' in s.host:
    ...             print(s.host)
    ...
    >>> go_async(asyncio.gather(enq_all_sites(site_q), site_handler(site_q)))
    link.denverlibrary.org
    [None, None] # asyncio.gather retval
    '''
    # XXX: The XML parse will complete before the task waiting with the queue ever gets run
    # Inevitable while expat (via xmliter) is not async
    def sink():
        while True:
            e = yield
            loc = next(select_name(e, 'loc'))
            lastmod = next(select_name(e, 'lastmod'))
            s = llsite()
            s.sitemap = loc.xml_value
            s.url, _, tail = s.sitemap.partition('harvest/sitemap.xml')
            s.base_url = s.url #Legacy property name
            # Early warning for funky URLs breaking stuff downstream
            assert not tail
            protocol, s.host, path, query, fragment = iri.split_uri_ref(s.sitemap)
            s.lastmod = lastmod.xml_value
            outq.put_nowait(s)

    ts = xmliter.sender(('sitemapindex', 'sitemap'), sink())

    retry_count = 0
    while retry_count <= max_retries:
        try:
            if session is None:
                # XXX: Assumes aiohttp.cient supports HTTP Cache Control, but not actually sure
                async with aiohttp.ClientSession() as session:
                    async with session.get(sitemap_url) as response:
                        text = await response.text()
                        ts.parse(text)
            else:
                async with session.get(sitemap_url) as response:
                    text = await response.text()
                    ts.parse(text)
            break
        except AIOHTTP_ERROR_MENAGERIE as e:
            #import sys; print(sitemap_url, f'[EXCEPTION {e}]', file=sys.stderr)
            retry_count += 1
            await asyncio.sleep(0.2)

    # Sentinel to indicate completed (or in the case of error, no data)
    await outq.put(None)


def all_sites(sitemap_url='http://library.link/harvest/sitemap.xml', plus_list=None):
    '''
    Yield all sites in the Library.Link master sitemap

    >>> from librarylink.util import all_sites
    >>> denversite = next(( s for s in all_sites() if 'denverlibrary' in s.host ))
    >>> denversite.host
    'link.denverlibrary.org'
    '''
    import requests
    try:
        from cachecontrol import CacheControl
        from cachecontrol.caches.file_cache import FileCache
        cachedir = getattr(all_sites, 'cachedir', '@UNKNOWN')
    except ImportError:
        cachedir = None
        pass

    #FIXME: Avoid accumulating all the nodes, which will require improvements to xml.treesequence
    def sink(accumulator):
        while True:
            e = yield
            loc = next(select_name(e, 'loc'))
            lastmod = next(select_name(e, 'lastmod'))
            s = liblink_site()
            s.sitemap = loc.xml_value
            s.url, _, tail = s.sitemap.partition('harvest/sitemap.xml')
            s.base_url = s.url #Legacy property name
            #Early warning for funky URLs breaking stuff downstream
            assert not tail
            protocol, s.host, path, query, fragment = iri.split_uri_ref(s.sitemap)
            s.lastmod = lastmod.xml_value
            accumulator.append(s)

    nodes = []

    ts = xmliter.sender(('sitemapindex', 'sitemap'), sink(nodes))
    if cachedir == '@UNKNOWN':
        sess = CacheControl(requests.Session(), cache=FileCache('.web_cache'))
    elif cachedir:
        sess = CacheControl(requests.Session(), cache=FileCache(cachedir))
    else:
        sess = CacheControl(requests.Session())
    result = sess.get(sitemap_url)
    ts.parse(result.text)
    
    for h in (plus_list or []):
        s = liblink_site()
        s.host = h
        s.base_url = s.url = 'http://' + s.host
        s.sitemap = s.url + '/harvest/sitemap.xml'
        nodes.append(s)
    yield from nodes

