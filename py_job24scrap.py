### new cersion with css selector?

import pandas as pd
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import random

# Liste mit User-Agents für Rotation
ua_path = "user_agents.txt"
ua_list = [line.rstrip('\n') for line in open(ua_path)]
ua_list[:10]

import random
# specify path of Chromedriver Location:
#chromedriver_path = r"C:\Users\Pierluigi\Documents\GitHub\chromedriver-win64\chromedriver.exe"
chromedriver_path = r"C:\Users\gigim\Documents\GitHub\chromedriver-win64\chromedriver.exe"



# Function to get the HTML content of a page and check if it's valid
def get_html(url):
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("user-agent=" + random.choice(ua_list))
    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=opts)
    
    try:
        # Load the page
        driver.get(url)
    except WebDriverException as e:
        print(f"Error loading page: {e}")
        driver.quit()
        return None

    # Get the full content of the website
    source = driver.page_source

    # Close driver
    driver.quit()

    return source

def read_and_increment_number(file_path="ubs_number.txt"):
    """
    Reads an integer from a file, increments it by 1, and writes it back.
    Returns the original number before incrementing.
    """
    try:
        # Step 1: Read the current number from the file
        with open(file_path, "r") as file:
            current_number = int(file.read().strip())
    except FileNotFoundError:
        # If the file doesn't exist, initialize with 1
        current_number = 1

    # Step 2: Increment the number
    next_number = current_number + 1

    # Step 3: Write the incremented number back to the file
    with open(file_path, "w") as file:
        file.write(str(next_number))

    return current_number  # Return the number before incrementing


bank = 'Raiffeisen'
page_list = list(range(1, 2))

# Initialize an empty list to store job data across all pages
job_data = []

for page in page_list:
    url = f'https://www.jobscout24.ch/de/jobs/bank/?p={page}'
    
    source = get_html(url)
    if source is None:
        continue  # Skip to the next page if the response is invalid

    # Parse HTML content with BeautifulSoup
    soup = BeautifulSoup(source, 'html.parser')

    # Get links
    link_elements = soup.find_all(class_='job-list-item')

    for element in link_elements:
        # Extract the job ID
        job_id = element.get('data-job-id')
        full_url = 'https://www.jobscout24.ch/de/jobs/raiffeisen/?jobId=' + job_id
        
        # Extract the job title from the <a> tag within the element
        job_title_element = element.find('a', class_='job-link-detail job-title')
        job_title = job_title_element['title'] if job_title_element else 'N/A'
        
        # Extract the data-job-detail-url attribute
        job_detail_url = element.get('data-job-detail-url', 'N/A')
        
        # Extract job attributes using a CSS selector
        job_attributes_element = element.select_one('p.job-attributes')
        job_attributes_html = str(job_attributes_element) if job_attributes_element else 'N/A'
        
        # Fetch the job-specific page HTML (if needed)
        source_job = get_html(full_url)
        
        # Parse job-specific page content with BeautifulSoup
        soup_job = BeautifulSoup(source_job, 'html.parser')
        
        # Find the job description or details within the job page
        job_element = soup_job.find('div', class_='job-details-bottom details-scroll-container')
        
        # Extract job type or description
        job_type = str(job_element) if job_element else None

        # Get the current date (year, month, and day only)
        current_date = datetime.datetime.now().date()
        
        # Append the extracted data to the list
        job_data.append({
            'Job URL': full_url,
            'Job Detail URL': job_detail_url, # reame to HTML content
            'Job Attributes': job_attributes_html,
            'Date': current_date,
            'Title': job_title,
            'Job Type': job_type,
        })

# Convert the list of job data to a DataFrame
df = pd.DataFrame(job_data)

# Convert the df to pkl file
x = read_and_increment_number()
df.to_pickle(f"job_data_job24_{x}.pkl")
# Display the DataFrame
print(df)