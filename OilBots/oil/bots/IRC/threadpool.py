# -*- coding: utf-8 -*-
'''
Yet another thread pool module.

A thread pool consists of a set of worker threads for performing time consuming
operations concurrently. A minimal API provides a way to submit jobs (requests),
without waiting for them to finish, and get the results back in some way once
they are available. The thread pool is responsible for assigning jobs to the
worker threads by putting them in a job queue, where they are picked up by the
next available worker. The worker then performs the assigned job in the background
and puts the processed request in an output queue.

The main novelty of this module compared to other threadpool recipes is the way
results are returned to the client. Instead of providing a callback to post-process
the computed results, a L{generator <ThreadPool.iterProcessedJobs>} is used for
popping the processed jobs from the output queue and yielding them back to the
caller. The processed jobs encapsulate the computed result (or raised exception)
and can be used transparently by the calling thread, as if the computation didn't
take place in a different thread. This is more flexible that the callback-based
approach since it gives full control to the caller of when to ask for a result,
how long to wait for it and what to do with it once it is fetched.

After a C{JobRequest} is L{added <ThreadPool.addJob>} to a L{ThreadPool}, it can
be in one of the following states:
    1. Unassigned: The request is still in the input queue, no worker thread
    has been assigned to it yet. There are two substates:
        - Pending: The job is waiting its turn to be picked up by a L{Worker}.
        - Cancelled: The job has been L{cancelled <ThreadPool.cancelJob>} and,
          although it still occupies a slot in the input queue, it will be
          discarded when a L{Worker} picks it up.
    2. In progress: The job has been popped by the input queue by a L{Worker} and
       is in the process of being executed.
    3. Processed: The job has been processed (successfully or not) and has been
       added to the output queue, ready to be returned.
    4. Returned: The job has been returned to the client, either by
       L{ThreadPool.iterProcessedJobs} or L{ThreadPool.processedJobs} and is no
       longer associated with the threadpool.
A job in state 1.a, 2 or 3 is said to be I{active}.

B{Acknowledgements:} The basic concept and the initial implementation was taken
from the U{threadpool module of Christopher Arndt
<http://www.chrisarndt.de/en/software/python/threadpool/>}, who in turn borrowed
from the "Python in a Nutshell" book by Alex Martelli.
'''

__all__ = ['ThreadPool', 'JobRequest']
__author__ = 'George Sakkis'

import sys
import time
import Queue
import logging
import threading
from decorator import decorator

_log = logging.getLogger(__name__)
log = _log


def synchronized(f):
    '''A synchronized method decorator'''
    def wrapper(self, *args, **kwargs):
        try: lock = self.__lock
        except AttributeError: # first time use
            lock = self.__dict__.setdefault('__lock', threading.RLock())
        lock.acquire()
        try: return f(self, *args, **kwargs)
        finally: lock.release()
    return wrapper

def queue1(f, pool=None):
    print 'in queue decoraator'
    def wrapper(self, *args, **kwargs):
        print 'in queue decoraator wrapper'
        print 12345, hasattr
        if pool:
            return pool.add_task(lambda: func(self, *args, **kwargs))
        return func(self, *args, **kwargs)
    return wrapper

def queue2(func):
    print 'in queue decoraator'
    def wrapper(func, self, *args, **kwargs):
        for attr, val in func.__dict__.iteritems():
            print 12345, attr, val
        return func(self, *args, **kwargs)
    return decorator(wrapper)

@decorator
def queue(func, *args, **kwargs):
    #print 'in queue decoraator'
#    print 'func.__dict__', func.__dict__
#    print 'func.__class__', func.__class__
#    print 'func.__class__.__name__', func.__class__.__name__
#    print 'func.__class__.__dict__', func.__class__.__dict__
#    print 'func.__class__.__dict__["__module__"]', func.__class__.__dict__['__module__']
#    print locals()
#    print args
#    print args[0].__dict__
    if hasattr(args[0], 'pool'):
        return args[0].pool.add_task(lambda: func(*args, **kwargs))
    return func(*args, **kwargs)

