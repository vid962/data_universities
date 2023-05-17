import pandas as pd
import requests
import re
import lxml
import cchardet
from bs4 import BeautifulSoup
from node_creator import NodeCreator
import time

start_time = time.time()

# Set the URL and language code
URL_language_eng = 'https://ects.coi.pw.edu.pl/menu2/changelang/lang/eng'
URL_language_pl = 'https://ects.coi.pw.edu.pl/menu2/changelang/lang/pl'
# request to actual page with saved cookies and headers
sess = requests.Session()


def soup_request(url, sess):
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

    data_list = []
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

                # getting text content of the 'tr' element, not cleaned
                tr_text = tr.get_text(strip=True)
                specialization = tr_text.strip()

                pattern = r'Specjalność:\s*(.*?)(\s*\((?:Rozwiń)\))'
                pattern_2 = r'Specjalność:\s*(.*?)(\s*\((?:Expand)\))'

                # searching for the patterns
                match = re.search(pattern, tr_text)
                match_2 = re.search(pattern_2, tr_text)

                # if any pattern matched, extracting the specialization
                if match or match_2:
                    if match:
                        specialization = match.group(1).strip()
                    else:
                        specialization = match_2.group(1).strip()

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
                        data_list.append(subjects)
                except Exception as e:
                    print(e)

    # creating pandas dataframe
    dataframe = pd.DataFrame(data_list, index=list(range(len(data_list))))
    print(dataframe)
    print(dataframe.shape)

    return dataframe


# create empty list to store the data frames
data_frames = []

df1 = soup_request(URL_language_pl, sess)
data_frames.append(df1)

df2 = soup_request(URL_language_eng, sess)
data_frames.append(df2)

final_df = pd.concat(data_frames)
# final_df = pd.read_csv('final_data.csv') # delete after!!!

def fetch_syllabus_content(syllabus_links, ses):
    data_syllabus_list = []

    for syllabus_link in syllabus_links:
        # checking if the link is valid
        if all([syllabus_link, isinstance(syllabus_link, str)]):
            try:
                response = sess.get(syllabus_link)
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                print(f"Failed to fetch dt elements from {syllabus_link}")
                continue

            soup = BeautifulSoup(response.content, 'lxml')
            all_dt_elements = soup.find_all("dt")
            all_dd_elements = soup.find_all("dd")

            # finding the index of the starting dt element
            start_index = next((index for index, dt in enumerate(all_dt_elements)
                                if dt.text.strip() in ["Purpose of course:", "Cel przedmiotu:"]), None)

            if start_index is not None:
                # selecting all dt and dd elements from start_index onwards
                dt_elements = all_dt_elements[start_index:]
                dd_elements = all_dd_elements[start_index:]

                # combining dt and dd elements, making sure to extract just the text
                combined_elements = " ".join([f"{dt.text}: {dd.text}" for dt, dd in zip(dt_elements, dd_elements)])
                # normalizing whitespace and replacing consecutive spaces with a single space
                combined_elements = re.sub('\s+', ' ', combined_elements)
                # combined_elements = {dt.text: dd.text for dt, dd in zip(dt_elements, dd_elements)}
                result = {
                    "Syllabus": syllabus_link,
                    "Content": combined_elements
                }
                data_syllabus_list.append(result)

    df_syllabus = pd.DataFrame(data_syllabus_list)
    print(df_syllabus)

    return df_syllabus

syllabus_df = fetch_syllabus_content(final_df['Syllabus'], sess)
syllabus_df.to_csv('syllabus.csv', index=False)

# merging the final_df and syllabus_df
final_df = pd.merge(final_df, syllabus_df, on='Syllabus', how='left')
final_df.to_csv('final_data.csv', index=False)
print(final_df.head())

# creating an instance of NodeCreator with the final_df
node_creator = NodeCreator(final_df)

# calling the process_data method to process the data
node_creator.process_data()

# saving the processed data to CSV files
node_creator.save_data_to_csv()

# checking the total running time
end_time = time.time()
elapsed_time = end_time - start_time
print(f"The program took {elapsed_time} seconds to complete.")
