import io
import sys
import requests
import lxml.etree
import lxml.html
from subprocess import Popen, PIPE
import json
import hashlib
import praw
import AccountDetails

LOCATION = "stadtmitte"

PrawInterface = praw.Reddit(user_agent='Mensa Speisekarte Poster by /u/ysangkok')
PrawInterface.login(AccountDetails.USERNAME, AccountDetails.PASSWORD)


def w3mrender(htmltext):
    cmd = ["w3m", "-dump", "-T", "text/html"]
    stdout, stderr = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE).communicate(htmltext)
    return stdout


def et_to_bytes(j):
    c = io.BytesIO()
    lxml.etree.ElementTree(j).write(c)
    return c.getvalue()

URLPREFIX = "http://www.studierendenwerkdarmstadt.de/index.php/de/essen-und-trinken/speisekarten/"
text = requests.get(URLPREFIX + LOCATION).text

m = hashlib.sha256()
m.update(text.encode())
pghash = m.hexdigest()

ET = lxml.html.document_fromstring(text)

xp = ET.xpath(".//*[@class='spk_table']")
date = "".join(ET.xpath(".//*[@class='spk_table']//th/text()")).strip()
print(date)

for j in xp:
    sys.stdout.buffer.write(w3mrender(et_to_bytes(j)))
    sys.stdout.buffer.flush()

with open("alreadyposted.json") as f:
    alreadyposted = set(json.loads(f.read()))

xp = ET.xpath(".//*[@class='spk_table']//td[2]/text()")
for j in xp:
    gerichtId = "{}: {}".format(date, j).strip()
    if gerichtId in alreadyposted:
        print("skipping gericht {}, it was already posted".format(gerichtId))

    SubmitResult = PrawInterface.submit(LOCATION, gerichtId, text="page hash {}".format(pghash))
    PostURL = SubmitResult.url

    alreadyposted.add(gerichtId)

with open("alreadyposted.json", "w") as f:
    f.write(json.dumps(list(alreadyposted)))
