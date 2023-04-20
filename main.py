import pandas as pd
import requests
from bs4 import BeautifulSoup

# Set the URL and language code
URL_language_eng = 'https://ects.coi.pw.edu.pl/menu2/changelang/lang/eng'
URL_language_pl = 'https://ects.coi.pw.edu.pl/menu2/changelang/lang/pl'


def soup_request(url):

    # request to actual page with saved cookies and headers
    sess = requests.Session()

    # extract language code from URL
    lang = url.split('/')[-1]
    language = 'Polish' if lang == 'pl' else 'English'

    req = sess.get('https://ects.coi.pw.edu.pl/menu2/programy')
    print(req.status_code)
    response = sess.get(url)
    print(response.status_code)
    soup = BeautifulSoup(response.content, "html.parser")

    table = soup.find(name='table')

    data_frame_data = []
    for a_tag in table.find_all('a'):

        link = a_tag.get('href').strip()
        link = f'https://ects.coi.pw.edu.pl{link}'

        full_subject = a_tag.get_text().strip().split(' ')
        subject = ' '.join(full_subject[:-2])
        level = str(full_subject[-2])

        req = sess.get(link)
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
                    print(name)
                    ects = tr.findChildren('td')[3].get_text(strip=True)

                    # extracting all syllabus links
                    syllabus = tr.findChildren('td')[-1].find('a')['href'].strip()
                    syllabus_link = f'https://ects.coi.pw.edu.pl{syllabus}'

                    if name != '∑=':
                        subjects = {'University_name': 'Politechnika Warszawska',
                                    'City': 'Warsaw',
                                    'Country': 'POL',
                                    'Source': url,
                                    'Language': language,
                                    'Subject': subject,
                                    'Level': level,
                                    'Link': link,
                                    'Faculty': faculty,
                                    'Semester': semester.replace(':', ''),
                                    'Name': name,
                                    'Ect': ects,
                                    'Syllabus': syllabus_link
                                    }
                        data_frame_data.append(subjects)
                except Exception as e:
                    print(e)

    # creating pandas dataframe
    dataframe = pd.DataFrame(data_frame_data, index=list(range(len(data_frame_data))))
    print(dataframe)
    print(dataframe.shape)

    return dataframe


# create empty list to store the data frames
data_frames = []

df1 = soup_request(URL_language_pl)
data_frames.append(df1)

df2 = soup_request(URL_language_eng)
data_frames.append(df2)

final_df = pd.concat(data_frames)
final_df.to_csv('final_data.csv', index=False)

print(final_df)
print(final_df.shape)

# creating sets for unique nodes and relations
unique_nodes = set()
unique_relations = set()
node_properties = []

for _, row in final_df.iterrows():
    # create university node
    university_node = {
        'Node_name': row['University_name'],
        'Node_type': 'university',
        'source': row['Source'],
        'language': row['Language'],
    }
    # add university node to unique nodes set
    unique_nodes.add(tuple(university_node.items()))

    # create city node
    city_node = {
        'Node_name': row['City'],
        'Node_type': 'city',
        'source': row['City'],
        'language': row['Language'],
    }
    # add city node to unique nodes set
    unique_nodes.add(tuple(city_node.items()))

    # create country node
    country_node = {
        'Node_name': row['Country'],
        'Node_type': 'country',
        'source': row['Country'],
        'language': row['Language'],
    }
    # add country node to unique nodes set
    unique_nodes.add(tuple(country_node.items()))

    # create university-city relation
    university_city_relation = {"source": row['University_name'],
                                "label": "IS_LOCATED",
                                "target": row['City']}
    # add university-city relation to unique relations set
    unique_relations.add(tuple(university_city_relation.items()))

    # create city-country relation
    city_country_relation = {"source": row['City'],
                             "label": "IS_PART_OF",
                             "target": row['Country']}
    # add city-country relation to unique relations set
    unique_relations.add(tuple(city_country_relation.items()))

# Loop through the unique nodes
for node in unique_nodes:

    # Loop through the items in each node tuple
    for item in node:
        # Append the node property as a dictionary to the node_properties list
        node_property = {
            'node_name': 'node_name',
            'property_name': 'property_name',
            'property_value': 'property_value'
        }
node_properties.append(node_property)


# convert unique nodes and relations sets back to dictionaries
unique_nodes = [dict(node) for node in unique_nodes]
unique_relations = [dict(relation) for relation in unique_relations]

nodes_df = pd.DataFrame(unique_nodes)
relations_df = pd.DataFrame(unique_relations)

nodes_df.to_csv('nodes.csv')
relations_df.to_csv('relations.csv')

# Convert the node_properties list to a DataFrame
node_properties_df = pd.DataFrame(node_properties)
node_properties_df.to_csv('node_properties.csv', index=False)





