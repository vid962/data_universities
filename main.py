import pandas as pd
import requests
from bs4 import BeautifulSoup
import scraper_helper

# extracted the headers of website from chrome network tab
headers = """accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
accept-encoding: gzip, deflate, br
accept-language: en-GB,en-US;q=0.9,en;q=0.8
cache-control: max-age=0
cookie: PHPSESSID=14cakhmscle13lsv1tq4qj12oj; pw_virt6_persistence=460917258.35918.0000
sec-ch-ua: "Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: "Windows"
sec-fetch-dest: document
sec-fetch-mode: navigate
sec-fetch-site: none
sec-fetch-user: ?1
upgrade-insecure-requests: 1
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"""

headers_eng = """accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8
accept-encoding: gzip, deflate, br
accept-language: en-US,en;q=0.5
cookie: PHPSESSID=f4cqt6rot4sn65nf84a2kkmbuc; pw_virt6_persistence=460917258.35918.0000
referer: https://ects.coi.pw.edu.pl/menu2/programy
sec-ch-ua: "Chromium";v="112", "Brave";v="112", "Not:A-Brand";v="99"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: "Windows"
sec-fetch-dest: document
sec-fetch-mode: navigate
sec-fetch-site: same-origin
sec-fetch-user: ?1
sec-gpc: 1
upgrade-insecure-requests: 1
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"""

# using scraper_helper library to convert the string headers into dictionary, saves a lot of time
headers = scraper_helper.get_dict(headers, strip_cookie=False)
headers_eng = scraper_helper.get_dict(headers_eng, strip_cookie=False)

print(headers)
print(headers_eng)

# Set the URL and language code
URL_language_eng = 'https://ects.coi.pw.edu.pl/menu2/changelang/lang/eng'
URL_language = 'https://ects.coi.pw.edu.pl/menu2/changelang/lang/pl'


def soup_request(url, headers):
    # Make subsequent request to actual page with saved cookies and headers
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    table = soup.find(name='table')

    data_frame_data = []
    for a_tag in table.find_all('a'):
        link = a_tag.get('href').strip()

        link = f'https://ects.coi.pw.edu.pl{link}'

        subject = a_tag.get_text().strip()
        req = requests.get(link, headers=headers)
        print(link, req.status_code)
        soup = BeautifulSoup(req.text, 'html.parser')

        # extracting all tables and faculty name
        tables = soup.find('div', {'id': 'content'})
        table1 = tables.findChildren('table')[0]
        faculty = table1.findChildren('tr')[1].findChildren('td')[1].string

        # iterating through each table row to extract semester, name and ects
        data_table = tables.findChildren('table')[1]
        semester = ''
        for tr in data_table.findChildren('tr'):
            if len(tr.findChildren('td')) > 0 and tr.findChildren('td')[0].findChildren('h3'):
                semester = tr.findChildren('td')[0].findChildren('h3')[0].get_text(strip=True)
                print(semester)
            if len(tr.findChildren('td')) > 1:
                try:
                    name = tr.findChildren('td')[2].get_text(strip=True)
                    ects = tr.findChildren('td')[3].get_text(strip=True)
                    if name != '∑=':
                        subjects = {'Subject': subject,
                                    'Link': link,
                                    'Faculty': faculty,
                                    'Semester': semester.replace(':', ''),
                                    'Name': name,
                                    'Ect': ects
                                    }
                        data_frame_data.append(subjects)
                except Exception as e:
                    print(e)

        # creating pandas dataframe
        dataframe = pd.DataFrame(data_frame_data, index=list(range(len(data_frame_data))))
    return dataframe


# create empty list to store the data frames
data_frames = []

soup_request(URL_language_eng, headers_eng)
df1 = soup_request(URL_language_eng, headers_eng)
data_frames.append(df1)

df2 = soup_request(URL_language, headers)
data_frames.append(df2)

final_df = pd.concat(data_frames)
# print(final_df)
# print(final_df.shape)

# CSV export
# final_df.to_csv('final_data.csv', index=False)

# Create nodes dataframe
nodes_df = pd.DataFrame()
nodes_df['node_id'] = final_df['Subject'] + final_df['Faculty']
nodes_df['node_type'] = final_df['Faculty']
nodes_df = nodes_df.drop_duplicates()

# Create relations dataframe
relations_df = pd.DataFrame()
relations_df['from_id'] = final_df['Subject'] + final_df['Faculty']
relations_df['to_id'] = final_df['Name'] + final_df['Faculty']
relations_df['relation_type'] = final_df['Semester']
relations_df['weight'] = final_df['Ect']

# Create node_properties dataframe
node_properties_df = pd.DataFrame()
node_properties_df['node_id'] = final_df['Subject'] + final_df['Faculty']
node_properties_df['property_type'] = 'Link'
node_properties_df['property_value'] = final_df['Link']

# Save dataframes to CSV files
nodes_df.to_csv("nodes.csv", index=False)
relations_df.to_csv("relations.csv", index=False)
node_properties_df.to_csv("node_properties.csv", index=False)

