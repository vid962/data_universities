import pandas as pd
import requests
import re
import lxml
import cchardet
from bs4 import BeautifulSoup
from node_creator import NodeCreator
import time


start_time = time.time()

# Setting the URL and language code
URL_language_eng = 'https://ects.coi.pw.edu.pl/menu2/changelang/lang/eng'
URL_language_pl = 'https://ects.coi.pw.edu.pl/menu2/changelang/lang/pl'
# Initialize session for making requests with saved cookies and headers
sess = requests.Session()


def initial_request():
    """Retrieve first links for different academic years to be used in subsequent requests.
    Returns:
        list: A list of dictionaries containing links and corresponding academic years.
    """

    # Starting link to the year which is going to be scraped first
    starting_page = 'https://ects.coi.pw.edu.pl/menu2/zmienrok/rok/1'
    req = sess.get(starting_page)
    print(req.status_code)
    response = sess.get(starting_page)
    print(response.status_code)
    soup = BeautifulSoup(response.content, "lxml")

    div_content = soup.find('div', id='content')
    # Find all 'a' tags within div_content
    a_tags = div_content.find_all('a')

    study_year = []

    for a_tag in a_tags:

        # Extracting links
        link = a_tag.get('href')

        # Finding button within 'a' tag and extract the year
        button = a_tag.find('button')
        year = button.text if button else None

        # Filtering only needed links, (those needed are shorter than 25 characters)
        if len(link) < 25:
            study_year.append({'link': link, 'year': year})

    return study_year


links_and_years = initial_request()


def subject_syllabus_id(syllabus_link):
    """Extract Syllabus_id from the link to each syllabus.
    Args:
        syllabus_link (str): Link to the syllabus.
    Returns:
        int or None: Extracted Syllabus_id or None if not found.
    """

    match = re.search(r'/(\d+)$', syllabus_link)
    return int(match.group(1)) if match else None


def soup_request(url, sess):
    """Perform requests and parse data from the provided URL.
        Args:
            url (str): URL to request data from.
            sess: Requests session.
        Returns:
            pd.DataFrame: DataFrame containing extracted data.
        """

    # Extracting language code from URL (for now it was only Polish or English)
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

    data_list = []

    for item in links_and_years:
        link = item.get('link')
        print(link)
        year = item.get('year')
        print(year)

        req = sess.get(f'https://ects.coi.pw.edu.pl{link}')
        print(req.status_code)
        response = sess.get(url)
        print(response.status_code)
        soup = BeautifulSoup(response.content, "lxml")
        table = soup.find(name='table')

        for a_tag in table.find_all('a'):

            link = a_tag.get('href').strip()
            link = f'https://ects.coi.pw.edu.pl{link}'
            full_subject = a_tag.get_text().strip()
            field_of_study, _, level = full_subject.rpartition(' ')
            match = re.search(r"\[(.*?)\]", full_subject)
            if match:
                level = match.group(1)
                field_of_study = full_subject.replace(' [' + level + ']', '')

            req = sess.get(link)
            print(link, req.status_code)
            soup = BeautifulSoup(req.text, 'lxml')

            # Extracting all tables and faculty subject
            tables = soup.find('div', {'id': 'content'})
            table1 = tables.findChildren('table')[0]
            faculty = table1.findChildren('tr')[1].findChildren('td')[1].string

            # Iterating through each table row to extract semester, subject and ects
            data_table = tables.findChildren('table')[1]
            semester = ''
            specialization = ''

            pattern = r'Specjalność:\s*(.*?)(\s*\((?:Rozwiń)\))'
            pattern_2 = r'Specjalność:\s*(.*?)(\s*\((?:Expand)\))'

            for tr in data_table.findChildren('tr'):

                tr_class_name = tr.get('class')

                if tr_class_name == ['blok_zwijanie']:

                    # Getting text content of the 'tr' element, not cleaned
                    tr_text = tr.get_text(strip=True)
                    specialization = tr_text.strip()

                    # Searching for the patterns
                    match = re.search(pattern, tr_text)
                    match_2 = re.search(pattern_2, tr_text)

                    # If any pattern matched, extracting the specialization
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

                        # Regular expression pattern to match the needed links
                        pattern = r"/menu3/view2/idPrzedmiot/\d+"

                        # Checking if the extracted link matches the pattern
                        if re.match(pattern, syllabus):
                            syllabus_link = f'https://ects.coi.pw.edu.pl{syllabus}'
                        else:
                            syllabus_link = None

                        syllabus_id = subject_syllabus_id(syllabus_link)

                        if subject != '∑=':
                            subjects = {'University_name': university,
                                        'City': city,
                                        'Country': country,
                                        'Year': year,
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
                                        'Syllabus': syllabus_link,
                                        'Syllabus_id': syllabus_id
                                        }
                            data_list.append(subjects)
                    except Exception as e:
                        print(e)

    dataframe = pd.DataFrame(data_list)

    return dataframe


