'''

'''

import re
import http
import asyncio
from itertools import *

from versa.driver import memory
from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET, ATTRIBUTES
from versa.reader import rdfalite
from versa.reader.rdfalite import RDF_NS, SCHEMAORG_NS
from versa import util as versautil

#from bibframe import BFZ, BL
#from bibframe.zextra import LL

#from rdflib import URIRef, Literal
#from rdflib import BNode

from amara3 import iri
from amara3.uxml import tree
from amara3.uxml import xml
from amara3.uxml.treeutil import *
from amara3.uxml import html5

RDFTYPE = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
SCHEMAORG = 'http://schema.org/'

LL_RESOURCE_BASE = 'http://library.link/resource/'
LL_ISBN_STEMPLATE = 'http://library.link/id/isbn/{isbn}/brief.json'
OPENLIBRARY_TITLESEARCHBASE = 'http://openlibrary.org/search.json'


async def BUSTED(title, session=None, max_retries=1):
    '''
    Async helper to get information from isbn.nu for a title query
    
    Returns a JSON object

    >>> from amara3.asynctools import go_async
    >>> from librarylink.util import rdfa_from_page
    >>> from versa import util as versautil
    >>> url = "http://library.link/resource/2_8BKlrtCTI/brief.json"
    >>> obj = go_async(network_resource_content(url))
    '''
    for isbn in [ compute_ean13_check(i) for i in c14n_isbns]:
        task = network_isbn_info(isbn)
        tasks.append(task)
    ll_result_sets = await asyncio.gather(*tasks)
    for isbn, result in ll_result_sets:
        #print(isbn, result)
        if result and isbn not in isbns_seen:
            filtered_isbns.append(isbn)
            isbns_seen.add(isbn)
    if filtered_isbns:
        ll_super_list.append({'label': group_label, 'isbns': filtered_isbns})


async def network_isbn_info(isbn, session=None, max_retries=1):
    '''
    Async helper to get JSON content from network resource page
    
    Returns a JSON object

    >>> from amara3.asynctools import go_async
    >>> from librarylink.resource import network_isbn_info
    >>> obj = go_async(network_isbn_info(9780871290861))
    >>> obj['workExample'][0].get('holdings_count')
    19
    '''
    retry_count = 0
    url = LL_ISBN_STEMPLATE.format(**{'isbn': isbn})
    #print('processing', url, file=sys.stderr)
    while True:
        model = memory.connection()
        try:
            if session == None:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        obj = await response.json()
                        return obj
            else:
                async with session.get(url) as response:
                    obj = await response.json()
                    return obj
        except Exception as e:
            #print(url, f'[EXCEPTION {e}], context: {context}', file=sys.stderr)
            retry_count += 1
            if retry_count >= max_retries:
                return None
            await asyncio.sleep(0.2)
