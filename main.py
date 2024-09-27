import sys
import traceback
from time import sleep
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class GoogleMeetBot(object):
    def __init__(self, driver, meeting_url, bot_name):
        self.driver = driver
        self.meeting_url = meeting_url
        self.bot_name = bot_name
        self.participants = []

    def join_meeting(self, join_attempts=0):
        """Join the Google Meet session"""
        try:
            # Navigate to the meeting URL
            self.driver.get(self.meeting_url)

            # Handle "Continue without microphone" if it appears
            # try:
            #     continue_button_xpath = "//span[contains(text(), 'Continue without microphone')]"
            #     continue_button = WebDriverWait(self.driver, 30).until(
            #         EC.element_to_be_clickable((By.XPATH, continue_button_xpath)))
            #     continue_button.click()
            # except TimeoutException:
            #     print("No 'Continue without microphone' prompt found, proceeding.")

            name_input_xpath = "//input[@placeholder='Your name']"
            name_input = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, name_input_xpath)))
            name_input.send_keys(self.bot_name)

            ask_to_join_button_xpath = "//span[contains(text(), 'Ask to join')]/ancestor::button"
            ask_to_join_button = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, ask_to_join_button_xpath)))
            ask_to_join_button.click()
            print(f"Joining the Google Meet meeting as {self.bot_name}...")

        except TimeoutException as e:
            print(f"Error: {str(e)}")
            join_attempts += 1
            if join_attempts >= 5:
                print("Maximum join attempts reached. Could not join the meeting.")
                self.driver.quit()
                raise
            else:
                print(
                    f"Retrying to join the meeting (Attempt {join_attempts})...")
                return self.join_meeting(join_attempts)

    def is_meeting_ongoing(self):
        sleep(30)
        """Check if the meeting is ongoing by monitoring participant count"""
        try:
            people_button_xpath = "//button[@aria-label='People'][@role='button']"
            people_button = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, people_button_xpath)))
            people_button.click()

            participant_elements_parent_xpath = "//div[@aria-label='Participants'][@role='list']"
            participant_elements_parent = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, participant_elements_parent_xpath)))

            participant_elements_xpath = "//div[@role='listitem']"
            participant_elements = participant_elements_parent.find_elements(
                By.XPATH, participant_elements_xpath)

            if len(participant_elements) <= 1:
                print("Participants are less than 2. Meeting has ended.")
                return False

            for element in participant_elements:
                try:
                    uName = element.get_attribute('aria-label')
                    if uName not in self.participants:
                        self.participants.append(uName)
                        print(f"New participant joined: {uName}")
                except NoSuchElementException:
                    continue
            return True
        except Exception as e:
            print(f"Error occurred while checking participants: {str(e)}")
            return False

    def leave_meeting(self):
        """Leave the Google Meet session after 10 minutes if everyone leaves"""
        print("All participants have left. Waiting 10 minutes before leaving...")
        sleep(20)  # 10 mins
        leave_button_xpath = "//*[@aria-label='Leave call']"
        try:
            leave_button = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, leave_button_xpath)))
            leave_button.click()
            print("Meeting left successfully.")
        finally:
            self.driver.quit()


class Browser(object):
    def initialize_browser(self):
        """Initialize Chrome using undetected_chromedriver"""
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument("--disable-search-engine-choice-screen")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-setuid-sandbox")
        chrome_options.add_argument("--use-fake-ui-for-media-stream")

        print("Initializing Chrome browser...")
        driver = uc.Chrome(options=chrome_options, patcher_force_close=True)
        return driver


def write_to_file(file, data):
    with open(file, 'w') as f:
        for item in data:
            f.write(f"{item}\n")


if __name__ == "__main__":
    browser = Browser()
    driver = browser.initialize_browser()

    meeting_url = "https://meet.google.com/nsw-wxkk-ixz"
    bot_name = "zenkoders"

    meet_bot = GoogleMeetBot(driver, meeting_url, bot_name)
    meet_bot.join_meeting()

    while True:
        meeting_active = meet_bot.is_meeting_ongoing()
        if not meeting_active:
            meet_bot.leave_meeting()
            write_to_file('participants.txt', meet_bot.participants)
            break

        sleep(30)
