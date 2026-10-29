"""
@Author : Administrator
@Company : 
@Date : 2026/7/28 10:18
@Desc :
@Version : 1.0
"""
import requests
from bs4 import BeautifulSoup

# response = requests.get("http://localhost:8080/resume1.html")
# response.encoding = "UTF-8"
# html = response.text
# soup = BeautifulSoup(html, "lxml")
# name = soup.find(id="name").get_text()
# # print(name)
# contact_list1 = soup.find_all(class_="contact")
# # print(contact_list1[0].get_text(), contact_list1[1].get_text())
# contact_list2 = soup.find_all(class_="info")
# # print(contact_list2[0].get_text(), contact_list2[1].get_text())
#
# form = soup.find(id="education")
# titles = form.find_all("th")
# rows = form.find_all("tr")
# contact_list3 = []
# for row in rows:
#     cols = row.find_all("td")
#     for col in cols:
#         contact_list3.append(col.get_text())
# print(contact_list3)
# contact4 = {n.get_text(): m for n, m in zip(titles, contact_list3)}
# print(contact4)
# results = soup.find(id="project").find_all("p")
# contacts = []
# for contact in results:
#     contacts.append(contact.get_text())
# print(contacts)

from lxml import etree

response1 = requests.get("http://localhost:8080/resume1.html")
response1.encoding = "UTF-8"
html1 = response1.text
tree = etree.HTML(html1)
# //*[@id="name"]
# /html/body/h2
name = tree.xpath("/html/body/h2/text()")[0]
print(name)
cont1 = tree.xpath("//div[@class='contact'][1]/text()")[0]
print(cont1)
cont2 = tree.xpath("//div[@class='contact'][2]//text()")
print("".join(cont2))
cont3 = tree.xpath("//*[@class='info']//text()")
print("\n".join(cont3))

titles = tree.xpath("//table[@id='education']/tr/th/text()")
cont4 = tree.xpath("//table[@id='education']/tr/td/text()")

cont_til = {n: m for n, m in zip(titles, cont4)}
print(cont_til)

cont5 = tree.xpath("//div[@id='project']//p/text()")
print("\n".join(cont5))


