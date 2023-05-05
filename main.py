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
        field_of_study = ' '.join(full_subject[:-2])
        level = str(full_subject[-2])

        req = sess.get(link)
        print(link, req.status_code)
        soup = BeautifulSoup(req.text, 'html.parser')

        # extracting all tables and faculty subject
        tables = soup.find('div', {'id': 'content'})
        table1 = tables.findChildren('table')[0]
        faculty = table1.findChildren('tr')[1].findChildren('td')[1].string

        # iterating through each table row to extract semester, subject and ects
        data_table = tables.findChildren('table')[1]
        semester = ''
        specialization = ''
        for tr in data_table.findChildren('tr'):

            tr_class_name = tr.get('class')

            if tr_class_name == ['blok_zwijanie']:

                # To get the text content of the 'tr' element, not cleaned
                tr_text = tr.get_text(strip=True)
                pattern = r'Specjalność:\s*(.*?)(\s*\((?:Rozwiń)\))'
                extracted_text = re.search(pattern, tr_text)

                if extracted_text:
                    specialization = extracted_text.group(1).strip()

                else:
                    print("Desired text not found in the string (specialisation)")

            if len(tr.findChildren('td')) > 0 and tr.findChildren('td')[0].findChildren('h3'):
                semester = tr.findChildren('td')[0].findChildren('h3')[0].get_text(strip=True)
                print(semester)

            if len(tr.findChildren('td')) > 1:
                try:
                    subject = tr.findChildren('td')[2].get_text(strip=True)
                    print(subject)
                    ects = tr.findChildren('td')[3].get_text(strip=True)

                    # extracting all syllabus links
                    a_tag = tr.findChildren('td')[-1].find('a')
                    if a_tag is not None:
                        syllabus = a_tag['href'].strip()
                    else:
                        syllabus = None

                    # regular expression pattern to match the needed links
                    pattern = r"/menu3/view2/idPrzedmiot/\d+"

                    # checking if the extracted link matches the pattern
                    if re.match(pattern, syllabus):
                        syllabus_link = f'https://ects.coi.pw.edu.pl{syllabus}'
                    else:
                        syllabus_link = None

                    if subject != '∑=':
                        subjects = {'University_name': university,
                                    'City': city,
                                    'Country': country,
                                    'Source': url,
                                    'Language': language,
                                    'Field_of_study': field_of_study,
                                    'Level': level,
                                    'Link': link,
                                    'Faculty': faculty,
                                    'Semester': semester.replace(':', ''),
                                    'Specialization': specialization,
                                    'Subject': subject,
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

# final_df = pd.read_csv('final_data.csv')  # delete after
# print(final_df['Syllabus'].value_counts().value_counts())  # delete

def fetch_dt_elements(syllabus_links):

    dt_data_list = []

    for syllabus_link in syllabus_links:

        # checking if the link is not None, an instance of str, and at least 30 characters long before making a request
        if syllabus_link and isinstance(syllabus_link, str) and len(syllabus_link) >= 30:

            response = requests.get(syllabus_link)

            if response.status_code != 200:
                print(f"Failed to fetch dt elements from {syllabus_link}")
                continue

            soup = BeautifulSoup(response.content, "html.parser")

            # finding the dt elements
            dt_elements_eng = soup.find("dt", text="Purpose of course:")
            dt_elements_pl = soup.find("dt", text="Cel przedmiotu:")

            # combining the English and Polish dt elements
            dt_elements = []
            if dt_elements_eng:
                dt_elements.append(dt_elements_eng)
            if dt_elements_pl:
                dt_elements.append(dt_elements_pl)

            dt_elements_html = [str(element) for element in dt_elements]

            result = {
                "Link": syllabus_link,
                "Content": " ".join(dt_elements_html)
            }
            dt_data_list.append(result)

    return dt_data_list


print(fetch_dt_elements(final_df['Syllabus']))
print(final_df.shape)

# creating an instance of NodeCreator with the final_df
node_creator = NodeCreator(final_df)

# calling the process_data method to process the data
node_creator.process_data()

# saving the processed data to CSV files
node_creator.save_data_to_csv()