class ThreadPool(object):
    '''A thread pool, distributing job requests and collecting them after they
    are processed.

    See the module doctring for more information.
    '''

    def __init__(self, num_workers, input_queue_size=0, output_queue_size=0):
        '''Set up the thread pool and start C{num_workers} worker threads.

        @param num_workers: The number of worker threads to start initially.
        @param input_queue_size: If a positive integer, it's the maximum number
            of unassigned jobs. The thread pool blocks when the queue is full a
            new job is submitted.
        @param output_queue_size: If a positive integer, it's the maximum number
            of completed jobs waiting to be fetched. The thread pool blocks when
            the queue is full and a job is completed.
        '''
        self._workers = []
        self._activeKey2Job = {}
        self._unassignedKey2Job = {}
        self._unassignedJobs = Queue.Queue(input_queue_size)
        self._processedJobs = Queue.Queue(output_queue_size)
        self.addWorkers(num_workers)

    @synchronized
    def addWorkers(self, n=1):
        '''Add C{n} worker threads to the pool.'''
        for _ in xrange(n):
            self._workers.append(Worker(self._unassignedJobs, self._processedJobs,
                                        self._unassignedKey2Job))
        _log.debug('Added %d workers' % n)

    @synchronized
    def dismissWorkers(self, n=1):
        'Tell C{n} worker threads to quit after they finish with their current job.'
        for _ in xrange(n):
            try: self._workers.pop().dismissed = True
            except KeyError: break

    @synchronized
    def addJob(self, job, timeout=None):
        '''Add a job request to the end of the input queue.

        @param timeout: If the input queue is full and C{timeout is None}, block
            until a slot becomes available. If C{timeout > 0}, block for up to
            C{timeout} seconds and raise C{Queue.Full} exception if the queue is
            still full. If C{timeout <= 0}, do not block and raise C{Queue.Full}
            immediately if the queue is full.
        '''
        key = job.key
        self._unassignedJobs.put(job, timeout is None or timeout>0, timeout)
        self._unassignedKey2Job[key] = self._activeKey2Job[key] = job
        _log.debug('Added job %r to the input queue' % key)

    @synchronized
    def cancelJob(self, key):
        '''Cancel a job.

        This has effect only if the job is still unassigned; if it's in progress
        or has already been processed, it has no effect.

        @param key: The job's identifier.
        '''
        try:
            del self._unassignedKey2Job[key]
            # if it's not in unassigned, it may be in progress or already
            # processed; don't try to delete it from active
            del self._activeKey2Job[key]
        except KeyError: pass

    @synchronized
    def cancelAllJobs(self):
        '''Cancel all unassigned jobs.'''
        while self._unassignedKey2Job:
            del self._activeKey2Job[self._unassignedKey2Job.popitem()[0]]

    def numActiveJobs(self):
        '''Return the approximate number of active jobs.

        This is not reliable due to thread semantics.
        '''
        return len(self._activeKey2Job)

    def iterProcessedJobs(self, timeout=None):
        '''Return an iterator over processed job requests, popping them off the
        output queue.

        @param timeout: There are three cases:
            - If C{None}, iterate over the processed jobs as long as there are
            any active jobs. Whenever there are no processed jobs available,
            block and wait for a job to finish.
            - If C{<= 0}, iterate over the currently processed jobs only; do not
            block.
            - If C{> 0}, wait up to C{timeout} seconds per processed job as long
            as there are active jobs. Note that a loop such as::
                for r in t.iterProcessedJobs(2): pass
            may take from microseconds (if there are no active jobs) to
            arbitrarily long time, as long as each processed job is yielded
            within 2 seconds. If you want a timeout for the whole loop, use
            L{processedJobs} instead.
        '''
        block = timeout is None or timeout>0
        while self._activeKey2Job:
            try: job = self._processedJobs.get(block, timeout)
            except Queue.Empty:
                break
            key = job.key
            _log.debug('Popped job %r from the output queue' % key)
            # at this point the key is guaranteed to be in _activeKey2Job even
            # if the job has been cancelled
            assert key in self._activeKey2Job
            del self._activeKey2Job[key]
            yield job

    def processedJobs(self, timeout=None):
        '''Return a list of processed job requests.

        @param timeout: If C{timeout is None} or C{timeout <= 0}, it is
            equivalent to C{list(t.iterProcessedJobs(timeout))}. If C{timeout > 0},
            this is the maximum overall time to spend on collecting processed jobs.
        '''
        if timeout is None or timeout <= 0:
            return list(self.iterProcessedJobs(timeout))
        now = time.time
        end = now() + timeout
        processed = []
        while timeout > 0:
            try: processed.append(self.iterProcessedJobs(timeout).next())
            except StopIteration: break
            timeout = end - now()
        return processed


