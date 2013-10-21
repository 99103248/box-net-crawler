from crawler import Crawler

#construct a crawler with email and password
crawler = Crawler('your_email', 'your_password')
crawler.login()

# list files for a sub directory
# the first arguments must be a folder name
# sorted_by is optional: name, date, size
# sorted_direction is optional: ASC, DESC
lst_files = crawler.ls('a_folder_name', sorted_by='date', sorted_direction='ASC')