"""
@Author : Administrator
@Company : 
@Date : 2026/7/28 11:33
@Desc :
@Version : 1.0
"""
from lxml import etree
import requests

response = requests.get('http://localhost:8080/resume2.html')
response.encoding = 'utf-8'
html = response.text
tree = etree.HTML(html)

# 头部
information_title_name = tree.xpath("//div[@class='resume-card']/div[@class='header']"
                                    "/div[@class='name' and @id='fullname']/text()")
print(information_title_name)
information_title_contacts = tree.xpath("//div[@class='resume-card']/div[@class='header']"
                                        "/div[@class='contact-bar']/div[@class='contact-item']"
                                        "/span/text()")
print(information_title_contacts)

# 基础信息
information_base_contacts1 = tree.xpath("//div[@class='resume-body']/div[@class='sidebar']"
                                       "/div[@class='section']/div[@class='info-grid']"
                                       "/div[@class='info-row']")
titles = []
values = []
for info in information_base_contacts1:
    titles.append(info.xpath(".//span[@class='info-label']/text()")[0])
    values.append(info.xpath("string(.//span[@class='info-value'])"))
print({n: m for n, m in zip(titles, values)})

# 技术栈表格
information_base_contacts2 = tree.xpath("//div[@class='resume-body']/div[@class='sidebar']"
                                       "/div[@class='section']/div[@class='skill-table-wrapper']")
table = information_base_contacts2[0].xpath(".//table")
table_titles = table[0].xpath(".//thead/tr/th/text()")
table_values = []
rows = table[0].xpath(".//tbody/tr")
# print(rows)
for row in rows:
    cols = row.xpath(".//td/text()")
    table_dic = [col.strip() for col in cols]
    if len(table_dic) == len(table_titles):
        table_values.append(dict(zip(table_titles, table_dic)))
    else:
        print("列不匹配.")
print(table_values)
# print({n: m for n, m in zip(table_titles, table_values)})

# 教育经历
information_edu_contacts3 = tree.xpath("//div[@class='resume-body']/div[@class='main-content']"
                                       "/div[@class='section' and @id='education-section']/div[@class='edu-list']")
div_contacts = information_edu_contacts3[0].xpath(".//div[@class='edu-item']")
# print(div_contacts)
infos1 = []
for info in div_contacts:
    title = info.xpath(".//div[@class='edu-title']/text()")
    meta = info.xpath(".//div[@class='edu-meta']//text()")
    text = info.xpath(".//div[@class='desc-text']/text()")
    infos1.append({"title": title, "meta": meta, "text": text})
print(infos1)

# 项目经历
information_edu_contacts4 = tree.xpath("//div[@class='resume-body']/div[@class='main-content']"
                                       "/div[@class='section' and @id='projects-section']")
list_projects = information_edu_contacts4[0].xpath(".//div[@class='project-list']")
list_items = list_projects[0].xpath(".//div[@class='project-item']")
infos2 = []
for item in list_items:
    title = item.xpath(".//div[@class='project-title']/text()")
    meta = item.xpath(".//div[@class='project-meta']//text()")
    text = item.xpath(".//div[@class='desc-text']/text()")
    infos2.append({"title": title, "meta": meta, "text": text})
print(infos2)



