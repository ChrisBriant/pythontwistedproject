#export PATH=$PATH:/usr/local/share/

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
import sys

def test_set_name():
    # chrome_options = Options()
    # chrome_options.add_experimental_option("detach", True)
    # driver = webdriver.Chrome(options=chrome_options)
    driver = webdriver.Firefox()
    driver.implicitly_wait(100)
    driver.execute_script('window.open("");')
    driver.switch_to_window(driver.window_handles[-1])
    driver.get('http://localhost:3000/')


if __name__ == '__main__':
    print ('Argument List:', str(sys.argv))
    if sys.argv[1] == 'set_name':
        test_set_name()
