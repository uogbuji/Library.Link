#!/usr/bin/env python
'''
Run using liblink_crawl

e.g.:

liblink_crawl --script=test/resource/quickinfo.py http://link.anythinklibraries.org/

'''

import re
import sys
import random

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET, VTYPE_REL
#from versa import util
from versa.driver import memory
#from versa.writer import md
from versa.reader import rdfalite
from versa import util as versautil

from amara3 import iri
from amara3.uxml import html5
from amara3.uxml.treeutil import descendants, select_elements

from librarylink.crawler.framework import crawltask, base_sink, links_from_html, LIBRARY_LINK_HEADER

SCHEMAORG = 'http://schema.org/'


class quickinfo_sink(object):
    @staticmethod
    def update_cmdline_parser(parser):
        # parser.add_argument('--outrdfttl', metavar='PATH',
        #     help='Full file path stem/prefix for writing RDF/TTL')
        # parser.add_argument('--outrdfxml', metavar='PATH',
        #     help='Full file path stem/prefix for writing RDF/XML')
        # parser.add_argument('--outversajson', metavar='PATH',
        #     help='Full file path stem/prefix for writing Versa/JSON')
        # parser.add_argument('--outversamd', metavar='PATH',
        #     help='Full file path stem/prefix for writing Versa/Literate')
        return

    @classmethod
    def setparams(cls, pagesperfile, logger):
        cls.pagesperfile = pagesperfile
        cls.logger = logger
        cls.outfp = open('/tmp/getinfo.txt', 'w')

    @classmethod
    def close(cls):
        cls.outfp.close()

    def __init__(self, frontpage, **kwargs):
        self._frontpage = frontpage
        _, self._fphost, _, _, _ = iri.split_uri_ref(self._frontpage)
        return

    #FIXME: Or do we make this a coroutine?
    def send(self, data):
        #Body text, respunse URL (e.g. after redirections), aiohttp.header object from response, referrer, controlling task ID
        (body, respurl, respheaders, referrer, task_id) = data
        _, respurlhost, _, _, _ = iri.split_uri_ref(respurl)
        if LIBRARY_LINK_HEADER not in respheaders:
            #Not even an LLN page at all
            return
        if self._fphost == respurlhost:
            output_model = memory.connection()
            quickinfo_sink.logger.debug('[TASK {}]: Target subpage {} -> {}'.format(task_id, referrer, respurl))
            #Subpage of the target site
            rdfalite.toversa(body, output_model, respurl)
            resname = versautil.simple_lookup(output_model, respurl, SCHEMAORG + 'name')
            print(respurl, '|', resname, file=quickinfo_sink.outfp)
            #orgentity = util.simple_lookup_byvalue(model, RDFTYPE, SCHEMAORG + 'Organization')
            #name = util.simple_lookup(model, orgentity, BL + 'name')
            #name = util.simple_lookup(model, baseurl + '#_default', BL + 'name')

            root = html5.parse(body)
            linkset = self._queue_links(root, respurl)
        return linkset

    def _queue_links(self, root, respurl):
        linkset = set()
        for link in links_from_html(root, respurl):
            #If you wanted to not even visit any resources outside this domain, here is how
            #_, linkhost, _, _, _ = iri.split_uri_ref(link)
            #if self._fphost == linkhost:
            #    link, frag = iri.split_fragment(link)
            #    linkset.add(link)

            link, frag = iri.split_fragment(link)
            linkset.add(link)
        if linkset: self._linkset_q.put_nowait((respurl, linkset))
        return



LLCRAWL_CLASS = quickinfo_sink
