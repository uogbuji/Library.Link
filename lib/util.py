'''
'''

import sys
import logging
import urllib
from itertools import *
from bibframe import BFZ, BL
import requests

#from versa.writer.rdfs import prep as statement_prep
from versa.driver import memory
from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET, ATTRIBUTES
from versa.reader import rdfalite
from versa.reader.rdfalite import RDF_NS, SCHEMAORG_NS
from versa import util

from rdflib import URIRef, Literal
from rdflib import BNode

from amara3 import iri
from amara3.uxml import tree
from amara3.uxml.treeutil import *
from amara3.uxml import html5


def get_orgname(org):
    '''
    Given an organization object as returned from bibframe.zextra.resource.util.all_sites, or just a plain base URL, return the org's name

    >>> from bibframe.zextra.resource.util import all_sites
    >>> from librarylink.util import get_orgname
    >>> org = next(all_sites())
    >>> get_orgname(org)
    >>> get_orgname('http://link.delawarelibrary.org/')
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
            print(o)
            if name is not None: return name
        #schema:Organization not reliable the way it's used in LLN
        #orgentity = util.simple_lookup_byvalue(model, RDF_NS + 'type', SCHEMAORG_NS + 'LibrarySystem')
        #orgentity = util.simple_lookup_byvalue(model, SCHEMAORG_NS + 'url', baseurl)
        #print(orgentity)
        #name = util.simple_lookup(model, orgentity, SCHEMAORG_NS + 'name')
        #name = util.simple_lookup(model, baseurl + '#_default', BL + 'name')
    #return name
