# Libraries
import os
import re
import json
import time
import random
import pandas as pd

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
import time
import datetime

# specify path of Chromedriver Location:
chromedriver_path = r"C:\Users\gigim\Documents\GitHub\chromedriver-win64\chromedriver.exe"

# Set options for Chrome-Driver (headless mode)
# opts = Options()
# opts.add_argument("--headless")
# opts.add_argument("user-agent=" + random.choice(ua_list))

#service = Service(executable_path=chromedriver_path) 
driver = webdriver.Chrome() #service=service, options=opts

# Liste mit User-Agents für Rotation
ua_path = "user_agents.txt"
ua_list = [line.rstrip('\n') for line in open(ua_path)]
ua_list[:5]



# Get the current date (year, month, and day only)
current_date = datetime.datetime.now().date()
# Initialize WebDriver
driver = webdriver.Chrome()  # Ensure chromedriver is in PATH or provide the full path
url = "https://jobs.ubs.com/TGNewUI/Search/Home/Home?partnerid=25008&siteid=5155#home"
driver.get(url)

# Wait for the page to load
wait = WebDriverWait(driver, 20)

# Initialize data storage
job_links = []
job_htmls = []
job_titles = []

# Step 1: Enter 'Switzerland' in the location search box
location_input = wait.until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='locationSearch']"))
)
location_input.clear()  # Clear any existing text
location_input.send_keys("Switzerland")  # Type 'Switzerland'
time.sleep(1)
# Send the Enter key to trigger the search
location_input.send_keys(Keys.ENTER)
print("Search initiated for 'Switzerland' using the Enter key.")
time.sleep(5)  # Wait for the results page to load

# Step 2: Scroll and interact with "Show More Jobs" button
try:
    # Step 3: Click "Show More Jobs" buttons until no more jobs are available
    while True:
        try:
            # Scroll for 5 seconds before looking for the button
            scroll_start_time = time.time()
            scroll_duration = 5  # Adjust as needed

            while time.time() - scroll_start_time < scroll_duration:
                driver.execute_script("window.scrollBy(0, 2000);")  # Scroll down incrementally
                time.sleep(0.5)  # Pause briefly to allow content to load
            print("Finished scrolling down for 5 seconds.")

            # Find and click the "Show More Jobs" button
            show_more_button = driver.find_element(By.XPATH, '//*[@id="showMoreJobs"]')
            actions = ActionChains(driver)
            actions.move_to_element(show_more_button).click().perform()
            print("Clicked 'Show More Jobs' button.")
            time.sleep(8)  # Wait for jobs to load after clicking the button

        except Exception as e:
            print("No more 'Show More Jobs' buttons to click or error:", e)
            break

    # Step 4: Extract job links
    job_elements = driver.find_elements(By.CSS_SELECTOR, "a.jobtitle")  # CSS selector for job links
    for job in job_elements:
        link = job.get_attribute("href")
        if link and link not in job_links:
            job_links.append(link)

    # Step 5: Open each job link and store its HTML body content
    for link in job_links:
        driver.get(link)
        time.sleep(5)  # Allow page to load
        print(link)
        body_content = driver.page_source
        job_htmls.append(body_content)
        # Extract job title
        try:
            # Locate the job title element
            job_title_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1.answer.ng-binding.jobtitleInJobDetails"))
            )
            job_title = job_title_element.text  # Extract the text of the job title
        except Exception as e:
            print(f"Could not extract job title for {link}: {e}")
            job_title = None  # Handle missing job title gracefully

        print(f"Job Title: {job_title}")
        job_titles.append(job_title)
finally:
    driver.quit()  # Close the WebDriver

# Step 6: Store data in a DataFrame
df = pd.DataFrame({
    "Job URL": job_links,
    "HTML Content": job_htmls,
    "job title" : job_titles,
    "Date": current_date
})

# Save to a CSV file
output_path = "ubs_jobs_data.csv"
df.to_csv(output_path, index=False)

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

x = read_and_increment_number()
df.to_pickle(f"job_data_ubs_{x}.pkl")