class JobRequest(object):
    '''A request to execute a callable later and encapsulate its result or
    exception info.
    '''

    class UnprocessedRequestError(Exception):
        '''The callable of a L{JobRequest} has not been called yet.'''

    def __init__(self, callable, args=(), kwds=None, key=None):
        '''Create a job request for a callable.

        A job request consists of the a callable to be executed by a L{worker
        thread <Worker>}, a list of positional arguments and a dictionary of
        keyword arguments.

        @param key: If given, it must be hashable to be used as identifier of
            the request. It defaults to C{id(self)}.
        '''
        if kwds is None: kwds = {}
        if key is None: key = id(self)
        for attr in 'callable', 'args', 'kwds', 'key':
            setattr(self, attr, eval(attr))
        self._exc_info = None

    def process(self):
        '''Execute the callable of this request with the given arguments and
        store the result or the raised exception info.
        '''
        _log.debug('Ready to process job request %r' % self.key)
        try:
            self._result = self.callable(*self.args, **self.kwds)
        except:
            self._exc_info = sys.exc_info()
            _log.info('Failed to process job request %r' % self.key)
        else:
            self._exc_info = None
            _log.debug('Job request %r was processed successfully' % self.key)

    def result(self):
        '''Return the computed result for this processed request.

        If the callable had risen an exception, it is reraised here with its
        original traceback.

        @raise JobRequest.UnprocessedRequestError: If L{process} has not been
            called for this request.
        '''
        if self._exc_info is not None:
            tp,exception,trace = self._exc_info
            raise tp,exception,trace
        try: return self._result
        except AttributeError:
            raise self.UnprocessedRequestError


class Worker(threading.Thread):
    '''Background thread connected to the input/output job request queues.

    A worker thread sits in the background and picks up job requests from one
    queue and puts the processed requests in another, until it is dismissed.
    '''

    def __init__(self, inputQueue, outputQueue, unassignedKey2Job, **kwds):
        '''Set up thread in daemonic mode and start it immediatedly.

        @param inputQueue, outputQueue: U{Queues
        <http://docs.python.org/lib/module-Queue.html>} passed by the L{ThreadPool}
        class when it creates a new worker thread.
        '''
        super(Worker,self).__init__(**kwds)
        self.setDaemon(True)
        self._inputQueue = inputQueue
        self._outputQueue = outputQueue
        self._unassignedKey2Job = unassignedKey2Job
        self.dismissed = False
        self.start()

    def run(self):
        '''Poll the input job queue indefinitely or until told to exit.

        Once a job request has been popped from the input queue, process it and
        add it to the output queue if it's not cancelled, otherwise discard it.
        '''
        while True:
            # thread blocks here if inputQueue is empty
            job = self._inputQueue.get()
            key = job.key
            _log.debug('Popped job request %r from the input queue' % key)
            try: del self._unassignedKey2Job[key]
            except KeyError:
                #_log.info('Discarded cancelled job request %r' % key)
                _log.debug('Discarded cancelled job request %r' % key)
                continue
            if self.dismissed: # put back the job we just picked up and exit
                self._inputQueue.put(job)
                _log.debug('Dismissing worker %r' % self.getName())
                break
            job.process()
            # thread blocks here if outputQueue is full
            self._outputQueue.put(job)
            _log.debug('Added job request %r to the output queue' % job.key)


import thread
from itertools import count
try:
    from paste.util import killthread
except ImportError:
    # Not available, probably no ctypes
    killthread = None
import atexit
import traceback

