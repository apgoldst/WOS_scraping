import save_tables
import submit_search
import wok_soap
import xml.etree.ElementTree as ET
import csv


csv_file = "DOE grant short list.csv"
ns = "{http://scientific.thomsonreuters.com/schema/wok5.4/public/FullRecord}"

# Save tables of data per publication and per grant
# save_tables.print_pub_table(csv_file)
# save_tables.print_grant_table(csv_file)
# save_tables.print_cited_refs_table(csv_file)


# data = []
# data.append({"__paper list": []})
# data.append({"__paper list": [1,2,3,4]})
# print data
# print data[1]["__paper list"][0]
#
# for grant in data:
#     example_paper = grant["__paper list"]
#     print example_paper
#     if example_paper:
#         break
#
# print "example_paper is " + str(example_paper)



# SID = wok_soap.auth()
# print SID
#
# UID = "WOS:000346178800058"
# results = wok_soap.citedReferences(UID, SID)
# print results

# # Test XML parsing for first record in a file of search results
# filename = "grant search results - full html/FT = AR0000007 OR FT = AR 0000007.txt"
# with open(filename, "r+") as f:
#     tree = ET.parse(f)
# root = tree.getroot()
# record = root[0]
# static_data = record[1]
# summary = static_data[0]
# fullrecord_metadata = static_data[1]
# item = static_data[2]
# dynamic_data = record[2]

# query = "FT = SC0000957 OR FT = SC 0000957"
# SID = wok_soap.auth()
# print SID
# SID = "1WEwqdk8PcphC1aOTiI"
# #
# search_result = wok_soap.search(query,SID)
# queryId = search_result[0]
# records_found = search_result[1]
# results_list = search_result[3]
# print len(results_list)
#
# print str(records_found) + " records found"
# with open("search result.txt", "wb") as f:
#     f.write(str(search_result))

# retrieve_result = wok_soap.retrieve(queryId,SID,start_count=101)
# with open("retrieve result.txt", "wb") as f:
#     f.write(str(retrieve_result))
# #
# # paper with 157 references
# UID = "WOS:000275858200003"

# cited_refs_result = wok_soap.citedReferences(UID,SID)
# queryId = cited_refs_result[0]
# with open("cited refs result.txt", "wb") as f:
#     f.write(str(cited_refs_result))
#
# cited_refs_retrieve_result = wok_soap.citedReferencesRetrieve(queryId,SID,start_count=101)
# with open("cited refs retrieve result.txt", "wb") as f:
#     f.write(str(cited_refs_retrieve_result))
# print type(cited_refs_retrieve_result)
# print dir(cited_refs_retrieve_result)
# print type(cited_refs_retrieve_result[0])
# print dir(cited_refs_retrieve_result[0])
# print cited_refs_retrieve_result[0].year

# print "results[1][0] = " + str(results[1][0]) # first cited ref
# print "results[1][0][0] = " + str(results[1][0][0]) # docid
# print dir(results[1][0])
# print results[1][0].citedWork

# UID = "000341217500093"
# results = wok_soap.retrieveById(UID, SID)
# print results[3]
# tree = ET.fromstring(results[3])
# refs = tree.find(".//" + ns + "refs")
# ref_count = refs.attrib['count']
# submit_search.search_for_cited_refs(UID, SID, ref_count)

# submit_search.search_for_cited_refs(UID,SID)
# submit_search.search_by_grant("FT = AR0000007 OR FT = AR 0000007.csv", SID)