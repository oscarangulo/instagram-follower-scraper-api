import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service

def save_credentials(username, password):
    with open('credentials.txt', 'w') as file:
        file.write(f"{username}\n{password}")


def load_credentials():
    if not os.path.exists('credentials.txt'):
        return None

    with open('credentials.txt', 'r') as file:
        lines = file.readlines()
        if len(lines) >= 2:
            return lines[0].strip(), lines[1].strip()

    return None


def prompt_credentials():
    username = input("Enter your Instagram username: ")
    password = input("Enter your Instagram password: ")
    save_credentials(username, password)
    return username, password


def login(bot, username, password):
    bot.get('https://www.instagram.com/accounts/login/')
    print("[Info] - Page loaded, waiting for form...")
    time.sleep(3)  # Reducir tiempo inicial de espera

    # Check if cookies need to be accepted (múltiples posibles selectores)
    # Usar timeout muy corto para no quedarse pegado
    print("[Info] - Checking for cookie consent (quick check)...")
    cookie_found = False
    cookie_selectors = [
        (By.XPATH, "//button[contains(text(), 'Aceptar')]"),
        (By.XPATH, "//button[contains(text(), 'Accept')]"),
        (By.XPATH, "//button[contains(text(), 'Allow')]"),
        (By.XPATH, "//button[contains(text(), 'Permitir')]"),
        (By.XPATH, "/html/body/div[4]/div/div/div[3]/div[2]/button"),
    ]
    
    # Intentar encontrar cookies rápidamente (máximo 2 segundos total)
    for selector_type, selector in cookie_selectors:
        try:
            element = WebDriverWait(bot, 0.5).until(EC.element_to_be_clickable((selector_type, selector)))
            if element and element.is_displayed():
                element.click()
                print("[Info] - Cookie consent accepted")
                time.sleep(1)
                cookie_found = True
                break
        except (TimeoutException, NoSuchElementException):
            continue
    
    if not cookie_found:
        print("[Info] - No cookie consent popup found (continuing...)")

    print("[Info] - Logging in...")
    print("[Info] - Waiting for login form to load...")
    
    # Esperar a que los campos de entrada estén disponibles con múltiples selectores
    username_input = None
    password_input = None
    
    # Selectores priorizados para español (basado en la imagen)
    username_selectors = [
        (By.CSS_SELECTOR, "input[name='username']"),
        (By.XPATH, "//input[@name='username']"),
        (By.CSS_SELECTOR, "input[aria-label*='usuario']"),
        (By.CSS_SELECTOR, "input[aria-label*='correo']"),
        (By.CSS_SELECTOR, "input[aria-label*='celular']"),
        (By.CSS_SELECTOR, "input[type='text']"),
        (By.XPATH, "//input[@type='text']"),
    ]
    
    password_selectors = [
        (By.CSS_SELECTOR, "input[name='password']"),
        (By.XPATH, "//input[@name='password']"),
        (By.CSS_SELECTOR, "input[aria-label*='Contraseña']"),
        (By.CSS_SELECTOR, "input[type='password']"),
        (By.XPATH, "//input[@type='password']"),
    ]
    
    # Buscar campo de username con logging
    print("[Info] - Looking for username field...")
    for selector_type, selector in username_selectors:
        try:
            print(f"[Debug] - Trying selector: {selector}")
            username_input = WebDriverWait(bot, 5).until(EC.presence_of_element_located((selector_type, selector)))
            if username_input:
                print(f"[Info] - Username field found with: {selector}")
                break
        except (TimeoutException, NoSuchElementException) as e:
            print(f"[Debug] - Selector failed: {selector}")
            continue
    
    # Buscar campo de password con logging
    print("[Info] - Looking for password field...")
    for selector_type, selector in password_selectors:
        try:
            print(f"[Debug] - Trying selector: {selector}")
            password_input = WebDriverWait(bot, 5).until(EC.presence_of_element_located((selector_type, selector)))
            if password_input:
                print(f"[Info] - Password field found with: {selector}")
                break
        except (TimeoutException, NoSuchElementException) as e:
            print(f"[Debug] - Selector failed: {selector}")
            continue
    
    if not username_input:
        print("[Error] - Username field not found. Current page source snippet:")
        try:
            page_source = bot.page_source[:500]
            print(page_source)
        except:
            pass
        raise Exception("No se pudo encontrar el campo de usuario. Instagram puede haber cambiado su estructura.")
    
    if not password_input:
        print("[Error] - Password field not found.")
        raise Exception("No se pudo encontrar el campo de contraseña. Instagram puede haber cambiado su estructura.")
    
    # Esperar a que sean interactuables (más flexible que clickeable)
    print("[Info] - Waiting for fields to be interactive...")
    try:
        WebDriverWait(bot, 5).until(EC.element_to_be_clickable(username_input))
        WebDriverWait(bot, 5).until(EC.element_to_be_clickable(password_input))
    except:
        print("[Warning] - Fields may not be fully clickable, but attempting to fill them anyway...")
    
    print("[Info] - Filling username...")
    username_input.clear()
    username_input.send_keys(username)
    time.sleep(0.5)
    
    print("[Info] - Filling password...")
    password_input.clear()
    password_input.send_keys(password)
    time.sleep(1)

    # Intentar múltiples selectores para el botón de login (priorizando español)
    # Instagram ahora usa divs con role="button" en lugar de elementos button
    login_button = None
    login_selectors = [
        # Selectores para div con role="button" (nueva estructura de Instagram)
        (By.XPATH, "//div[@role='button' and @aria-label='Iniciar sesión']"),
        (By.XPATH, "//div[@role='button' and contains(@aria-label, 'Iniciar sesión')]"),
        (By.XPATH, "//div[@role='button' and @aria-label='Log in']"),
        (By.XPATH, "//div[@role='button' and contains(@aria-label, 'Log in')]"),
        # Selectores por texto dentro de divs (para la estructura anidada)
        (By.XPATH, "//div[@role='button']//span[contains(text(), 'Iniciar sesión')]"),
        (By.XPATH, "//div[@role='button']//span[contains(text(), 'Log in')]"),
        (By.XPATH, "//div[contains(@class, 'wbloks_1') and @role='button']"),
        # Selectores tradicionales (por si acaso)
        (By.XPATH, "//button[contains(text(), 'Iniciar sesión')]"),
        (By.XPATH, "//button[normalize-space(text())='Iniciar sesión']"),
        (By.CSS_SELECTOR, "button[type='submit']"),
        (By.XPATH, "//button[@type='submit']"),
        (By.XPATH, "//button[contains(text(), 'Log in')]"),
        (By.XPATH, "//div[contains(text(), 'Iniciar sesión')]"),
        (By.XPATH, "//div[contains(text(), 'Log in')]"),
        (By.CSS_SELECTOR, "button._acan._acap._acas._aj1-"),
        (By.CSS_SELECTOR, "button[class*='_acan']"),
        (By.XPATH, "//button[@type='submit' and contains(@class, 'button')]"),
        (By.XPATH, "//form//button[@type='submit']"),
        (By.CSS_SELECTOR, "form button[type='submit']"),
    ]
    
    print("[Info] - Looking for login button...")
    for selector_type, selector in login_selectors:
        try:
            print(f"[Debug] - Trying login button selector: {selector}")
            login_button = WebDriverWait(bot, 3).until(EC.presence_of_element_located((selector_type, selector)))
            if login_button:
                # Verificar si está visible (para divs con role="button", is_enabled puede no funcionar)
                try:
                    is_enabled = login_button.is_enabled() if login_button.tag_name == 'button' else True
                except:
                    is_enabled = True
                
                if login_button.is_displayed() and is_enabled:
                    print(f"[Info] - Login button found with selector: {selector}")
                    break
                else:
                    print(f"[Debug] - Button found but not visible/enabled: {selector}")
                    login_button = None
        except (TimeoutException, NoSuchElementException):
            print(f"[Debug] - Login button selector failed: {selector}")
            continue
    
    if not login_button:
        # Último intento: buscar cualquier botón o div con role="button" dentro del formulario
        print("[Info] - Trying fallback method for login button...")
        try:
            # Buscar botones tradicionales
            buttons = bot.find_elements(By.XPATH, "//form//button")
            for btn in buttons:
                if btn.is_displayed() and btn.is_enabled():
                    login_button = btn
                    print("[Info] - Login button found using fallback method (button)")
                    break
            
            # Si no se encontró, buscar divs con role="button"
            if not login_button:
                div_buttons = bot.find_elements(By.XPATH, "//form//div[@role='button']")
                for btn in div_buttons:
                    if btn.is_displayed():
                        # Verificar que contenga el texto "Iniciar sesión" o "Log in"
                        text = btn.text.lower()
                        if 'iniciar sesión' in text or 'log in' in text or 'iniciar' in text:
                            login_button = btn
                            print("[Info] - Login button found using fallback method (div with role=button)")
                            break
        except Exception as e:
            print(f"[Debug] - Fallback method failed: {e}")
            pass
    
    if login_button:
        print("[Info] - Clicking login button...")
        try:
            # Intentar hacer scroll al botón si es necesario
            bot.execute_script("arguments[0].scrollIntoView(true);", login_button)
            time.sleep(0.5)
            login_button.click()
            print("[Info] - Login button clicked, waiting for authentication...")
        except Exception as e:
            print(f"[Warning] - Error clicking button, trying JavaScript click: {e}")
            bot.execute_script("arguments[0].click();", login_button)
        
        # Esperar con verificación periódica
        print("[Info] - Waiting for authentication (max 15 seconds)...")
        for i in range(15):
            time.sleep(1)
            current_url = bot.current_url
            if '/accounts/login' not in current_url:
                print(f"[Info] - Redirect detected after {i+1} seconds. Login may be successful.")
                break
            if i % 3 == 0:
                print(f"[Info] - Still waiting... ({i+1}/15 seconds)")
        
        # Verificar si hay algún popup de "Save Your Login Info" o similar
        popup_selectors = [
            (By.XPATH, "//button[contains(text(), 'Not Now')]"),
            (By.XPATH, "//button[contains(text(), 'Ahora no')]"),
            (By.XPATH, "//button[contains(text(), 'Save Info')]"),
            (By.XPATH, "//button[contains(text(), 'Guardar información')]"),
            (By.XPATH, "//div[contains(text(), 'Not Now')]"),
        ]
        
        for selector_type, selector in popup_selectors:
            try:
                popup_button = WebDriverWait(bot, 3).until(EC.element_to_be_clickable((selector_type, selector)))
                if popup_button and popup_button.is_displayed():
                    popup_button.click()
                    print("[Info] - Dismissed 'Save Login Info' popup")
                    time.sleep(2)
                    break
            except (TimeoutException, NoSuchElementException):
                continue
                
        # Verificar si hay popup de notificaciones
        notif_selectors = [
            (By.XPATH, "//button[contains(text(), 'Not Now')]"),
            (By.XPATH, "//button[contains(text(), 'Ahora no')]"),
            (By.XPATH, "//button[contains(text(), 'Turn on Notifications')]"),
            (By.XPATH, "//button[contains(text(), 'Activar notificaciones')]"),
        ]
        
        for selector_type, selector in notif_selectors:
            try:
                notif_button = WebDriverWait(bot, 3).until(EC.element_to_be_clickable((selector_type, selector)))
                if notif_button and notif_button.is_displayed():
                    notif_button.click()
                    print("[Info] - Dismissed notifications popup")
                    time.sleep(2)
                    break
            except (TimeoutException, NoSuchElementException):
                continue
        
        # Verificar que el login fue exitoso (con timeout más corto)
        print("[Info] - Verifying login success...")
        try:
            # Esperar máximo 5 segundos para verificar el login
            WebDriverWait(bot, 5).until(
                lambda driver: 'instagram.com' in driver.current_url and '/accounts/login' not in driver.current_url
            )
            print("[Info] - Login successful! Redirected from login page.")
        except TimeoutException:
            # Verificar manualmente la URL actual
            current_url = bot.current_url
            if '/accounts/login' not in current_url:
                print("[Info] - Login appears successful (not on login page).")
            else:
                print("[Warning] - Still on login page. Login may have failed, but continuing...")
        except Exception as e:
            print(f"[Warning] - Could not verify login success: {e}. Continuing anyway...")
    else:
        raise Exception("No se pudo encontrar el botón de login. Instagram puede haber cambiado su estructura.")


