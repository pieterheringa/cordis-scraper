cordis-scraper
==============

This project has been developed to download data from cordis.europa.eu and
to give some aggregation functions in order to perform some kind of analysis.

More specifically, the following scripts are available:

down.py
-------

This script is used to download data from the cordis website, creating a csv
file containing a row for each and every project funded.

To run it, just execute

    python down.py

The script uses redis to cache the website requests, and will take a bit
to run. For each project, it's storing the following information:

* Theme (e.g.: FP7-COORDINATION)
* Activities (research area) (e.g.: ERANET.2008.1 ERA-NET proposals of a horizontal nature)
* Project Acronym (e.g.: ERA-AGE 2)
* Start Date (e.g.: 2009-04-01)
* End Date (e.g.: 2012-09-30)
* Project Cost (e.g.: 190676)
* Project Funding (e.g.: 1699998)
* Project Status (e.g.: Execution)
* Contract Type (e.g.: Coordination (or networking) actions)
* Coordinator (e.g.: THE UNIVERSITY OF SHEFFIELD - COUNTRY: UNITED KINGDOM)
* Project Reference (e.g.: 235356)
* Record (e.g.: 92401)
* Partner 1 (e.g.: UNITATEA EXECUTIVA PENTRU FINANTAREA INVATAMANTULUI SUPERIOR, A CERCETARII, DEZVOLTARII SI INOVARII - COUNTRY: ROMANIA)
* Partner 2 (e.g.: SUOMEN AKATEMIA - COUNTRY: SUOMI/FINLAND	ISTITUTO SUPERIORE DI SANITA - COUNTRY: ITALIA)
* Partner 3 (e.g.: MINISTERIO DE CIENCIA E INNOVACION - COUNTRY: ESPAÑA)
* Partner 4 (e.g.: CENTER FOR POPULATION STUDIES - BULGARIAN ACADEMY OF SCIENCE - COUNTRY: BULGARIA)
* Parnter 5 (e.g.: MINISTRY OF HEALTH - COUNTRY: ISRAEL)
* Partner 6 (e.g.: FONDS NATIONAL DE LA RECHERCHE - COUNTRY: LUXEMBOURG (GRAND-DUCHÉ))
* Partner 7 (e.g.: FORSKINGSRADET FOR ARBETSLIV OCH SOCIALVETENSKAP - COUNTRY: SVERIGE)
* Partner 8 (e.g.: LATVIJAS ZINATNES PADOME - COUNTRY: LATVIJA)
* Partner 9 (e.g.: MINISTERUL SANATATII - COUNTRY: ROMANIA)
* Partner 10 (e.g.: OESTERREICHISCHE AKADEMIE DER WISSENSCHAFTEN - COUNTRY: ÖSTERREICH)
* Partner 11 (e.g.: CAISSE NATIONALE D'ASSURANCE VIEILLESSE - COUNTRY: FRANCE)
* Partner 12 ...

build_matrix.py
---------------
This script is used to aggregate the data extracted by down.py.

<more coming eventually>
