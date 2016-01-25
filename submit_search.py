# Author: Anna Goldstein
# This script runs a search on Web of Knowledge, using IP authentication.
# You must have an IP address from an institution with a WOK subscription.
#

import csv
import os
import wok_soap


def search_records(csv_file):
    SID = wok_soap.auth()

    with open(csv_file, "rb") as h:
        text = csv.reader(h)
        grant_list = [row[0] for row in text]

    file_list = []

    for i, cell in enumerate(grant_list):
        # Define query
        grant_number_full = cell
        prefix = grant_number_full[3:5]
        grant_number = grant_number_full[5:]
        query = "FT = " + prefix + grant_number + " OR FT = " + prefix + " " + grant_number
        # print query
        filename = "grant search results - full html/" + query + ".txt"
        file_list.append(filename)

        if not os.path.exists(filename):
            # Search on WOS
            # Only the first 100 records will be returned.
            # To get more than 100, you need to write a "retrieve" method into wok_soap.py
            results = wok_soap.search(query, SID)

            # Interpret raw search results stored in 4th line of object
            # results_string = str(results[3])
            results_unicode = results[3].encode('utf-8')
            # root = ET.fromstring(results_string)
            # print len(root)

            # Write raw search results to txt file
            with open(filename, "w") as f:
                # results_string = str(results[3])
                f.write(results_unicode)
                # f.write(results_string)

            # Alternate method of writing to file
            # f = os.open("results.txt", os.O_RDWR|os.O_CREAT)
            # results_string = str(results[3])
            # results_file = os.write(f, results_string)
            # os.close(f)

    return [grant_list, file_list]


csv_file = "DOE grant short list.csv"

if __name__ == '__main__':
    search_records(csv_file[:10])
