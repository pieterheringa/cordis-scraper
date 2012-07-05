html = """
<div>
<!-- Template mode: INFSO-->
<div class="projttl">
<img src="/projects/icons/logo-fp7.jpg" alt="FP7" class="logo-prog"/>
<h1>ITSY</h1>
<h2>IT[t] Simply Works</h2>
</div>
<div class="projdates">
<b>From</b> 2010-06-01 <b>to</b> 2011-05-31</div>
<div class="projdescr">
<div class="short">
<script type="text/JavaScript">abstract();</script>
</div>
<div class="full">
<div class="tech">
<h3>Objective</h3>
<p>The primary goal of the proposed effort is to generate a set of innovative research topics on the notion of simplicity as a driving paradigm in ICT development, maintenance and use. We believe that the philosophy of simplicity is strategically important, yet poorly understood, and rarely systematically applied. Instead, design principles attempt to focus on increased functionality within thinly disguised complexity, often at the expense of life cycle costs and total cost of ownership issues (e.g., training, system malfunctions, system upgrades). <br/><br/>Often designers are unaware of the tradeoffs and impacts. With the increased use of ICT in such socially critical areas such as healthcare, society can no longer afford systems that do not perform as specified. We believe that an understanding of simplicity is the key. Simplicity is foundational, its essence fundamental to many desired characteristics of ICT systems such as reliability, usability and trust. Thus, we believe that knowledge gained through research on simplicity can provide the EU a sustainable competitive advantage. To gain this knowledge we must ask the right questions, we must develop the proper research directions. To do so, the IT Simply Works team will organise a set of multidisciplinary experts to assist in surveying key research communities about their understandings and vision of the philosophy of simplicity. <br/><br/>Only through such a multidisciplinary approach can we hope to achieve a basic and yet thorough understanding of the important issues to be addressed. The results of this effort will be presented in a final report elaborating the vision of simplicity in ICT and proposing topics, initiatives and modalities for future-directed foundational research and its transformation for benefitting Europe's citizens, businesses, industry and governments.</p>
</div>
</div>
</div>
<div class="projdet">
<h2>Project details</h2>
<div class="box-left">
<b>Project reference</b>: 258058<br/>
<b>Status</b>: Completed<br/>
<br/>
<b>Total cost</b>: EUR 131 760<br/>
<b>EU contribution</b>: EUR 117 000<br/>
</div>
<div class="box-right">
<p>
<b>Programme acronym: </b>
<br/>
<a href="/fetch?CALLER=PROGLINK_NEWS_EN&amp;QF_PGA=FP7-ICT">FP7-ICT</a>
</p>
<p>
<b>Subprogramme area: </b>
<br/>ICT-2009.8.10 Identifying new research topics, Assessing emerging global S&amp;T trends in ICT for future FET Proactive initiatives</p>
<p>
<b>Contract type: </b>
<br/>Coordination and support actions</p>
</div>
</div>
<div class="projcoord" id="coord">
<h2>Coordinator</h2>
<div class="main">
<div class="name">UNIVERSITAET POTSDAM</div>
<div class="country">DEUTSCHLAND <a class="see-more" href="JavaScript:tglInfo('coord');">
<span>(+)</span>
</a>
</div>
</div>
<div class="optional item-content">Administrative contact: Regina GERBER (Dr)<br/>DEZERNAT 1<br/>AM NEUEN PALAIS 10, POTSDAM, DEUTSCHLAND<br/>
</div>
</div>
<div id="subjects">
<h2>Subjects</h2>COO - EVA - INF - ITT</div>
<div id="recinfo">
<b>Record number</b>: 95086 / <b>Last updated on (QVD)</b>: 2011-07-26</div>
<script type="text/JavaScript">SeeAlsoObj = {PGA: 'FP7-ICT',SIC: 'COO,EVA,INF,ITT',CCY: 'DE'};</script>
</div>
"""

from BeautifulSoup import BeautifulSoup
from down import _get_p_br_entry, convert_to_currency, extract_institution

content = BeautifulSoup(html, convertEntities="html", smartQuotesTo="html", fromEncoding="utf-8")

# extract useful chunks of content
data_info = content.find(attrs={'class':'projdates'})
data_coordinator = content.find(attrs={'class': 'projcoord'})
data_details = content.find(attrs={'class': 'projdet'})
data_participants = content.find(attrs={'class': 'participants'})
data_footer = content.find(attrs={'id': 'recinfo'})

# extract useful information about this project
print "ACTIVITY: %s" % _get_p_br_entry(data_details, "subprogramme area")
print "ACRONYM: %s" %  content.find('h1').text
if data_info:
    start_date = _get_p_br_entry(data_info, "from")
    end_date = _get_p_br_entry(data_info, "to")
else:
    start_date = ''
    end_date = ''

print "START DATE: %s" % start_date
print "END DATE: %s" % end_date
 
print "COST: %s" % convert_to_currency(_get_p_br_entry(data_details, "total cost"))
print "FUNDING: %s" % convert_to_currency(_get_p_br_entry(data_details, "EU contribution"))
print "STATUS: %s" % _get_p_br_entry(data_details, "status")
print "CONTRACT TYPE: %s" %  _get_p_br_entry(data_details, "contract type")
print "COORDINATOR: %s" %  extract_institution(data_coordinator)
print "CONTACT: %s" % _get_p_br_entry(data_coordinator, "administrative contact")
print "REFERENCE ##: %s" %  _get_p_br_entry(data_details, "project reference")
print "RECORD ##: %s" %  _get_p_br_entry(data_footer, "record number")

partners = []
if data_participants is not None:
    for participant in data_participants.findAll(attrs={'class': 'participant'}):
        print "PARTNER: %s" % extract_institution(participant)
