#!/usr/bin/env python
'''
Run using liblink_crawl

e.g.:

liblink_crawl --script=test/resource/csvexport.py http://link.delawarelibrary.org/

'''

import os
import re
import sys
import gzip
import csv
from asyncio import Lock

from versa import I, VERSA_BASEIRI, ORIGIN, RELATIONSHIP, TARGET, VTYPE_REL
#from versa import util
from versa.driver import memory
#from versa.writer import md
from versa.reader import rdfalite
from versa import util as versautil
from versa.writer import csv as vcsv

from amara3 import iri
from amara3.uxml import html5
from amara3.uxml.treeutil import descendants, select_elements

from librarylink.util import llnurl_ident
from librarylink.crawler.framework import crawltask, base_sink, links_from_html, LIBRARY_LINK_HEADER

SCHEMAORG = 'http://schema.org/'
HASH_WIDTH = 2

class csvexport_sink(base_sink):
    @staticmethod
    def update_cmdline_parser(parser):
        parser.add_argument('--csvexport', metavar='PATH',
            help='Full file path stem/prefix for writing CSV')
        parser.add_argument('--config', metavar='FILEPATH',
            help='File containing translation rules from LD to CSV')
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
        cls.locks = {}

    #@classmethod
    #def close(cls):
    #    cls.outfp.close()

    def __init__(self, frontpage, **kwargs):
        self._frontpage = frontpage
        _, self._fphost, _, _, _ = iri.split_uri_ref(self._frontpage)
        self.outfolder = kwargs['csvexport']
        from bibframe import BFZ, BL, BA, REL, MARC
        self.rules = [
            (BL + 'controlCode', 'controlCode'),
            (BL + 'instantiates', 'instantiates'),
            (BL + 'link', 'link'),
            (BL + 'title', 'title'),
            (BL + 'name', 'name'),
            (BL + 'providerDate', 'providerDate'),
            (BL + 'providerPlace', 'providerPlace'),
            (BL + 'creator', 'creator'),
            (BL + 'genre', 'genre'),
            (BL + 'language', 'language'),
            (BL + 'subject', 'subject'),
            (BL + 'controlCode', 'controlCode'),
            (BL + 'focus', 'focus'),
            (BL + 'date', 'date'),
            (MARC + 'isbn', 'isbn'),
            (MARC + 'lccn', 'lccn'),
            (MARC + 'titleStatement', 'titleStatement'),
            (MARC + 'lcCallNumber', 'lcCallNumber'),
            (MARC + 'lcItemNumber', 'lcItemNumber'),
            (MARC + 'literaryForm', 'literaryForm'),
            (MARC + 'seriesStatement', 'seriesStatement'),
            (MARC + 'formSubdivision', 'formSubdivision'),
        ]
        return

    #XXX: Or do we make this a coroutine?
    async def send(self, data):
        #Body text, response URL (e.g. after redirections), aiohttp.header object from response, referrer, controlling task ID
        (body, respurl, respheaders, referrer, task_id) = data
        _, respurlhost, _, _, _ = iri.split_uri_ref(respurl)
        if self._fphost == respurlhost:
            #csvexport_sink.logger.debug('[TASK {}]: Target subpage {} -> {}'.format(task_id, referrer, respurl))

            root = html5.parse(body)
            linkset = self._queue_links(root, respurl)
            
            try:
                _, resid = llnurl_ident(respurl)
            except ValueError:
                resid = None
            if resid:
                model = memory.connection()
                rdfalite.toversa(body, model, respurl)
                #Lock the file for 
                resstem = resid[:HASH_WIDTH]
                csvexport_sink.locks.setdefault(resstem, Lock())
                #csvexport_sink.logger.debug('Awaiting lock on {}; TASK [{}].'.format(resstem, task_id))
                print('Awaiting lock on {}; TASK [{}].'.format(resstem, task_id), file=sys.stderr)
                await csvexport_sink.locks[resstem]
                print('Acquired lock on {}; TASK [{}].'.format(resstem, task_id), file=sys.stderr)

                try:
                    resstem_fpath = os.path.join(self.outfolder, resstem + '.csv')
                    csvexists = os.path.exists(resstem_fpath)
                    #with gzip.open(resstem_fpath, 'at', newline='') as resstem_fp:
                    with open(resstem_fpath, 'at', newline='') as resstem_fp:
                        resstem_csv = csv.writer(resstem_fp, delimiter=',',
                                                    quotechar='"', quoting=csv.QUOTE_MINIMAL)
                        vcsv.write(model, resstem_csv, self.rules, not csvexists, base=respurl, logger=csvexport_sink.logger)
                finally:
                    csvexport_sink.locks[resstem].release()
                    #csvexport_sink.logger.debug('Released lock on {}; TASK [{}].'.format(resstem, task_id))
                    print('Released lock on {}; TASK [{}].'.format(resstem, task_id), file=sys.stderr)

            #self.save_ntriples()
            return linkset
        return None


LLCRAWL_CLASS = csvexport_sink