class PasteThreadPool(object):
    """
    Generic thread pool with a queue of callables to consume.

    Keeps a notion of the status of its worker threads:

    idle: worker thread with nothing to do

    busy: worker thread doing its job

    hung: worker thread that's been doing a job for too long

    dying: a hung thread that has been killed, but hasn't died quite
    yet.

    zombie: what was a worker thread that we've tried to kill but
    isn't dead yet.

    At any time you can call track_threads, to get a dictionary with
    these keys and lists of thread_ids that fall in that status.  All
    keys will be present, even if they point to emty lists.

    hung threads are threads that have been busy more than
    hung_thread_limit seconds.  Hung threads are killed when they live
    longer than kill_thread_limit seconds.  A thread is then
    considered dying for dying_limit seconds, if it is still alive
    after that it is considered a zombie.

    When there are no idle workers and a request comes in, another
    worker *may* be spawned.  If there are less than spawn_if_under
    threads in the busy state, another thread will be spawned.  So if
    the limit is 5, and there are 4 hung threads and 6 busy threads,
    no thread will be spawned.

    When there are more than max_zombie_threads_before_die zombie
    threads, a SystemExit exception will be raised, stopping the
    server.  Use 0 or None to never raise this exception.  Zombie
    threads *should* get cleaned up, but killing threads is no
    necessarily reliable.  This is turned off by default, since it is
    only a good idea if you've deployed the server with some process
    watching from above (something similar to daemontools or zdaemon).

    Each worker thread only processes ``max_requests`` tasks before it
    dies and replaces itself with a new worker thread.
    """


    SHUTDOWN = object()

    def __init__(
        self, nworkers, name="PasteThreadPool", daemon=False,
        max_requests=100, # threads are killed after this many requests
        hung_thread_limit=30, # when a thread is marked "hung"
        kill_thread_limit=1800, # when you kill that hung thread
        dying_limit=300, # seconds that a kill should take to go into effect (longer than this and the thread is a "zombie")
        spawn_if_under=5, # spawn if there's too many hung threads
        max_zombie_threads_before_die=0, # when to give up on the process
        hung_check_period=100, # every 100 requests check for hung workers
        logger=None, # Place to log messages to
        error_email=None, # Person(s) to notify if serious problem occurs
        ):
        """
        Create thread pool with `nworkers` worker threads.
        """
        self.nworkers = nworkers
        self.max_requests = max_requests
        self.name = name
        self.queue = Queue.Queue()
        self.workers = []
        self.daemon = daemon
        if logger is None:
