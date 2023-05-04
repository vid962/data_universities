import pandas as pd
import requests
import re
from bs4 import BeautifulSoup
from node_creator import NodeCreator

# Set the URL and language code
URL_language_eng = 'https://ects.coi.pw.edu.pl/menu2/changelang/lang/eng'
URL_language_pl = 'https://ects.coi.pw.edu.pl/menu2/changelang/lang/pl'


def soup_request(url):

    # request to actual page with saved cookies and headers
    sess = requests.Session()

    # extract language code from URL
    lang = url.split('/')[-1]

    lang_dict = {
        'pl': {
            'language': 'Polish',
            'university': 'Politechnika Warszawska',
            'country': 'Polska',
            'city': 'Warszawa'
        },
        'eng': {
            'language': 'English',
            'university': 'Warsaw University of Technology',
            'country': 'Poland',
            'city': 'Warsaw'
        }
    }

    language = lang_dict[lang]['language']
    university = lang_dict[lang]['university']
    country = lang_dict[lang]['country']
    city = lang_dict[lang]['city']

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

                    # regular expression pattern to match the needed links
                    pattern = r"/menu3/view2/idPrzedmiot/\d+"

                    # checking if the extracted link matches the pattern
                    if re.match(pattern, syllabus):
                        syllabus_link = f'https://ects.coi.pw.edu.pl{syllabus}'
                    else:
                        syllabus_link = None

                    if name != '∑=':
                        subjects = {'University_name': university,
                                    'City': city,
                                    'Country': country,
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


# final_df2 = pd.read_csv('final_data.csv')  # delete after
#
# print(final_df2['Syllabus'].value_counts())  # delete





# print(final_df)
print(final_df.shape)



# creating an instance of NodeCreator with the final_df
node_creator = NodeCreator(final_df)

# calling the process_data method to process the data
node_creator.process_data()

# saving the processed data to CSV files
node_creator.save_data_to_csv()











