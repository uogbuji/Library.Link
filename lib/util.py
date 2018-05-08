'''
'''

import re
import sys
import logging
import urllib
import urllib.request
from itertools import *
import collections.abc

import requests
try:
    from cachecontrol import CacheControl
    from cachecontrol.caches.file_cache import FileCache
    CACHEDIR = '.web_cache'
except ImportError:
    CACHEDIR = None

from versa.driver import memory
from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET, ATTRIBUTES
from versa.reader import rdfalite
from versa.reader.rdfalite import RDF_NS, SCHEMAORG_NS
from versa import util as versautil

from bibframe import BFZ, BL
from bibframe.zextra import LL

from rdflib import URIRef, Literal
from rdflib import BNode

from amara3 import iri
from amara3.uxml import tree
from amara3.uxml import xml
from amara3.uxml.treeutil import *
from amara3.uxml import html5

RDFTYPE = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
SCHEMAORG = 'http://schema.org/'


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
            s.url, _, tail = s.sitemap.partition('harvest/sitemap.xml')
            s.base_url = s.url #Legacy property name
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


if CACHEDIR: all_sites.cachedir = '.web_cache'


def load_rdfa_page(site):
    '''
    Helper to load RDFa page as text, plus load a Versa model with the metadata
    
    Returns a versa memory model and the raw site text, except in eror case where it returns None and the error
    '''
    model = memory.connection()
    try:
        with urllib.request.urlopen(site) as resourcefp:
            sitetext = resourcefp.read()
            rdfalite.toversa(sitetext, model, site)
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        return None, e
    return model, sitetext


#Legacy name
prep_site_model = load_rdfa_page

def rdf_from_site(site, rules=None):
    '''
    >>> from librarylink.util import rdf_from_site
    >>> g = rdf_from_site('http://link.denverlibrary.org')
    >>> s = g.serialize(format='json-ld', indent=2)
    >>> with open('denverlibrary.ld.json', 'wb') as fp: fp.write(s)

    >>> rules = {'ignore-predicates': ['http://bibfra.me/', 'http://library.link/'], 'rename-predicates': {'http://library.link/vocab/branchOf': 'http://schema.org/branch'}}
    >>> g = rdf_from_site('http://link.denverlibrary.org', rules=rules)
    >>> s = g.serialize(format='json-ld', indent=2)
    >>> with open('denverlibrary.ld.json', 'wb') as fp: fp.write(s)
    '''
    from rdflib import ConjunctiveGraph, URIRef, Literal, RDF, RDFS
    from versa.writer.rdf import mock_bnode, prep, RDF_TYPE
    #Also requires: pip install rdflib-jsonld
    rules = rules or {}
    ignore_pred = rules.get('ignore-predicates', set())
    rename_pred = rules.get('rename-predicates', {})
    model, sitetext = load_rdfa_page(site)
    if not model:
        return None
    g = ConjunctiveGraph()
    #Hoover up everything with a type
    for o, r, t, a in model.match():
        for oldp, newp in rename_pred.items():
            if r == oldp: r = newp
        for igp in ignore_pred:
            if r.startswith(igp):
                break
        else:
            g.add(prep(o, r, t))
    return g


def jsonize_site(site, rules=None):
    '''
    >>> from librarylink.util import jsonize_site
    >>> obj = jsonize_site('http://link.denverlibrary.org')
    >>> with open('denverlibrary.ld.json', 'w') as fp: json.dump(obj, fp, indent=2)

    >>> rules = {'ignore-predicates': ['http://bibfra.me/', 'http://library.link/'], 'rename-predicates': {'http://library.link/vocab/branchOf': 'http://schema.org/branch'}}
    >>> obj = jsonize_site('http://link.denverlibrary.org', rules=rules)
    >>> with open('denverlibrary.ld.json', 'w') as fp: json.dump(obj, fp, indent=2)
    '''
    from versa.util import uniquify
    from versa.writer import jsonld
    rules = rules or {}
    ignore_pred = rules.get('ignore-predicates', set())
    rename_pred = rules.get('rename-predicates', {})
    ignore_oftypes = rules.get('ignore-oftypes', [])
    invert = rules.get('invert', {})
    context = rules.get('context', {})
    pre_model, _ = load_rdfa_page(site)
    if not pre_model:
        return None
    uniquify(pre_model)
    post_model = memory.connection()
    for o, r, t, a in pre_model.match():
        #print(o, r, t)
        for oldp, newp in rename_pred.items():
            if r == oldp: r = newp
        for rpre, rpost in invert.items():
            if r == rpre:
                assert isinstance(t, I)
                o, r, t = t, rpost, o
        for igp in ignore_pred:
            if r.startswith(igp):
                break
        else:
            post_model.add(o, r, t, a)
    obj = jsonld.bind(post_model, context=context, ignore_oftypes=ignore_oftypes)
    return obj


