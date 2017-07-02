'''
'''

import sys
import logging
import urllib
from itertools import *
import collections.abc

import requests

#from versa.writer.rdfs import prep as statement_prep
from versa.driver import memory
from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET, ATTRIBUTES
from versa.reader import rdfalite
from versa.reader.rdfalite import RDF_NS, SCHEMAORG_NS
from versa import util

from bibframe import BFZ, BL

from rdflib import URIRef, Literal
from rdflib import BNode

from amara3 import iri
from amara3.uxml import tree
from amara3.uxml import xml
from amara3.uxml.treeutil import *
from amara3.uxml import html5


def all_sites(sitemap_url='http://library.link/harvest/sitemap.xml'):
    '''
    >>> from librarylink.util import all_sites
    >>> [ s.host for s in all_sites() if 'denverlibrary' in s.host ]
    ['link.denverlibrary.org']
    '''
    #FIXME: Avoid accumulating all the nodes, which will require improvements to xml.treesequence
    @coroutine
    def sink(accumulator):
        while True:
            e = yield
            loc = next(select_name(e, 'loc'))
            lastmod = next(select_name(e, 'lastmod'))
            s = liblink_site()
            s.sitemap = loc.xml_value
            s.base_url, _, tail = s.sitemap.partition('harvest/sitemap.xml')
            #Early warning for funky URLs breaking stuff downstream
            assert not tail
            protocol, s.host, path, query, fragment = iri.split_uri_ref(s.sitemap)
            s.lastmod = lastmod.xml_value
            accumulator.append(s)

    nodes = []
    ts = xml.treesequence(('sitemapindex', 'sitemap'), sink(nodes))
    if hasattr (all_sites, 'cachedir'):
        sess = CacheControl(requests.Session(), cache=FileCache(all_sites.cachedir))
    else:
        sess = CacheControl(requests.Session())
    result = sess.get(sitemap_url)
    ts.parse(result.text)
    yield from nodes

try:
    from cachecontrol import CacheControl
    from cachecontrol.caches.file_cache import FileCache
    all_sites.cachedir = '.web_cache'
except ImportError:
    pass


# sites = list(all_sites())

def get_orgname(org):
    '''
    Given an organization object as returned from librarylink.util.all_sites, or just a plain base URL string; return the org's name

    >>> from librarylink.util import all_sites, get_orgname
    >>> org = next(s for s in all_sites() if 'denverlibrary' in s.host )
    >>> get_orgname(org)
    'Denver Public Library'
    >>> get_orgname('http://link.denverlibrary.org/')
    'Denver Public Library'
    '''
    if isinstance(org, str):
        baseurl = org
    else:
        baseurl = org.sitemap.partition('harvest/sitemap.xml')[0]
    model = memory.connection()
    with urllib.request.urlopen(baseurl) as resourcefp:
        rdfalite.toversa(resourcefp.read(), model, baseurl)
        for o, r, t, a in model.match(None, RDF_NS + 'type', SCHEMAORG_NS + 'Organization'):
            name = util.simple_lookup(model, o, SCHEMAORG_NS + 'name')
            if name is not None: return name
        #schema:Organization not reliable the way it's used in LLN
        #orgentity = util.simple_lookup_byvalue(model, RDF_NS + 'type', SCHEMAORG_NS + 'LibrarySystem')
        #orgentity = util.simple_lookup_byvalue(model, SCHEMAORG_NS + 'url', baseurl)
        #print(orgentity)
        #name = util.simple_lookup(model, orgentity, SCHEMAORG_NS + 'name')
        #name = util.simple_lookup(model, baseurl + '#_default', BL + 'name')
    #return name


def llnurl_ident(url):
    '''
    Return the identifying pair of (site, hash) from an LLN URL

    >>> from librarylink.util import llnurl_ident
    >>> llnurl_ident('http://link.worthingtonlibraries.org/resource/9bz8W30aSZY/')
    ('link.worthingtonlibraries.org', '9bz8W30aSZY')
    >>> llnurl_ident('http://link.worthingtonlibraries.org/portal/Unshakeable--your-financial-freedom-playbook/cZlfLtSpcng/')
    ('link.worthingtonlibraries.org', 'cZlfLtSpcng')
    '''
    scheme, host, path, query, fragment = iri.split_uri_ref(url)
    if path.startswith('/resource/'):
        rhash = path.partition('/resource/')[-1].split('/')[0]
    elif '/portal/' in url:
        rhash = path.partition('/portal/')[-1].split('/')[1]
    return host, rhash


def simplify_link(url):
    '''
    Return a simplified & unique form of an LLN URL

    >>> from librarylink.util import simplify_link
    >>> simplify_link('http://link.worthingtonlibraries.org/resource/9bz8W30aSZY/')
    ('link.worthingtonlibraries.org', '9bz8W30aSZY')
    >>> simplify_link('http://link.worthingtonlibraries.org/portal/Unshakeable--your-financial-freedom-playbook/cZlfLtSpcng/')
    ('link.worthingtonlibraries.org', 'cZlfLtSpcng')
    '''
    scheme, auth, path, query, fragment = iri.split_uri_ref(url)
    if path.startswith('/resource/'):
        path = '/resource/' + path.partition('/resource/')[-1].split('/')[0] + '/'
        return iri.unsplit_uri_ref((scheme, auth, path, None, None))
    if '/portal/' in url:
        path = '/portal/' + '/'.join(path.partition('/portal/')[-1].split('/')[:2]) + '/'
        return iri.unsplit_uri_ref((scheme, auth, path, None, None))


class liblink_set(collections.abc.MutableSet):
    '''
    Smart collection of URLs that is smart about Library.Link URLs and how to dedup them for set operations
    '''
    def __init__(self, iterable=None):
        self.rawset = set()
        if iterable is not None:
            self |= iterable

    def add(self, item):
        simplified = simplify_link(item) or item
        self.rawset.add(simplified)

    def __len__(self):
        return len(self.rawset)

    def __contains__(self, item):
        simplified = simplify_link(item) or item
        return simplified in self.rawset

    def discard(self, item):
        simplified = simplify_link(item) or item
        self.rawset.discard(simplified)

    def __iter__(self):
        yield from self.rawset

    #?
    #def __reversed__(self):
    #def pop(self, last=True):
    #def __repr__(self):

class liblink_site(object):
    pass
