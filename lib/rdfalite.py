'''
'''

import sys
import logging
import urllib.request
from itertools import *

#from versa.writer.rdfs import prep as statement_prep
from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET, ATTRIBUTES

from rdflib import URIRef, Literal
from rdflib import BNode

from amara3 import iri
from amara3.uxml import tree
from amara3.uxml.treeutil import *
from amara3.uxml import html5

RDF_NS = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
SCHEMA_NS = 'http://schema.org'
FOAF_NS = 'http://xmlns.com/foaf/0.1/'
DC_NS = 'http://purl.org/dc/terms/'

DEFAULT_PREFIXES = {
    'rdf': RDF_NS,
    'schema': SCHEMA_NS,
    'foaf': FOAF_NS,
    'dc': DC_NS
}

logger = logging.getLogger('rdfalite')
verbose = True
if verbose:
    logger.setLevel(logging.DEBUG)

BNODE_ROOT = 'urn:amara-bnode:_'

#Coroutine to keep triples raw as they are
def dumb_triples(output):
    while True:
        triple = yield
        output.append(triple)
    return


def statement_prep(link):
    '''
    Prepare a statement into a triple ready for rdflib
    '''
    s, p, o = link[:3]
    if not isinstance(s, BNode): s = URIRef(s)
    p = URIRef(p)
    if not isinstance(o, BNode): o = URIRef(o) if isinstance(o, I) else Literal(o)
    return s, p, o


#Coroutine to convert triples to RDF
def direct_rdf(g):
    while True:
        triple = yield
        (s, p, o) = statement_prep(triple)
        g.add((s, p, o))
    return


def parse(htmlsource, source_uri, statement_sink):
    '''

    '''
    root = html5.parse(htmlsource)

    g_bnode_counter = 1
    def do_parse(elem, resource, vocab=None, prop=None, prefixes=None):
        nonlocal g_bnode_counter
        prefixes = prefixes or DEFAULT_PREFIXES.copy()
        vocab = elem.xml_attributes.get('vocab', vocab)
        #element_satisfied = False
        if vocab:
            typeof_list = elem.xml_attributes.get('typeof')
            if typeof_list:
                for typeof in typeof_list.split():
                    typeof = I(vocab + typeof.lstrip('/'))
                    statement_sink.send((resource, RDF_NS + 'type', typeof))
            prefix = elem.xml_attributes.get('prefix')
            if prefix:
                logging.debug('{}'.format(prefix))
                a, b = tee(prefix.split())
                next(b, None)
                for p, ns in zip(a, b):
                    p = p.strip().strip(':')
                    ns = ns.strip()
                    #print(p, ns)
                    prefixes[p] = ns
            new_resource = elem.xml_attributes.get('resource')
            if new_resource:
                resource = I(iri.absolutize(new_resource.lstrip('/'), source_uri))
            new_prop_list = elem.xml_attributes.get('property')
            new_value = None
            if new_prop_list:
                if typeof_list and not new_resource:
                    new_value = BNode()
                    #new_value = I(BNODE_ROOT + str(g_bnode_counter))
                    #g_bnode_counter += 1
                for new_prop in new_prop_list.split():
                    if ':' in new_prop:
                        p, local = new_prop.split(':', 1)
                        if not p in prefixes:
                            #Silent error for now
                            continue
                        prop = I(prefixes[p] + new_prop.lstrip('/'))
                    else:
                        prop = I(vocab + new_prop.lstrip('/'))
                    value = new_value or elem.xml_attributes.get('content') or elem.xml_value
                    statement_sink.send((resource, prop, value))
                    #print((resource, prop, value))
                    logging.debug('{}'.format((resource, prop, value)))
                    #element_satisfied = True
            if new_value: resource = new_value
        for child in elem.xml_children:
            if isinstance(child, element):
                do_parse(child, resource, vocab=vocab, prop=prop, prefixes=prefixes)

    do_parse(root, source_uri)
    return