def get_orgname(site, reuse=None):
    '''
    Given a site URL return the org's name

    >>> from librarylink.util import all_sites, get_orgname
    >>> org = next(s for s in all_sites() if 'denverlibrary' in s.host )
    >>> get_orgname(org)
    'Denver Public Library'
    >>> get_orgname('http://link.denverlibrary.org/')
    'Denver Public Library'
    '''
    if reuse:
        model, sitetext = reuse
    else:
        model, sitetext = load_rdfa_page(site)
    if not model:
        return None
    for o, r, t, a in model.match(None, RDF_NS + 'type', SCHEMAORG_NS + 'Organization'):
        name = versautil.simple_lookup(model, o, SCHEMAORG_NS + 'name')
        if name is not None: return name
    #schema:Organization not reliable the way it's used in LLN
    #orgentity = versautil.simple_lookup_byvalue(model, RDF_NS + 'type', SCHEMAORG_NS + 'LibrarySystem')
    #orgentity = versautil.simple_lookup_byvalue(model, SCHEMAORG_NS + 'url', baseurl)
    #print(orgentity)
    #name = versautil.simple_lookup(model, orgentity, SCHEMAORG_NS + 'name')
    #name = versautil.simple_lookup(model, baseurl + '#_default', BL + 'name')
    #return name


NETWORK_HINTS = {
    #e.g. from http://augusta.library.link/
    #<link href="/static/liblink_ebsco/css/network.css" rel="stylesheet">
    b'liblink_ebsco/css/network.css': 'ebsco',
    #e.g. from http://msu.library.link/
    #<link href="/static/liblink_iii/css/network.css" rel="stylesheet"/>
    b'liblink_iii/css/network.css': 'iii',
    #e.g. from http://link.houstonlibrary.org/
    #<link href="/static/liblink_bcv/css/network.css" rel="stylesheet"/>
    b'liblink_bcv/css/network.css': 'bcv',
    #e.g. from http://link.library.gmu.edu/
    #<link href="/static/liblink_atlas/css/network.css" rel="stylesheet"/>
    b'liblink_atlas/css/network.css': 'atlas',
}