# Create empty list to store the data frames
data_frames = [soup_request(URL_language_pl, sess), soup_request(URL_language_eng, sess)]

# Concatenate data frames to merge the data
final_df_doubled = pd.concat(data_frames)

# Define filters for duplicate removal
filters = ['Year', 'Field_of_study', 'Level', 'Faculty', 'Specialization', 'Subject', 'Syllabus_id']

# Drop duplicates based on filters and keep the first occurrence
final_df = final_df_doubled.drop_duplicates(subset=filters, keep='first')


def fetch_syllabus_content(syllabus_links, ses):
    """Fetch syllabus content for a list of syllabus links.
        Args:
            syllabus_links (Series): Series containing syllabus links.
            ses: Requests session.
        Returns:
            pd.DataFrame: DataFrame containing syllabus content.
        """

    data_syllabus_list = []

    for syllabus_link in syllabus_links:
        # Checking if the link is valid
        if all([syllabus_link, isinstance(syllabus_link, str)]):
            try:
                response = ses.get(syllabus_link)
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                print(f"Failed to fetch dt elements from {syllabus_link}")
                continue

            soup = BeautifulSoup(response.content, 'lxml')
            all_dt_elements = soup.find_all("dt")
            all_dd_elements = soup.find_all("dd")

            # Finding the index of the starting dt element
            start_index = next((index for index, dt in enumerate(all_dt_elements)
                                if dt.text.strip() in ["Purpose of course:", "Cel przedmiotu:"]), None)

            if start_index is not None:
                # Selecting all dt and dd elements from start_index onwards
                dt_elements = all_dt_elements[start_index:]
                dd_elements = all_dd_elements[start_index:]

                # Combining dt and dd elements, making sure to extract the raw HTML
                combined_elements = " ".join([f"{str(dt)}: {str(dd)}" for dt, dd in zip(dt_elements, dd_elements)])
                # Normalizing whitespace and replacing consecutive spaces with a single space
                combined_elements = re.sub('\s+', ' ', combined_elements)
                result = {
                    "Syllabus": syllabus_link,
                    "Content": combined_elements
                }
                data_syllabus_list.append(result)

    df_syllabus = pd.DataFrame(data_syllabus_list)
    print(df_syllabus)

    return df_syllabus


# Fetching syllabus content and save to CSV
syllabus_df = fetch_syllabus_content(final_df['Syllabus'], sess)
syllabus_df.to_csv('syllabus.csv', index=False)

# Merging syllabus data with the main data frame
final_df = pd.merge(final_df, syllabus_df, on='Syllabus', how='left')
final_df.to_csv('final_data.csv', index=False)
print(final_df.head())

# Creating an instance of NodeCreator with the final_df
node_creator = NodeCreator(final_df)

# Calling the process_data method to process the data
node_creator.process_data()

# Saving the processed data to CSV files
node_creator.save_data_to_csv()

# Calculate and display the total running time
end_time = time.time()
elapsed_time = end_time - start_time
print(f"The program took {elapsed_time} seconds to complete.")

