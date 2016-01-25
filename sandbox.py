import save_tables
import xml.etree.ElementTree as ET
import csv


csv_file = "DOE grant short list.csv"
ns = "{http://scientific.thomsonreuters.com/schema/wok5.4/public/FullRecord}"

save_tables.print_pub_table(csv_file, ns)
save_tables.print_grant_table(csv_file, ns)

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
#
