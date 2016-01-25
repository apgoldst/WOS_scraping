import save_tables

csv_file = "DOE grant numbers.csv"
ns = "{http://scientific.thomsonreuters.com/schema/wok5.4/public/FullRecord}"

save_tables.print_pub_table(csv_file, ns)
save_tables.print_grant_table(csv_file, ns)