# Selenium: automation of browser
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotVisibleException, WebDriverException
from selenium.webdriver.common.by import By


# some other imports :-)
import os
import platform
import time
import random
import requests
import atexit
from pathlib import Path
from shutil import which

# Tinderbotz: helper classes
from tinderbotz.helpers.geomatch import Geomatch
from tinderbotz.helpers.match import Match
from tinderbotz.helpers.profile_helper import ProfileHelper
from tinderbotz.helpers.preferences_helper import PreferencesHelper
from tinderbotz.helpers.geomatch_helper import GeomatchHelper
from tinderbotz.helpers.match_helper import MatchHelper
from tinderbotz.helpers.login_helper import LoginHelper
from tinderbotz.helpers.storage_helper import StorageHelper
from tinderbotz.helpers.email_helper import EmailHelper
from tinderbotz.helpers.popup_helper import PopupHelper
from tinderbotz.helpers.constants_helper import Printouts
from tinderbotz.helpers.xpaths import *
from tinderbotz.addproxy import get_proxy_extension


class Session:
    HOME_URL = "https://www.tinder.com/app/recs"

    def __init__(self, headless=False, store_session=True, proxy=None, user_data=False,
                 browser_executable_path=None):
        self.browser = None
        self.started = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        browser_path = (
            browser_executable_path
            or os.environ.get("CHROME_BINARY")
            or next((path for name in ("google-chrome", "google-chrome-stable",
                                       "chromium", "chromium-browser", "chrome")
                     if (path := which(name))), None)
        )
        if not browser_path or not Path(browser_path).is_file() or not os.access(browser_path, os.X_OK):
            raise FileNotFoundError(
                "Chrome/Chromium executavel nao encontrado. Instale o navegador no "
                "mesmo ambiente do Python (Linux no WSL) ou informe seu caminho "
                "com CHROME_BINARY ou Session(browser_executable_path=...)."
            )
        self.email = None
        self.may_send_email = False
        self.session_data = {
            "duration": 0,
            "like": 0,
            "dislike": 0,
            "superlike": 0
        }

        start_session = time.time()

        # this function will run when the session ends
        def cleanup():
            # End session duration
            seconds = int(time.time() - start_session)
            self.session_data["duration"] = seconds

            # add session data into a list of messages
            lines = []
            for key in self.session_data:
                message = "{}: {}".format(key, self.session_data[key])
                lines.append(message)

            # print out the statistics of the session
            try:
                box = self._get_msg_box(lines=lines, title="Tinderbotz")
                print(box)
            finally:
                print("Started session: {}".format(self.started))
                y = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                print("Ended session: {}".format(y))
            
            # Close browser properly
            self.close()

        # Go further with the initialisation
        # Setting some options of the browser here below

        options = webdriver.ChromeOptions()
        options.binary_location = str(browser_path)

        # Create empty profile to avoid annoying Mac Popup
        if store_session:
            if not user_data:
                user_data = f"{Path().absolute()}/chrome_profile/"
            profile_path = Path(user_data).resolve()
            profile_path.mkdir(parents=True, exist_ok=True)
            (profile_path / 'First Run').touch()
            options.add_argument(f"--user-data-dir={profile_path}")

        #options.add_argument("--start-maximized")
        for argument in ('--no-first-run', '--no-service-autorun', '--password-store=basic'):
            options.add_argument(argument)
        options.add_argument("--lang=en-GB")

        if headless:
            options.add_argument("--headless=new")

        if proxy:
            if '@' in proxy:
                parts = proxy.split('@')

                user = parts[0].split(':')[0]
                pwd = parts[0].split(':')[1]

                host = parts[1].split(':')[0]
                port = parts[1].split(':')[1]

                extension = get_proxy_extension(PROXY_HOST=host, PROXY_PORT=port, PROXY_USER=user, PROXY_PASS=pwd)
                options.add_extension(extension)
            else:
                options.add_argument(f'--proxy-server=http://{proxy}')

        # Getting the chromedriver from cache or download it from internet
        print("Getting ChromeDriver ...")
        self.browser = webdriver.Chrome(options=options)
        atexit.register(cleanup)
        # self.browser = webdriver.Chrome(options=options)
        # self.browser.set_window_size(1250, 750)

        # clear the console based on the operating system you're using
        #os.system('cls' if os.name == 'nt' else 'clear')

        # Cool banner
        print(Printouts.BANNER.value)
        time.sleep(1)

        self.started = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print("Started session: {}\n\n".format(self.started))

    # Setting a custom location
    def close(self):
        """Release the browser, including sessions cancelled before login."""
        browser, self.browser = self.browser, None
        if browser is not None:
            try:
                browser.quit()
            except WebDriverException:
                # The user may already have closed the browser window.
                pass

    def set_custom_location(self, latitude, longitude, accuracy="100%"):

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "accuracy": int(accuracy.split('%')[0])
        }

        self.browser.execute_cdp_cmd("Page.setGeolocationOverride", params)

    # This will send notification when you get a match to your email used to logged in.
    def set_email_notifications(self, boolean):
        self.may_send_email = boolean

    # NOTE: Need to be logged in for this
    def set_distance_range(self, km):
        helper = PreferencesHelper(browser=self.browser)
        helper.set_distance_range(km)

    def set_age_range(self, min, max):
        helper = PreferencesHelper(browser=self.browser)
        helper.set_age_range(min, max)

    def set_sexuality(self, type):
        helper = PreferencesHelper(browser=self.browser)
        helper.set_sexualitiy(type)

    def set_global(self, boolean):
        helper = PreferencesHelper(browser=self.browser)
        helper.set_global(boolean)

    def set_bio(self, bio):
        helper = ProfileHelper(browser=self.browser)
        helper.set_bio(bio)

    def add_photo(self, filepath):
        helper = ProfileHelper(browser=self.browser)
        helper.add_photo(filepath)

    # Actions of the session
    def login_manually(self):
        """Keep the browser open while the user completes authentication."""
        self.browser.get("https://tinder.com/?lang=en")
        while True:
            input("Conclua o login no navegador. Depois, pressione ENTER aqui "
                  "(Ctrl+C para cancelar): ")
            if self._is_logged_in():
                return
            print("Login ainda nao identificado. A janela continuara aberta para tentar novamente.")

    def login_using_google(self, email, password):
        self.email = email
        if not self._is_logged_in():
            helper = LoginHelper(browser=self.browser)
            helper.login_by_google(email, password)
            time.sleep(5)
        if not self._is_logged_in():
            print('Manual interference is required.')
            input('press ENTER to continue')

    def login_using_facebook(self, email, password):
        self.email = email
        if not self._is_logged_in():
            helper = LoginHelper(browser=self.browser)
            helper.login_by_facebook(email, password)
            time.sleep(5)
        if not self._is_logged_in():
            print('Manual interference is required.')
            input('press ENTER to continue')

    def login_using_sms(self, country, phone_number):
        if not self._is_logged_in():
            helper = LoginHelper(browser=self.browser)
            helper.login_by_sms(country, phone_number)
            time.sleep(5)
        if not self._is_logged_in():
            print('Manual interference is required.')
            input('press ENTER to continue')

    def store_local(self, match):
        if isinstance(match, Match):
            filename = 'matches'
        elif isinstance(match, Geomatch):
            filename = 'geomatches'
        else:
            print("type of match is unknown, storing local impossible")
            print("Crashing in 3.2.1... :)")
            assert False

        # store its images
        for url in match.image_urls:
            hashed_image = StorageHelper.store_image_as(url=url, directory='data/{}/images'.format(filename))
            match.images_by_hashes.append(hashed_image)

        # store its userdata
        StorageHelper.store_match(match=match, directory='data/{}'.format(filename), filename=filename)

    def like(self, amount=1, ratio='100%', sleep=1, randomize_sleep = True):
        
        initial_sleep = sleep
        ratio = float(ratio.split('%')[0]) / 100

        if self._is_logged_in():
            helper = GeomatchHelper(browser=self.browser)
            amount_liked = 0
            # handle one time up front, from then on check after every action instead of before
            self._handle_potential_popups()
            print("\nLiking profiles started.")
            while amount_liked < amount:
                self._handle_potential_popups()
                # randomize sleep
                if randomize_sleep:
                    sleep = random.uniform(0.5, 2.3) * initial_sleep
                if random.random() <= ratio:
                    if helper.like():
                        amount_liked += 1
                        # update for stats after session ended
                        self.session_data['like'] += 1
                        print(f"{amount_liked}/{amount} liked, sleep: {sleep}")
                else:
                    helper.dislike()
                    # update for stats after session ended
                    self.session_data['dislike'] += 1

                self._handle_potential_popups()
                time.sleep(sleep)

            self._print_liked_stats()

    def dislike(self, amount=1):
        if self._is_logged_in():
            helper = GeomatchHelper(browser=self.browser)
            for _ in range(amount):
                self._handle_potential_popups()
                helper.dislike()

                # update for stats after session ended
                self.session_data['dislike'] += 1
                #time.sleep(1)
            self._print_liked_stats()

    def superlike(self, amount=1):
        if self._is_logged_in():
            helper = GeomatchHelper(browser=self.browser)
            for _ in range(amount):
                self._handle_potential_popups()
                helper.superlike()
                # update for stats after session ended
                self.session_data['superlike'] += 1
                time.sleep(1)
            self._print_liked_stats()

    def get_geomatch(self, quickload=True):
        if self._is_logged_in():
            helper = GeomatchHelper(browser=self.browser)
            self._handle_potential_popups()

            name = None
            attempts = 0
            max_attempts = 3
            while not name and attempts < max_attempts:
                attempts += 1
                name = helper.get_name()
                self._handle_potential_popups() # Popup handling on first geomatch
                time.sleep(1)

            age = helper.get_age()

            bio, passions, lifestyle, basics, anthem, looking_for = helper.get_bio_and_passions()
            image_urls = helper.get_image_urls(quickload)
            instagram = helper.get_insta(bio)
            rowdata = helper.get_row_data()
            work = rowdata.get('work')
            study = rowdata.get('study')
            home = rowdata.get('home')
            distance = rowdata.get('distance')
            gender = rowdata.get('gender')

            return Geomatch(name=name, age=age, work=work, gender=gender, study=study, home=home, distance=distance,
                            bio=bio, passions=passions, lifestyle=lifestyle, basics=basics, anthem=anthem, looking_for=looking_for, image_urls=image_urls, instagram=instagram)

    def get_chat_ids(self, new=True, messaged=True):
        if self._is_logged_in():
            helper = MatchHelper(browser=self.browser)
            self._handle_potential_popups()
            return helper.get_chat_ids(new, messaged)

    def get_new_matches(self, amount=100000, quickload=True):
        if self._is_logged_in():
            helper = MatchHelper(browser=self.browser)
            self._handle_potential_popups()
            return helper.get_new_matches(amount, quickload)

    def get_messaged_matches(self, amount=100000, quickload=True):
        if self._is_logged_in():
            helper = MatchHelper(browser=self.browser)
            self._handle_potential_popups()
            return helper.get_messaged_matches(amount, quickload)

    def send_message(self, chatid, message):
        if self._is_logged_in():
            helper = MatchHelper(browser=self.browser)
            self._handle_potential_popups()
            helper.send_message(chatid, message)

    def send_gif(self, chatid, gifname):
        if self._is_logged_in():
            helper = MatchHelper(browser=self.browser)
            self._handle_potential_popups()
            helper.send_gif(chatid, gifname)

    def send_song(self, chatid, songname):
        if self._is_logged_in():
            helper = MatchHelper(browser=self.browser)
            self._handle_potential_popups()
            helper.send_song(chatid, songname)

    def send_socials(self, chatid, media):
        if self._is_logged_in():
            helper = MatchHelper(browser=self.browser)
            self._handle_potential_popups()
            helper.send_socials(chatid, media)

    def unmatch(self, chatid):
        if self._is_logged_in():
            helper = MatchHelper(browser=self.browser)
            self._handle_potential_popups()
            helper.unmatch(chatid)

    # Utilities
    def _handle_potential_popups(self):
        def notify_match():
            if getattr(self, 'may_send_email', False):
                try:
                    EmailHelper.send_mail_match_found(self.email)
                except Exception as error:
                    print("Could not send match notification: {}".format(error))

        helper = PopupHelper(self.browser, on_match=notify_match)
        while not helper.dismiss():
            input("Popup sem opcao de fechar reconhecida. Feche-o no navegador e "
                  "pressione ENTER para continuar (Ctrl+C para cancelar): ")
        return None

    def _is_logged_in(self):
        # make sure tinder website is loaded for the first time
        if not "tinder" in self.browser.current_url:
            # enforce english language
            self.browser.get("https://tinder.com/?lang=en")
            time.sleep(1.5)

        if "tinder.com/app/" in self.browser.current_url:
            return True
        else:
            print("User is not logged in yet.\n")
            return False

    def _get_msg_box(self, lines, indent=1, width=None, title=None):
        """Print message-box with optional title."""
        space = " " * indent
        if not width:
            width = max(map(len, lines))
        box = f'/{"=" * (width + indent * 2)}\\\n'  # upper_border
        if title:
            box += f'|{space}{title:<{width}}{space}|\n'  # title
            box += f'|{space}{"-" * len(title):<{width}}{space}|\n'  # underscore
        box += ''.join([f'|{space}{line:<{width}}{space}|\n' for line in lines])
        box += f'\\{"=" * (width + indent * 2)}/'  # lower_border
        return box

    def _print_liked_stats(self):
        likes = self.session_data['like']
        dislikes = self.session_data['dislike']
        superlikes = self.session_data['superlike']

        if superlikes > 0:
            print(f"You've superliked {self.session_data['superlike']} profiles during this session.")
        if likes > 0:
            print(f"You've liked {self.session_data['like']} profiles during this session.")
        if dislikes > 0:
            print(f"You've disliked {self.session_data['dislike']} profiles during this session.")

