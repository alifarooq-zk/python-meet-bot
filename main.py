import subprocess
from time import sleep
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class GoogleMeetBot:
    def __init__(self, driver, meeting_url, bot_name, audio_file):
        self.driver = driver
        self.meeting_url = meeting_url
        self.bot_name = bot_name
        self.participants = set()
        self.audio_file = audio_file
        self.ffmpeg_process = None

    def join_meeting(self, max_attempts=5):
        """Join the Google Meet session and start recording audio"""
        attempts = 0
        while attempts < max_attempts:
            try:
                self.driver.get(self.meeting_url)

                self._input_bot_name()
                self._click_ask_to_join()

                print(f"Successfully joined the Google Meet meeting as {
                      self.bot_name}.")
                self.start_audio_recording()
                return True
            except TimeoutException:
                attempts += 1
                print(f"Timeout while trying to join. Retrying... (Attempt {
                      attempts}/{max_attempts})")
                if attempts >= max_attempts:
                    print("Maximum attempts to join the meeting reached.")
                    self.driver.quit()
                    return False
        return False

    def _input_bot_name(self):
        """Fill in the bot name in the name input field"""
        name_input_xpath = "//input[@placeholder='Your name']"
        name_input = WebDriverWait(self.driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, name_input_xpath)))
        name_input.send_keys(self.bot_name)

    def _click_ask_to_join(self):
        """Click on 'Ask to Join' button"""
        ask_to_join_button_xpath = "//span[contains(text(), 'Ask to join')]/ancestor::button"
        ask_to_join_button = WebDriverWait(self.driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, ask_to_join_button_xpath)))
        ask_to_join_button.click()

    def is_meeting_ongoing(self):
        """Check if the meeting is ongoing by monitoring participant count"""
        sleep(10)
        try:
            self._click_people_button()
            participants_list = self._get_participant_elements()

            if len(participants_list) <= 1:  # Only the bot itself is present
                print("Participants are less than 2. Meeting has ended.")
                return False

            self._update_participants(participants_list)
            return True
        except Exception as e:
            print(f"Error occurred while checking participants: {str(e)}")
            return False

    def _click_people_button(self):
        """Open the participants list"""
        people_button_xpath = "//button[@aria-label='People'][@role='button']"
        people_button = WebDriverWait(self.driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, people_button_xpath)))
        people_button.click()

    def _get_participant_elements(self):
        """Return a list of participant elements"""
        participant_elements_parent_xpath = "//div[@aria-label='Participants'][@role='list']"
        participant_elements_parent = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.XPATH, participant_elements_parent_xpath)))
        participant_elements_xpath = "//div[@role='listitem']"
        return participant_elements_parent.find_elements(By.XPATH, participant_elements_xpath)

    def _update_participants(self, participant_elements):
        """Update the participant list with any new participants"""
        for element in participant_elements:
            try:
                uName = element.get_attribute('aria-label')
                if uName not in self.participants:
                    self.participants.add(uName)
                    print(f"New participant joined: {uName}")
            except NoSuchElementException:
                continue

    def leave_meeting(self):
        """Leave the Google Meet session and stop recording"""
        print("All participants have left. Waiting 20 seconds before leaving...")
        sleep(20)

        leave_button_xpath = "//*[@aria-label='Leave call']"
        try:
            leave_button = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, leave_button_xpath)))
            leave_button.click()
            print("Meeting left successfully.")
        finally:
            self.stop_audio_recording()
            self.driver.close()
            sleep(1)

    def start_audio_recording(self):
        """Start recording system audio using ffmpeg on Windows"""
        print("Starting audio recording with ffmpeg on Windows...")
        self.ffmpeg_process = subprocess.Popen(
            ["ffmpeg", "-f", "dshow", "-i",
                "audio=Stereo Mix (Realtek(R) Audio)", self.audio_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    def stop_audio_recording(self):
        """Stop the ffmpeg audio recording process"""
        if self.ffmpeg_process:
            print("Stopping audio recording...")
            self.ffmpeg_process.terminate()
            self.ffmpeg_process.wait()
            print(f"Audio saved to {self.audio_file}")


class Browser:
    @staticmethod
    def initialize_browser():
        """Initialize undetected Chrome browser"""
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument("--disable-search-engine-choice-screen")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-setuid-sandbox")
        chrome_options.add_argument("--use-fake-ui-for-media-stream")

        print("Initializing Chrome browser...")
        driver = uc.Chrome(options=chrome_options, patcher_force_close=True)
        return driver


def write_to_file(filename, data):
    """Write data to a file"""
    with open(filename, 'w') as f:
        for item in data:
            f.write(f"{item}\n")


if __name__ == "__main__":
    browser = Browser()
    driver = browser.initialize_browser()

    meeting_url = "https://meet.google.com/jhu-yhke-myh"
    bot_name = "zenkoders"
    audio_file = "meeting_audio.mp3"

    meet_bot = GoogleMeetBot(driver, meeting_url, bot_name, audio_file)

    if meet_bot.join_meeting():
        while meet_bot.is_meeting_ongoing():
            sleep(10)  # Check meeting status every 10 seconds

        meet_bot.leave_meeting()
        write_to_file('participants.txt', meet_bot.participants)
