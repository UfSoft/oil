# -*- coding: utf-8 -*-
# vim: sw=4 ts=4 fenc=utf-8
# =============================================================================
# $Id: __init__.py 7 2007-08-23 07:23:55Z s0undt3ch $
# =============================================================================
#             $URL: http://oil.ufsoft.org/svn/trunk/oil/IRC/__init__.py $
# $LastChangedDate: 2007-08-23 08:23:55 +0100 (Thu, 23 Aug 2007) $
#             $Rev: 7 $
#   $LastChangedBy: s0undt3ch $
# =============================================================================
# Copyright (C) 2007 Ufsoft.org - Pedro Algarvio <ufs@ufsoft.org>
#
# Please view LICENSE for additional licensing information.
# =============================================================================

#import oil.model as model
#from oil.IRC import irclib
import Queue

import logging

log = logging.getLogger(__name__)

class ProcessQueue(object):
    def __init__(self):
        self.queue = Queue.Queue()

    def add(self, callable, *args, **kwargs):
        self.queue.put((callable, args, kwargs))

    def process_queue(self):
        processing = True
        while processing:
            self.queue.put(None)
            try:
                callable, args, kwargs = self.queue.get()
                log.info('calling %s with args %s and kwargs %s' % (callable, args, kwargs))
                callable(*args, **kwargs)
            except (Queue.Empty, TypeError), e:
                #print e
                log.info('All Queue Processed')
                processing = False

if __name__ == '__main__':
    def pprint(n, f=None):
        print n, f

    q = ProcessQueue()
    for n in range(5):
        q.add(pprint, n, f='Foo')
        q.add(pprint, n, f=None)

    q.process_queue()


