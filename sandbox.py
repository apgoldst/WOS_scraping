import save_tables
import submit_search
import wok_soap
import xml.etree.ElementTree as ET
import csv
import os
import time




#SID = wok_soap.auth()
#print(SID)

csv_file = "example DOIs.csv"
SID="8BIaALTznDdvcPRBWqF"

save_tables.print_pub_table_from_DOIs(csv_file)




#
#filename = "DOI search results xml/DO = 10.1002 9781118877517.ch7.txt"
#
## open search results file and parse as XML
#with open(filename) as h:
#    tree = ET.parse(h)
#    print(str(tree))
#    root = tree.getroot()
#    
#if root:
#    print(root[0])
#    
#    
#
#record = root[0]
#paper = save_tables.process_article(record)
#paper = save_tables.citation_analysis(paper, SID, counter)