PIPELINE_VERSION_PAT = re.compile(b'<dt>Transformation Pipeline</dt>\s*<dd>([^<]*)</dd>', re.MULTILINE)
TEMPLATE_VERSION_PAT = re.compile(b'<dt>Template Version</dt>\s*<dd>([^<]*)</dd>', re.MULTILINE)
def get_orgdetails(site, reuse=None):
    '''
    Given an organization object as returned from librarylink.util.all_sites, or just a plain base URL string; return the org's name
    >>> from librarylink.util import all_sites, get_orgdetails
    >>> det = get_orgdetails('http://link.dcl.org/')
    >>> det['name']
    'Douglas County Libraries'
    >>> org = next(s for s in all_sites() if 'denverlibrary' in s.host )
    >>> det = get_orgdetails(org.base_url)
    >>> det['name']
    'Denver Public Library'
    '''
    if reuse:
        model, sitetext = reuse
    else:
        model, sitetext = load_rdfa_page(site)
    if not model:
        return None
    details = {'name': None, 'group': None, 'groupname': None, 'network': None, 'features': set()}
    id_ = None
    for o, r, t, a in model.match(None, RDF_NS + 'type', SCHEMAORG_NS + 'LibrarySystem'):
        id_ = o
        details['name'] = next(versautil.lookup(model, o, SCHEMAORG_NS + 'name'), '').strip()
        break

    details['id'] = id_
    #for o, r, t, a in model.match(None, SCHEMAORG_NS + 'member'):
    #    group = t.split('#')[0]
    for o, r, t, a in model.match(None, RDF_NS + 'type', SCHEMAORG_NS + 'Consortium'):
        details['group'] = versautil.simple_lookup(model, o, SCHEMAORG_NS + 'url')
        #group = o.split('#')[0]
        details['groupname'] = next(versautil.lookup(model, o, SCHEMAORG_NS + 'name'), '').strip()
        break

    network = 'zviz'
    for searchstr in NETWORK_HINTS:
        if searchstr in sitetext:
            details['network'] = NETWORK_HINTS[searchstr]

    m = PIPELINE_VERSION_PAT.search(sitetext)
    if m:
        details['pipeline_ver'] = m.group(1).decode('utf-8')
    else:
        details['pipeline_ver'] = None
        #print('Unable to get pipeline version from:', site)
    m = TEMPLATE_VERSION_PAT.search(sitetext)
    if m:
        details['template_ver'] = m.group(1).decode('utf-8')
    else:
        details['template_ver'] = None
        #print('Unable to get template version from:', site)

    for o, r, t, a in model.match(None, LL+'feature'):
        details['features'].add(t)

    #Legacy, for libraries where the above isn't published
    if b'<img class="img-responsive" src="/static/liblink_ea/img/nlogo.png"' in sitetext:
        details['features'].add('http://library.link/ext/feature/novelist/merge')

    details['same-as'] = []
    for o, r, t, a in model.match(None, RDF_NS + 'type', SCHEMAORG_NS + 'LibrarySystem'):
        for _, r, t, a in model.match(o, SCHEMAORG_NS + 'sameAs'):
            details['same-as'].append(t)
        break

    for o, r, t, a in model.match(None, RDF_NS + 'type', SCHEMAORG_NS + 'LibrarySystem'):
        logo = versautil.simple_lookup(model, o, SCHEMAORG_NS + 'logo')
        details['logo'] = logo.strip() if logo else logo
        break

    return details


def get_branches(site, reuse=None):
    '''
    Given an organization object as returned from librarylink.util.all_sites, or just a plain base URL string; return the org's name
    >>> from librarylink.util import all_sites, get_branches
    >>> org = next(s for s in all_sites() if 'denverlibrary' in s.host )
    >>> get_branches(org)
    'Denver Public Library'
    >>> get_branches('http://link.denverlibrary.org/')
    'Denver Public Library'
    '''
    if reuse:
        model, sitetext = reuse
    else:
        model, sitetext = load_rdfa_page(site)
    if not model:
        return None
    branches = []
    for o, r, t, a in model.match(None, RDF_NS + 'type', SCHEMAORG_NS + 'Library'):
        id_ = o
        name = next(versautil.lookup(model, o, SCHEMAORG_NS + 'name'), '').strip()
        url = versautil.simple_lookup(model, o, SCHEMAORG_NS + 'url')
        loc = versautil.simple_lookup(model, o, SCHEMAORG_NS + 'location')
        addr = versautil.simple_lookup(model, o, SCHEMAORG_NS + 'address')
        #Goes schema:Library - schema:location -> schema:Place - schema:geo -> Coordinates
        if loc:
            loc = versautil.simple_lookup(model, loc, SCHEMAORG_NS + 'geo')
        if loc:
            lat = versautil.simple_lookup(model, loc, SCHEMAORG_NS + 'latitude')
            long_ = versautil.simple_lookup(model, loc, SCHEMAORG_NS + 'longitude')

        if addr:
            #rdf:type	schema:PostalAddress
            #schema:streetAddress	"2111 Snow Road"@en
            #schema:addressLocality	"Parma"@en
            #schema:addressRegion	"OH"@en
            #schema:postalCode	"44134"@en
            #schema:addressCountry	"US"@en
            street = versautil.simple_lookup(model, addr, SCHEMAORG_NS + 'streetAddress')
            locality = versautil.simple_lookup(model, addr, SCHEMAORG_NS + 'addressLocality')
            region = versautil.simple_lookup(model, addr, SCHEMAORG_NS + 'addressRegion')
            postcode = versautil.simple_lookup(model, addr, SCHEMAORG_NS + 'postalCode')
            country = versautil.simple_lookup(model, addr, SCHEMAORG_NS + 'addressCountry')

        branches.append((
            id_,
            url,
            name,
            (lat, long_) if loc else None,
            (street, locality, region, postcode, country) if addr else None
        ))

    return branches


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
    try:
        if path.startswith('/resource/'):
            rhash = path.partition('/resource/')[-1].split('/')[0]
        elif '/portal/' in url:
            rhash = path.partition('/portal/')[-1].split('/')[1]
        else:
            raise ValueError('Invalid LLN URL: ' + repr(url))
    except IndexError as e:
        #FIXME L10N
        raise ValueError('Invalid LLN URL: ' + repr(url))
    return host, rhash


