import contextlib
import logging
import time
import urllib.parse

from selenium.webdriver.common.by import By

from src.browser import Browser


class Login:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver
        self.utils = browser.utils

    def login(self):
        logging.info("[LOGIN] " + "Logging-in...")
        self.webdriver.get("https://login.live.com/")
        alreadyLoggedIn = False
        while True:
            try:
                self.utils.waitUntilVisible(
                    By.CSS_SELECTOR, 'html[data-role-name="MeePortal"]', 0.1
                )
                alreadyLoggedIn = True
                break
            except Exception:  # pylint: disable=broad-except
                try:
                    self.utils.waitUntilVisible(By.ID, "i0116", 0.1)
                    break
                except Exception:  # pylint: disable=broad-except
                    if self.utils.tryDismissAllMessages():
                        continue

        if not alreadyLoggedIn:
            self.executeLogin()
        self.utils.tryDismissCookieBanner()

        logging.info("[LOGIN] " + "Logged-in !")

        self.utils.goHome()
        points = self.utils.getAccountPoints()

        logging.info("[LOGIN] " + "Ensuring login on Bing...")
        self.checkBingLogin()
        logging.info("[LOGIN] Logged-in successfully !")
        return points

    def executeLogin(self):
        self.utils.waitUntilVisible(By.ID, "i0116", 10)
        logging.info("[LOGIN] " + "Writing email...")
        self.webdriver.find_element(By.NAME, "loginfmt").send_keys(
            self.browser.username
        )
        self.webdriver.find_element(By.ID, "idSIButton9").click()

        try:
            self.enterPassword(self.browser.password)
        except Exception:  # pylint: disable=broad-except
            logging.error("[LOGIN] " + "2FA required !")
            with contextlib.suppress(Exception):
            #     code = self.webdriver.find_element(
            #         By.ID, "idRemoteNGC_DisplaySign"
            #     ).get_attribute("innerHTML")
            #     logging.error("[LOGIN] " + f"2FA code: {code}")
            # logging.info("[LOGIN] Press enter when confirmed...")
            # input()
                # Find the 2FA html element
                code_element = self.webdriver.find_element(By.ID, "displaySign")
                code = code_element.text
                logging.error("[LOGIN] " + f"2FA code: {code}")
                # Take a screenshot (not necessary)
                # self.webdriver.save_screenshot('2fa_screenshot.png')
                # logging.info("[LOGIN] Screenshot saved as '2fa_screenshot.png'")
                logging.info("[LOGIN] Press enter when confirmed...")
                input()

            # Click the checkbox and the "Yes" button after submitting the 2FA code
            self.click_buttons_after_2fa()

        while not (
            urllib.parse.urlparse(self.webdriver.current_url).path == "/"
            and urllib.parse.urlparse(self.webdriver.current_url).hostname
            == "account.microsoft.com"
        ):
            self.utils.tryDismissAllMessages()
            time.sleep(1)

        self.utils.waitUntilVisible(
            By.CSS_SELECTOR, 'html[data-role-name="MeePortal"]', 10
        )

    def enterPassword(self, password):
        self.utils.waitUntilClickable(By.NAME, "passwd", 10)
        self.utils.waitUntilClickable(By.ID, "i0118", 10)
        self.utils.waitUntilClickable(By.ID, "idSIButton9", 10)
        # browser.webdriver.find_element(By.NAME, "passwd").send_keys(password)
        # If password contains special characters like " ' or \, send_keys() will not work
        password = password.replace("\\", "\\\\").replace('"', '\\"')
        self.webdriver.execute_script(
            f'document.getElementsByName("passwd")[0].value = "{password}";'
        )
        logging.info("[LOGIN] " + "Writing password...")
        self.webdriver.find_element(By.ID, "idSIButton9").click()
        time.sleep(3)
        logging.info("[LOGIN] " + "Writing password...")
       
        password_field = self.webdriver.find_element(By.ID, "i0118")

        while True:
            password_field.send_keys(password)
            time.sleep(3)
            if password_field.get_attribute("value") == password:
                self.webdriver.find_element(By.ID, "idSIButton9").click()
                logging.info("[LOGIN] " + "Password submitted")
                break

            password_field.clear()
            time.sleep(3)
        time.sleep(3)

        # self.webdriver.save_screenshot('pass_end_screenshot.png')
        # logging.info("[LOGIN] Screenshot saved as 'pass_end_screenshot.png'")

    def click_buttons_after_2fa(self):
        try:
            # Find and check the checkbox if present (it will be there if the session is blank, otherwise skip this step)
            checkbox = self.webdriver.find_element(By.ID, "checkboxField")
            if checkbox and not checkbox.is_selected():
                checkbox.click()
                logging.info("[LOGIN] Checkbox blunt")

                # Add a delay to make sure that the page refreshes
                time.sleep(2)

                # Find and click the "Yes" button
                accept_button = self.webdriver.find_element(By.ID, "acceptButton")
                if accept_button:
                    accept_button.click()
                    logging.info("[LOGIN] 'Yes' button clicked")

        except Exception as e:
            logging.error(f"[LOGIN] Error occurred while clicking checkbox and button: {e}")

    def checkBingLogin(self):
        self.webdriver.get(
            "https://www.bing.com/fd/auth/signin?action=interactive&provider=windows_live_id&return_url=https%3A%2F%2Fwww.bing.com%2F"
        )
        while True:
            currentUrl = urllib.parse.urlparse(self.webdriver.current_url)
            if currentUrl.hostname == "www.bing.com" and currentUrl.path == "/":
                time.sleep(3)
                self.utils.tryDismissBingCookieBanner()
                with contextlib.suppress(Exception):
                    if self.utils.checkBingLogin():
                        return
            time.sleep(1)
