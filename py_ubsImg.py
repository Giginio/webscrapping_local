
# Libraries
import time
import pytesseract
import cv2
import random
import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from PIL import Image
import os

# Set up Chrome options (fixed resolution for consistent scrolling)
options = Options()
options.add_argument("--window-size=1920,1080")  # Ensures each scroll step is predictable

# Initialize WebDriver
driver = webdriver.Chrome(options=options)

# Open UBS job site
url = "https://jobs.ubs.com/TGNewUI/Search/Home/Home?partnerid=25008&siteid=5155#home"
driver.get(url)

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Define unwanted repeated sections (footer, headers, buttons, etc.)
UNWANTED_TEXT = [
    "Terms of use", "Privacy statement", "Report fraudulent mail", "Cookies",
    "Datenschutzerklärung von Infinite Talent", "@ Deutsch", "Apply now"
]

def clean_text(text):
    """ Remove unwanted repetitive footer/header text and empty lines. """
    lines = text.split("\n")
    cleaned_lines = [line.strip() for line in lines if line.strip() and not any(phrase in line for phrase in UNWANTED_TEXT)]
    return "\n".join(cleaned_lines)

def remove_duplicates(prev_text, new_text):
    """ Remove overlapping parts by checking last 10 lines of prev_text against first 10 lines of new_text. """
    prev_lines = prev_text.split("\n")[-10:]  # Last 10 lines of previous text
    new_lines = new_text.split("\n")[:10]  # First 10 lines of new text

    overlap_index = -1
    for i in range(len(new_lines)):
        if new_lines[i] in prev_lines:
            overlap_index = i  # Find where duplication starts

    return "\n".join(new_text.split("\n")[overlap_index + 1:]) if overlap_index != -1 else new_text

def screencapture(link):
    """ Captures job description by scrolling and using OCR. """
    driver.get(link)
    time.sleep(3)  # Allow JavaScript to load

    scroll_height = 500  # Smaller scroll step to avoid skipping content
    full_text = ""
    previous_texts = set()  # Store previous text snippets
    last_text = ""  # Track the last extracted text
    end_reached = False  # Stop condition

    while not end_reached:
        # Take a screenshot
        screenshot_path = f"screenshot_{len(previous_texts)}.png"
        driver.save_screenshot(screenshot_path)

        # Process image with OCR
        img = cv2.imread(screenshot_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray, lang="deu+eng").strip()

        # Clean up unwanted repeated elements
        text = clean_text(text)

        # Check for duplicates and trim overlapping sections
        filtered_text = remove_duplicates(last_text, text)

        # Append only unique content
        if filtered_text.strip() and filtered_text not in previous_texts:
            full_text += "\n" + filtered_text
            last_text = filtered_text  # Update last recorded text
            previous_texts.add(filtered_text)  # Store to detect future duplicates

        # Scroll down
        driver.execute_script(f"window.scrollBy(0, {scroll_height});")
        time.sleep(2)  # Allow content to load

        # Stop scrolling if we are at the bottom of the page
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == driver.execute_script("return window.pageYOffset + window.innerHeight"):
            end_reached = True

    # Extract job title
    try:
        job_title_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1.answer.ng-binding.jobtitleInJobDetails"))
        )
        job_title = job_title_element.text.strip()
    except Exception as e:
        print(f"Could not extract job title for {link}: {e}")
        job_title = None  

    print(f"Job Title: {job_title}")
    print(f"Extracted Text for {link}:\n{full_text[:500]}...\n")

    return full_text, job_title

# Initialize data storage
job_links = []
job_htmls = []
job_titles = []

# Step 1: Wait for the page to load
wait = WebDriverWait(driver, 20)

# Step 2: Enter 'Switzerland' in the location search box
location_input = wait.until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='locationSearch']"))
)
location_input.clear()  
location_input.send_keys("Switzerland")  
time.sleep(1)
location_input.send_keys(Keys.ENTER)
print("Search initiated for 'Switzerland'.")
time.sleep(5)

# Step 3: Scroll and interact with "Show More Jobs" button
try:
    
    try:
        scroll_start_time = time.time()
        scroll_duration = 5  

        while time.time() - scroll_start_time < scroll_duration:
            driver.execute_script("window.scrollBy(0, 2000);")  
            time.sleep(0.5)  

        print("Finished scrolling.")

        show_more_button = driver.find_element(By.XPATH, '//*[@id="showMoreJobs"]')
        actions = ActionChains(driver)
        actions.move_to_element(show_more_button).click().perform()
        print("Clicked 'Show More Jobs' button.")
        time.sleep(8)  

    except Exception as e:
        print("No more 'Show More Jobs' buttons or error:", e)

    # Step 4: Extract job links (limit to 5 jobs)
    job_elements = driver.find_elements(By.CSS_SELECTOR, "a.jobtitle")  
    for job in job_elements:
        link = job.get_attribute("href")
        if link and link not in job_links:
            job_links.append(link)
        #if len(job_links) >= 5:  # Stop after collecting 5 links
            #break

    # Step 5: Open each job link and extract visible job descriptions
    for link in job_links:
        job_text, job_title = screencapture(link)
        job_htmls.append(job_text)
        job_titles.append(job_title)

finally:
    driver.quit()  

# Step 6: Store data in a DataFrame
df = pd.DataFrame({
    "Job URL": job_links,
    "Job Title": job_titles,
    "Job Description": job_htmls,
    "Date": datetime.datetime.now().date()
})

# Save to CSV
output_path = "ubs_jobs_test_data.csv"
df.to_csv(output_path, index=False)

print("UBS Test complete! 5 job records have been scraped and saved.")

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

# Check if the mapped network drive is accessible
drive_path = "Z:/"

# Check if the directory exists
if os.path.exists(drive_path):
    print(f"The network drive {drive_path} is accessible.")
else:
    print(f"The network drive {drive_path} is NOT accessible.")
    df.to_pickle(f"C:/Users/Pierluigi/Documents/GitHub/jobScanBackup/job_data_ubs_{x}.pkl")


df.to_pickle(f"Z:/job_data_ubs_{x}.pkl")