def simplify_link(url):
    '''
    Return a simplified & unique form of an LLN URL

    >>> from librarylink.util import simplify_link
    >>> simplify_link('http://link.worthingtonlibraries.org/resource/9bz8W30aSZY/')
    'http://link.worthingtonlibraries.org/resource/9bz8W30aSZY/'
    >>> simplify_link('http://link.worthingtonlibraries.org/portal/Unshakeable--your-financial-freedom-playbook/cZlfLtSpcng/')
    'http://link.worthingtonlibraries.org/portal/Unshakeable--your-financial-freedom-playbook/cZlfLtSpcng/'
    >>> simplify_link('http://link.worthingtonlibraries.org/portal/Unshakeable--your-financial-freedom-playbook/cZlfLtSpcng/borrow/')
    'http://link.worthingtonlibraries.org/portal/Unshakeable--your-financial-freedom-playbook/cZlfLtSpcng/'
    >>> simplify_link('http://link.worthingtonlibraries.org/res/9bz8W30aSZY/boo/') is None
    True
    >>> simplify_link('http://link.worthingtonlibraries.org/resource/9bz8W30aSZY/boo/')
    'http://link.worthingtonlibraries.org/resource/9bz8W30aSZY/'
    >>> simplify_link('/res/9bz8W30aSZY/boo/') is None
    True
    >>> simplify_link('/resource/9bz8W30aSZY/boo/')
    '/resource/9bz8W30aSZY/'
    >>> simplify_link('https://link.worthingtonlibraries.org/resource/9bz8W30aSZY/')
    'https://link.worthingtonlibraries.org/resource/9bz8W30aSZY/'
    >>> simplify_link('https://link.worthingtonlibraries.org/resource/9bz8W30aSZY/borrow/')
    'https://link.worthingtonlibraries.org/resource/9bz8W30aSZY/'
    '''
    scheme, auth, path, query, fragment = iri.split_uri_ref(url)
    try:
        if path.startswith('/resource/'):
            path = '/resource/' + path.partition('/resource/')[-1].split('/')[0] + '/'
            return iri.unsplit_uri_ref((scheme, auth, path, None, None))
        if '/portal/' in url:
            path = '/portal/' + '/'.join(path.partition('/portal/')[-1].split('/')[:2]) + '/'
            return iri.unsplit_uri_ref((scheme, auth, path, None, None))
        else:
            path = None
    except IndexError as e:
        #FIXME L10N
        raise ValueError('Invalid LLN URL: ' + repr(url))
    return path


class liblink_set(collections.abc.MutableSet):
    '''
    Smart collection of URLs that understands Library.Link URLs and how to dedup them for set operations
    It can also manage a set of exclusions, e.g. to eliminate a URL for repeat processing
    '''
    def __init__(self, iterable=None):
        self._rawset = set()
        self._exclusions = set()
        if iterable is not None:
            self |= iterable

    def add(self, item):
        simplified = simplify_link(item) or item
        if simplified not in self._exclusions:
            self._rawset.add(simplified)

    def exclude(self, item):
        simplified = simplify_link(item) or item
        self._rawset.discard(simplified)
        self._exclusions.add(simplified)

    def __len__(self):
        return len(self._rawset)

    def __contains__(self, item):
        simplified = simplify_link(item) or item
        return simplified in self._rawset

    def discard(self, item):
        simplified = simplify_link(item) or item
        self._rawset.discard(simplified)

    def __iter__(self):
        yield from self._rawset

    def __repr__(self):
        s = 'RAWSET: ' + repr(self._rawset) + '\n' + 'EXCLUSIONS: ' + repr(self._exclusions)
        return s


class liblink_site(object):
    '''
    High-level (sitemap-style) information about a Library.Link site
    
    >>> from librarylink.util import liblink_site
    >>> s = liblink_site('http://link.worthingtonlibraries.org')
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
