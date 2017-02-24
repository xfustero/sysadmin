#!/usr/bin/env python

from xml.etree.ElementTree import parse, tostring
import os, re

jobs_dir = "/var/lib/jenkins/jobs"
folder = "/TestFolder/"

# We go under jenkins' jobs directori and list all jobs
# For each one we check its config.xml file and log for 'template' tag under 'publisher' tag
# and we rename it adding the folder path we created in the XL-release server
dirs = [d for d in os.listdir(jobs_dir) if os.path.isdir(os.path.join(jobs_dir,d))]
print "\n"
print "Jobs listed below will be modified to have the publishers template name complaient with the new folder structure from XL-release 6\n"
for d in dirs:

  doc = parse(jobs_dir + "/" + d + "/config.xml")
  for p in doc.findall('publishers'): 
    elems = p.findall(".//template")
    for elem in elems:

      # We ensure it has not been already renamed to be idempotent
      pattern = re.compile(folder)
      if not pattern.match(elem.text):
      	elem.text = folder + elem.text
      	doc.write(jobs_dir + "/" + d + "/config.xml")
      	print "Job " + d + " modifying template=" + elem.text
      else:
        print "Job " + d + " has been already updated!"