#            logger = logging.getLogger('paste.httpserver.PasteThreadPool')
            logger = logging.getLogger(__name__)
        if isinstance(logger, basestring):
            logger = logging.getLogger(logger)
        self.logger = logger
        self.error_email = error_email
        self._worker_count = count()

        assert (not kill_thread_limit
                or kill_thread_limit >= hung_thread_limit), (
            "kill_thread_limit (%s) should be higher than hung_thread_limit (%s)"
            % (kill_thread_limit, hung_thread_limit))
        if not killthread:
            kill_thread_limit = 0
            self.logger.info(
                "Cannot use kill_thread_limit as ctypes/killthread is not available")
        self.kill_thread_limit = kill_thread_limit
        self.dying_limit = dying_limit
        self.hung_thread_limit = hung_thread_limit
        assert spawn_if_under <= nworkers, (
            "spawn_if_under (%s) should be less than nworkers (%s)"
            % (spawn_if_under, nworkers))
        self.spawn_if_under = spawn_if_under
        self.max_zombie_threads_before_die = max_zombie_threads_before_die
        self.hung_check_period = hung_check_period
        self.requests_since_last_hung_check = 0
        # Used to keep track of what worker is doing what:
        self.worker_tracker = {}
        # Used to keep track of the workers not doing anything:
        self.idle_workers = []
        # Used to keep track of threads that have been killed, but maybe aren't dead yet:
        self.dying_threads = {}
        # This is used to track when we last had to add idle workers;
        # we shouldn't cull extra workers until some time has passed
        # (hung_thread_limit) since workers were added:
        self._last_added_new_idle_workers = 0
        if not daemon:
            atexit.register(self.shutdown)
        for i in range(self.nworkers):
            self.add_worker_thread(message='Initial worker pool')

    def add_task(self, task):
        """
        Add a task to the queue
        """
        self.logger.debug('Added task (%i tasks queued)', self.queue.qsize())
        if self.hung_check_period:
            self.requests_since_last_hung_check += 1
            if self.requests_since_last_hung_check > self.hung_check_period:
                self.requests_since_last_hung_check = 0
                self.kill_hung_threads()
        if not self.idle_workers and self.spawn_if_under:
            # spawn_if_under can come into effect...
            busy = 0
            now = time.time()
            self.logger.debug('No idle workers for task; checking if we need to make more workers')
            for worker in self.workers:
                if not hasattr(worker, 'thread_id'):
                    # Not initialized
                    continue
                time_started, info = self.worker_tracker.get(worker.thread_id,
                                                             (None, None))
                if time_started is not None:
                    if now - time_started < self.hung_thread_limit:
                        busy += 1
            if busy < self.spawn_if_under:
                self.logger.info(
                    'No idle tasks, and only %s busy tasks; adding %s more '
                    'workers', busy, self.spawn_if_under-busy)
                self._last_added_new_idle_workers = time.time()
                for i in range(self.spawn_if_under - busy):
                    self.add_worker_thread(message='Response to lack of idle workers')
            else:
                self.logger.debug(
                    'No extra workers needed (%s busy workers)',
                    busy)
        if (len(self.workers) > self.nworkers
            and len(self.idle_workers) > 3
            and time.time()-self._last_added_new_idle_workers > self.hung_thread_limit):
            # We've spawned worers in the past, but they aren't needed
            # anymore; kill off some
            self.logger.info(
                'Culling %s extra workers (%s idle workers present)',
                len(self.workers)-self.nworkers, len(self.idle_workers))
            self.logger.debug(
                'Idle workers: %s', self.idle_workers)
            for i in range(len(self.workers) - self.nworkers):
                self.queue.put(self.SHUTDOWN)
        self.queue.put(task)

    def track_threads(self):
        """
        Return a dict summarizing the threads in the pool (as
        described in the PasteThreadPool docstring).
        """
        result = dict(idle=[], busy=[], hung=[], dying=[], zombie=[])
        now = time.time()
        for worker in self.workers:
            if not hasattr(worker, 'thread_id'):
                # The worker hasn't fully started up, we should just
                # ignore it
                continue
            time_started, info = self.worker_tracker.get(worker.thread_id,
                                                         (None, None))
            if time_started is not None:
                if now - time_started > self.hung_thread_limit:
                    result['hung'].append(worker)
                else:
                    result['busy'].append(worker)
            else:
                result['idle'].append(worker)
        for thread_id, (time_killed, worker) in self.dying_threads.items():
            if not self.thread_exists(thread_id):
                # Cull dying threads that are actually dead and gone
                self.logger.info('Killed thread %s no longer around',
                                 thread_id)
                try:
                    del self.dying_threads[thread_id]
                except KeyError:
                    pass
                continue
            if now - time_killed > self.dying_limit:
                result['zombie'].append(worker)
            else:
                result['dying'].append(worker)
        return result

    def kill_worker(self, thread_id):
        """
        Removes the worker with the given thread_id from the pool, and
        replaces it with a new worker thread.

        This should only be done for mis-behaving workers.
        """
        if killthread is None:
            raise RuntimeError(
                "Cannot kill worker; killthread/ctypes not available")
        thread_obj = threading._active.get(thread_id)
        killthread.async_raise(thread_id, SystemExit)
        try:
            del self.worker_tracker[thread_id]
        except KeyError:
            pass
        self.logger.info('Killing thread %s', thread_id)
        if thread_obj in self.workers:
            self.workers.remove(thread_obj)
        self.dying_threads[thread_id] = (time.time(), thread_obj)
        self.add_worker_thread(message='Replacement for killed thread %s' % thread_id)

    def thread_exists(self, thread_id):
        """
        Returns true if a thread with this id is still running
        """
        return thread_id in threading._active

    def add_worker_thread(self, *args, **kwargs):
        index = self._worker_count.next()
        worker = threading.Thread(target=self.worker_thread_callback,
                                  args=args, kwargs=kwargs,
                                  name=("worker %d" % index))
        worker.setDaemon(self.daemon)
        worker.start()

    def kill_hung_threads(self):
        """
        Tries to kill any hung threads
        """
        if not self.kill_thread_limit:
            # No killing should occur
            return
        now = time.time()
        max_time = 0
        total_time = 0
        idle_workers = 0
        starting_workers = 0
        working_workers = 0
        killed_workers = 0
        for worker in self.workers:
            if not hasattr(worker, 'thread_id'):
                # Not setup yet
                starting_workers += 1
                continue
            time_started, info = self.worker_tracker.get(worker.thread_id,
                                                         (None, None))
            if time_started is None:
                # Must be idle
                idle_workers += 1
                continue
            working_workers += 1
            max_time = max(max_time, now-time_started)
            total_time += now-time_started
            if now - time_started > self.kill_thread_limit:
                self.logger.warning(
                    'Thread %s hung (working on task for %i seconds)',
                    worker.thread_id, now - time_started)
                try:
                    import pprint
                    info_desc = pprint.pformat(info)
                except:
                    out = StringIO()
                    traceback.print_exc(file=out)
                    info_desc = 'Error:\n%s' % out.getvalue()
                self.notify_problem(
                    "Killing worker thread (id=%(thread_id)s) because it has been \n"
                    "working on task for %(time)s seconds (limit is %(limit)s)\n"
                    "Info on task:\n"
                    "%(info)s"
                    % dict(thread_id=worker.thread_id,
                           time=now - time_started,
                           limit=self.kill_thread_limit,
                           info=info_desc))
                self.kill_worker(worker.thread_id)
                killed_workers += 1
        if working_workers:
            ave_time = float(total_time) / working_workers
            ave_time = '%.2fsec' % ave_time
        else:
            ave_time = 'N/A'
        self.logger.info(
            "kill_hung_threads status: %s threads (%s working, %s idle, %s starting) "
            "ave time %s, max time %.2fsec, killed %s workers"
            % (idle_workers + starting_workers + working_workers,
               working_workers, idle_workers, starting_workers,
               ave_time, max_time, killed_workers))
        self.check_max_zombies()

    def check_max_zombies(self):
        """
        Check if we've reached max_zombie_threads_before_die; if so
        then kill the entire process.
        """
        if not self.max_zombie_threads_before_die:
            return
        found = []
        now = time.time()
        for thread_id, (time_killed, worker) in self.dying_threads.items():
            if not self.thread_exists(thread_id):
                # Cull dying threads that are actually dead and gone
                try:
                    del self.dying_threads[thread_id]
                except KeyError:
                    pass
                continue
            if now - time_killed > self.dying_limit:
                found.append(thread_id)
        if found:
            self.logger.info('Found %s zombie threads', found)
        if len(found) > self.max_zombie_threads_before_die:
            self.logger.fatal(
                'Exiting process because %s zombie threads is more than %s limit',
                len(found), self.max_zombie_threads_before_die)
            self.notify_problem(
                "Exiting process because %(found)s zombie threads "
                "(more than limit of %(limit)s)\n"
                "Bad threads (ids):\n"
                "  %(ids)s\n"
                % dict(found=len(found),
                       limit=self.max_zombie_threads_before_die,
                       ids="\n  ".join(map(str, found))),
                subject="Process restart (too many zombie threads)")
            self.shutdown(10)
            print 'Shutting down', threading.currentThread()
            raise ServerExit(3)

    def worker_thread_callback(self, message=None):
        """
        Worker thread should call this method to get and process queued
        callables.
        """
        thread_obj = threading.currentThread()
        thread_id = thread_obj.thread_id = thread.get_ident()
        self.workers.append(thread_obj)
        self.idle_workers.append(thread_id)
        requests_processed = 0
        add_replacement_worker = False
        self.logger.debug('Started new worker %s: %s', thread_id, message)
        try:
            while True:
                if self.max_requests and self.max_requests < requests_processed:
                    # Replace this thread then die
                    self.logger.debug('Thread %s processed %i requests (limit %s); stopping thread'
                                      % (thread_id, requests_processed, self.max_requests))
                    add_replacement_worker = True
                    break
                runnable = self.queue.get()
                if runnable is PasteThreadPool.SHUTDOWN:
                    self.logger.debug('Worker %s asked to SHUTDOWN', thread_id)
                    break
                try:
                    self.idle_workers.remove(thread_id)
                except ValueError:
                    pass
                self.worker_tracker[thread_id] = [time.time(), None]
                requests_processed += 1
                try:
                    try:
                        runnable()
                    except:
                        # We are later going to call sys.exc_clear(),
                        # removing all remnants of any exception, so
                        # we should log it now.  But ideally no
                        # exception should reach this level
                        print >> sys.stderr, (
                            'Unexpected exception in worker %r' % runnable)
                        traceback.print_exc()
                    if thread_id in self.dying_threads:
                        # That last exception was intended to kill me
                        break
                finally:
                    try:
                        del self.worker_tracker[thread_id]
                    except KeyError:
                        pass
                    sys.exc_clear()
                self.idle_workers.append(thread_id)
        finally:
            try:
                del self.worker_tracker[thread_id]
            except KeyError:
                pass
            try:
                self.idle_workers.remove(thread_id)
            except ValueError:
                pass
            try:
                self.workers.remove(thread_obj)
            except ValueError:
                pass
            try:
                del self.dying_threads[thread_id]
            except KeyError:
                pass
            if add_replacement_worker:
                self.add_worker_thread(message='Voluntary replacement for thread %s' % thread_id)

    def shutdown(self, force_quit_timeout=0):
        """
        Shutdown the queue (after finishing any pending requests).
        """
        self.logger.info('Shutting down threadpool')
        # Add a shutdown request for every worker
        for i in range(len(self.workers)):
            self.queue.put(PasteThreadPool.SHUTDOWN)
        # Wait for each thread to terminate
        hung_workers = []
        for worker in self.workers:
            worker.join(0.5)
            if worker.isAlive():
                hung_workers.append(worker)
        zombies = []
        for thread_id in self.dying_threads:
            if self.thread_exists(thread_id):
                zombies.append(thread_id)
        if hung_workers or zombies:
            self.logger.info("%s workers didn't stop properly, and %s zombies",
                             len(hung_workers), len(zombies))
            if hung_workers:
                for worker in hung_workers:
                    self.kill_worker(worker.thread_id)
                self.logger.info('Workers killed forcefully')
            if force_quit_timeout:
                hung = []
                timed_out = False
                need_force_quit = bool(zombies)
                for workers in self.workers:
                    if not timed_out and worker.isAlive():
                        timed_out = True
                        worker.join(force_quit_timeout)
                    if worker.isAlive():
                        print "Worker %s won't die" % worker
                        need_force_quit = True
                if need_force_quit:
                    import atexit
                    # Remove the threading atexit callback
                    for callback in list(atexit._exithandlers):
                        func = getattr(callback[0], 'im_func', None)
                        if not func:
                            continue
                        globs = getattr(func, 'func_globals', {})
                        mod = globs.get('__name__')
                        if mod == 'threading':
                            atexit._exithandlers.remove(callback)
                    atexit._run_exitfuncs()
                    print 'Forcefully exiting process'
                    os._exit(3)
                else:
                    self.logger.info('All workers eventually killed')
        else:
            self.logger.info('All workers stopped')

    def notify_problem(self, msg, subject=None, spawn_thread=True):
        """
        Called when there's a substantial problem.  msg contains the
        body of the notification, subject the summary.

        If spawn_thread is true, then the email will be send in
        another thread (so this doesn't block).
        """
        if not self.error_email:
            return
        if spawn_thread:
            t = threading.Thread(
                target=self.notify_problem,
                args=(msg, subject, False))
            t.start()
            return
        from_address = 'errors@localhost'
        if not subject:
            subject = msg.strip().splitlines()[0]
            subject = subject[:50]
            subject = '[http threadpool] %s' % subject
        headers = [
            "To: %s" % self.error_email,
            "From: %s" % from_address,
            "Subject: %s" % subject,
            ]
        try:
            system = ' '.join(os.uname())
        except:
            system = '(unknown)'
        body = (
            "An error has occurred in the paste.httpserver.PasteThreadPool\n"
            "Error:\n"
            "  %(msg)s\n"
            "Occurred at: %(time)s\n"
            "PID: %(pid)s\n"
            "System: %(system)s\n"
            "Server .py file: %(file)s\n"
            % dict(msg=msg,
                   time=time.strftime("%c"),
                   pid=os.getpid(),
                   system=system,
                   file=os.path.abspath(__file__),
                   ))
        message = '\n'.join(headers) + "\n\n" + body
        import smtplib
        server = smtplib.SMTP('localhost')
        error_emails = [
            e.strip() for e in self.error_email.split(",")
            if e.strip()]
        server.sendmail(from_address, error_emails, message)
        server.quit()
        print 'email sent to', error_emails, message


if __name__ == '__main__':
    def pprint(n, f=None):
        print n, f
    p = PasteThreadPool(5)
    for n in range(6):
        p.add_task(lambda: pprint(n))
        p.add_task(lambda: pprint(n, f=n))
    import sys
    sys.exit()