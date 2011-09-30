#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gevent import monkey #the best thing to do is put this import in manage.py
monkey.patch_socket()

import logging
import requests
import tablib
from BeautifulSoup import BeautifulSoup

import gevent
from gevent.queue import JoinableQueue, Queue

logging.basicConfig(level=logging.DEBUG)

NUM_THEME_WORKER_THREADS = 6
NUM_PROJECT_WORKER_THREADS = 50

THEME_URL = "http://cordis.europa.eu/fetch?CALLER=FP7_PROJ_EN&QM_EP_PGA_A=%(theme)s"

def theme_worker():
    def get_projects(doc):
        for result in doc.findAll(title=u"Project acronym"):
            a = result.a
            link = "http://cordis.europa.eu" + dict(a.attrs)['href'][2:]
            yield link

    logging.info('START THEME WORKER')
    while True:
        theme = q.get()
        logging.info('THEME: %s', repr(theme))

        url = THEME_URL % {'theme': theme}
        try:
            while True:
                r = requests.get(url)
                if r.status_code != 200:
                    logging.error("Request failed for url: %s", url)
                    continue
                doc = BeautifulSoup(r.content)
                for proj in get_projects(doc):
                    project_queue.put((theme, proj))
                try:
                    next_ = dict(doc.find(
                            text="Next 20 projects &raquo;").parent.attrs
                        )['href'][2:]
                except AttributeError:
                    break
                url = "http://cordis.europa.eu" + next_

        except:
            logging.error("THEME_WORKER: Error for url: %s", url)
        finally:
            q.task_done()


def project_worker():
    logging.info('START PROJECT WORKER')
    while True:
        item = project_queue.get()
        logging.info('PROJECT: %s', repr(item))
        try:
            # do_work(item)
            out_queue.put('out')
        finally:
            project_queue.task_done()


def get_themes():
    # http://cordis.europa.eu/fp7/projects_en.html
    r = requests.get('http://cordis.europa.eu/fp7/projects_en.html')
    assert r.status_code == 200, "Error retrieving themes"
    doc = BeautifulSoup(r.content)
    for option in doc.find(id="themes"):
        try:
            option = option.string.strip()
        except:
            continue
        if not option:
            continue
        yield option


def get_timestamp():
    """
    returns a string containg the timestamp (in seconds)
    """
    from datetime import datetime
    from time import mktime

    return str(mktime(datetime.utcnow().timetuple()))[:-2]


if __name__ == "__main__":
    q = JoinableQueue()
    project_queue = JoinableQueue()
    out_queue = Queue()

    for i in range(NUM_THEME_WORKER_THREADS):
         gevent.spawn(theme_worker)

    for i in range(NUM_PROJECT_WORKER_THREADS):
         gevent.spawn(project_worker)

    for item in get_themes():
        q.put(item)

    q.join()  # block until all tasks are done
    project_queue.join()
    out_queue.put(StopIteration)

    data = tablib.Dataset(headers=['First Name', 'Last Name', 'Age'])
    for i, out in enumerate(out_queue):
        logging.info('OUT: %d, %s', i, repr(out))
        data.append(out)

    with open('projects.%s.ods' % (get_timestamp(),), 'w') as f:
        f.write(data.ods)



