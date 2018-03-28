#!/usr/bin/env python
'''
Run using liblink_crawl

e.g.:

liblink_crawl --script=test/resource/ntriplify.py http://link.delawarelibrary.org/

'''

import os
import re
import sys
import random
from asyncio import Lock

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET, VTYPE_REL
#from versa import util
from versa.driver import memory
#from versa.writer import md
from versa.reader import rdfalite
from versa import util as versautil
from versa.writer import ntriples

from amara3 import iri
from amara3.uxml import html5
from amara3.uxml.treeutil import descendants, select_elements

from librarylink.util import llnurl_ident
from librarylink.crawler.framework import crawltask, base_sink, links_from_html, LIBRARY_LINK_HEADER

SCHEMAORG = 'http://schema.org/'


class ntriplify_sink(base_sink):
    @staticmethod
    def update_cmdline_parser(parser):
        parser.add_argument('--outrdfnt', metavar='PATH',
            help='Full file path stem/prefix for writing NTriples')
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
        cls.logger = logger
        #cls.outfolder = '/tmp/ntrilplified/'
        cls.locks = {}

    #@classmethod
    #def close(cls):
    #    cls.outfp.close()

    def __init__(self, frontpage, **kwargs):
        self._frontpage = frontpage
        _, self._fphost, _, _, _ = iri.split_uri_ref(self._frontpage)
        self.outfolder = kwargs['outrdfnt']
        return

    #XXX: Or do we make this a coroutine?
    async def send(self, data):
        #Body text, response URL (e.g. after redirections), aiohttp.header object from response, referrer, controlling task ID
        (body, respurl, respheaders, referrer, task_id) = data
        _, respurlhost, _, _, _ = iri.split_uri_ref(respurl)
        if self._fphost == respurlhost:
            #ntriplify_sink.logger.debug('[TASK {}]: Target subpage {} -> {}'.format(task_id, referrer, respurl))

            root = html5.parse(body)
            linkset = self._queue_links(root, respurl)
            
            try:
                _, resid = llnurl_ident(respurl)
            except ValueError:
                resid = None
            if resid:
                #Lock the file for 
                resstem = resid[:3]
                ntriplify_sink.locks.setdefault(resstem, Lock())
                await ntriplify_sink.locks[resstem]
                try:
                    #Note:
                    #timeit.timeit(‘rdfalite.toversa(open(“index.html”).read(), model, “http://link.delawarelibrary.org/portal/Nest-Esther-Ehrlich-overdrive-ebook/F-h_bGCl5lk/“)’, setup=‘from versa.driver import memory; from versa.reader import rdfalite; model = memory.connection()’, number=10)
                    #4.412366830001702
                    #timeit.timeit(‘g = rdflib.Graph(); g.parse(“index.html”, format=“html”)’, setup=‘import rdflib’, number=10)
                    #[snip tons of warnings]
                    #16.82040351499745
                    #IOW Versa is 4X faster than RDFlib for this task, and more robust
                    with open(os.path.join(self.outfolder, resstem + '.nt'), 'a') as resstem_fp:
                        model = memory.connection()
                        rdfalite.toversa(body, model, respurl)
                        ntriples.write(model, out=resstem_fp, base=respurl, logger=ntriplify_sink.logger)
                finally:
                    ntriplify_sink.locks[resstem].release()

            #self.save_ntriples()
            return linkset
        return None


LLCRAWL_CLASS = ntriplify_sink
