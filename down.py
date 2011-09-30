#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import namedtuple
from gevent import monkey #the best thing to do is put this import in manage.py
monkey.patch_socket()

import logging
import requests
from BeautifulSoup import BeautifulSoup

import gevent
from gevent.queue import JoinableQueue, Queue

logging.basicConfig(level=logging.DEBUG)

Person = namedtuple('Person', ['name', 'phone', 'fax'])
Project = namedtuple('Project', ['theme', 'activities', 'acronym',
                                 'name', 'start_date', 'end_date',
                                 'duration', 'cost', 'funding',
                                 'status', 'contract_type',
                                 'coordinator', 'partners',
                                 'contact_person', 'reference'])

NUM_THEME_WORKER_THREADS = 4
NUM_PROJECT_WORKER_THREADS = 10

def theme_worker():
    logging.info('START THEME WORKER')
    while True:
        item = q.get()
        logging.info('THEME: %s', repr(item))
        try:
            # do_work(item)
            project_queue.put('p')
        finally:
            q.task_done()


def project_worker():
    logging.info('START PROJECT WORKER')
    while True:
        theme, url = project_queue.get()
        logging.info('PROJECT: %s: %s' % (theme, url))
        r = requests.get(url)
        assert(r.ok)

        doc = BeautifulSoup(r.content)
        content = doc.find(id="textcontent")
        info = content.find(text="Project details").findParent("table").find(text="Project Acronym:").findParent("td")
        contact_info = content.find(text="Coordinator").findParent("table").find(text="Contact Person:").findParent("td")
        organization_info = content.find(text="Coordinator").findParent("table").find(text="Organisation:").findParent("td")

        contact_info_tokens = contact_info.text.split("<br />")
        contact_name = contact_info_tokens[0][contact_info_tokens[0].find("Name:")+5:].strip()
        contact_phone = contact_info_tokens[1][contact_info_tokens[1].find("Tel:")+5:].strip()
        contact_fax = contact_info_tokens[2][contact_info_tokens[2].find("fax:")+5:].strip()
        contact = Person(contact_name, contact_phone, contact_fax)

        activities = content.find(text="Research area:").parent.parent.getText()[len("Research area:"):].strip()
        name = content.find("h4").getText().strip()
        acronym = info.find(text="Project Acronym:").parent.nextSibling.strip()

        start_date = info.find(text="Start Date:").parent.nextSibling.strip()
        end_date = info.find(text="End Date:").parent.nextSibling.strip()
        duration = info.find(text="Duration:").parent.nextSibling.strip()
        cost = info.find(text="Project Cost:").parent.nextSibling.strip()
        funding = info.find(text="Project Funding:").parent.nextSibling.strip()
        status = info.find(text="Project Status:").parent.nextSibling.strip()
        contract_type = info.find(text="Contract Type:").parent.nextSibling.strip()
        coordinator = 'something'
        partners = ["a", "b"]
        reference = info.find(text="Project Reference:").parent.nextSibling.strip()

        project = Project(theme, activities, acronym, name, start_date,
                          end_date, duration, cost, funding,
                          status, contract_type, coordinator,
                          partners, contact, reference)

        try:
            out_queue.put(project)
        finally:
            project_queue.task_done()


def get_themes():
    # http://cordis.europa.eu/fp7/projects_en.html
    r = requests.get('ttp://cordihs.europa.eu/fp7/projects_en.html')
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

#    project_queue.put(("FP7-Coordination","http://cordis.europa.eu/fetch?CALLER=FP7_PROJ_EN&ACTION=D&DOC=2&CAT=PROJ&QUERY=0132b91a1d37:ca42:20734bc8&RCN=96249"))

    q.join()  # block until all tasks are done
    project_queue.join()
    out_queue.put(StopIteration)

    for out in out_queue:
        print out