def scrape_followers(bot, username, user_input):
    bot.get(f'https://www.instagram.com/{username}/')
    time.sleep(3.5)
    WebDriverWait(bot, TIMEOUT).until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/followers')]"))).click()
    time.sleep(2)
    print(f"[Info] - Scraping followers for {username}...")

    users = set()

    while len(users) < user_input:
        followers = bot.find_elements(By.XPATH, "//a[contains(@href, '/')]")

        for i in followers:
            if i.get_attribute('href'):
                users.add(i.get_attribute('href').split("/")[3])
            else:
                continue

        ActionChains(bot).send_keys(Keys.END).perform()
        time.sleep(1)

    users = list(users)[:user_input]  # Trim the user list to match the desired number of followers

    print(f"[Info] - Saving followers for {username}...")
    with open(f'{username}_followers.txt', 'a') as file:
        file.write('\n'.join(users) + "\n")


def scrape():
    credentials = load_credentials()

    if credentials is None:
        username, password = prompt_credentials()
    else:
        username, password = credentials

    user_input = int(input('[Required] - How many followers do you want to scrape (100-2000 recommended): '))

    usernames = input("Enter the Instagram usernames you want to scrape (separated by commas): ").split(",")

    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--log-level=3")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    options.add_argument("--lang=es-ES,es")
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0,
        "profile.managed_default_content_settings.images": 1
    })
    # Usar un User-Agent más actualizado y realista
    mobile_emulation = {
        "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
    }
    options.add_experimental_option("mobileEmulation", mobile_emulation)


    bot = webdriver.Chrome(service=service, options=options)
    bot.set_page_load_timeout(30) # Timeout de carga de página
    bot.implicitly_wait(2) # Espera implícita reducida a 2 segundos para evitar bloqueos

    login(bot, username, password)

    for user in usernames:
        user = user.strip()
        scrape_followers(bot, user, user_input)

    bot.quit()


if __name__ == '__main__':
    TIMEOUT = 15
    scrape()
