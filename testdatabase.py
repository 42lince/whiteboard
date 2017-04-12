from bs4 import BeautifulSoup
import requests
import sqlite3


html_doc = requests.get("https://en.wikipedia.org/wiki/Neighborhoods_in_New_York_City#Community_areas").text

soup = BeautifulSoup(html_doc, 'html.parser')

allcolumns = soup.find(id = "mw-content-text").table.find_all("td")

neighborhoods = []

for i in range(len(allcolumns)):
    if (i % 5 == 4):
        neighborhoods.extend(allcolumns[i].text.split(","))

conn= sqlite3.connect('data.db')
c = conn.cursor()

#c.execute('''CREATE TABLE neighborhoods(id int, name text)''')

print('{} found'.format(len(neighborhoods)))
for i in range(len(neighborhoods)):
    command = "INSERT INTO neighborhoods (id, name) VALUES ({}, '{}')".format(i, neighborhoods[i])
    c.execute(command)

conn.commit()
conn.close()
