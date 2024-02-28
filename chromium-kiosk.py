#!/usr/bin/env python3
import os
import argparse
import time

from playwright.sync_api import sync_playwright
from pynput import keyboard


def init(user_data_dir):
    os.makedirs(user_data_dir, exist_ok=True)
    # Hide the playwright inspector
    os.environ['PWDEBUG'] = ''


def refresh_browser(page):
    print("Refreshing browser...")
    page.reload()


def main():
    parser = argparse.ArgumentParser(description='Launch a Chromium browser for an Application')
    parser.add_argument('--url', required=True, help='URL of the application')
    parser.add_argument('--user-data-dir', required=True, help='Path to Chromium user data directory')
    args = parser.parse_args()

    expanded_user_data_dir = os.path.expanduser(args.user_data_dir)

    if not os.path.isdir(expanded_user_data_dir):
        raise ValueError(f"Invalid user data directory: {args.user_data_dir}")

    init(expanded_user_data_dir)

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(headless=False, downloads_path=os.getcwd(),
                                                       ignore_default_args=['--enable-automation'],
                                                       args=['--disable-dev-shm-usage',
                                                             '--disable-blink-features=AutomationControlled',
                                                             '--disable-infobars',
                                                             '--start-maximized',
                                                             '--no-sandbox',
                                                             '--kiosk'],
                                                       devtools=False,
                                                       no_viewport=True,
                                                       user_data_dir=args.user_data_dir)

        page = browser.new_page()
        page.goto(args.url)

        def handle_exit():
            print('Exiting...')
            browser.close()
            exit(0)

        def for_canonical(f):
            return lambda k: f(l.canonical(k))

        hotkey = keyboard.HotKey(
            keyboard.HotKey.parse('<ctrl>+<shift>+x'), handle_exit
        )

        refresh_interval = 1000 * 30
        last_refresh_time = time.time()

        while True:
            try:
                with keyboard.Listener(
                        on_press=for_canonical(hotkey.press),
                        on_release=for_canonical(hotkey.release)
                ) as l:
                    l.join()

                page.wait_for_timeout(1000)

                current_time = time.time()
                if current_time - last_refresh_time >= refresh_interval:
                    refresh_browser(page)
                    page.goto(args.url)
                    last_refresh_time = current_time

            except KeyboardInterrupt:
                break

        print('Exiting...')


if __name__ == '__main__':
    main()
