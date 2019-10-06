'''

'''

import re
import http
#import urllib
#import urllib.request
from itertools import *

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


async def openlibrary_search_title(title, session=None, max_retries=1):
    '''
    Async helper to get information from isbn.nu for a title query
    
    Returns a JSON object

    >>> from amara3.asynctools import go_async
    >>> from librarylink.util import rdfa_from_page
    >>> from versa import util as versautil
    >>> url = "http://library.link/resource/2_8BKlrtCTI/brief.json"
    >>> obj = go_async(network_resource_content(url))
    '''

    retry_count = 0
    qparams = {'title': title}
    while True:
        model = memory.connection()
        try:
            if session == None:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(OPENLIBRARY_TITLESEARCHBASE, params=qparams) as response:
                        #OL doesn't use proper response type, so gotta disable checks: https://docs.aiohttp.org/en/stable/client_advanced.html#disabling-content-type-validation-for-json-responses
                        obj = await response.json(content_type=None)
                        return obj
            else:
                async with session.get(OPENLIBRARY_TITLESEARCHBASE, params=qparams) as response:
                    obj = await response.json(content_type=None)
                    return obj
        except Exception as e:
            print(f'title: {title}, EXCEPTION {e}')
            retry_count += 1
            if retry_count >= max_retries:
                return None


