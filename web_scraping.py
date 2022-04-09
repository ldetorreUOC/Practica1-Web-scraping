from bs4 import BeautifulSoup
from selenium import webdriver
import time
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
import requests
import sys
import csv


def write_row(csv_row):
    '''
        Escribe una fila en el csv
    '''

    with open('best_films.csv', 'a') as file:
        fieldnames = [
            'titulo',
            'año',
            'duracion',
            'pais',
            'valoracion',
            'votos',
            'direccion1',
            'direccion2',
            'direccion3',
            'guion1',
            'guion2',
            'guion3',
            'produccion1',
            'produccion2',
            'produccion3',
            'genero1',
            'genero2',
            'genero3',
        ]

        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if csv_row == {'set_header': True}:
            writer.writeheader()
        else:
            writer.writerow(csv_row)


def get_profesion(child, profesion, campo_csv, csv_row):
    '''
        Recupera hasta tres personas, compañías o temas de la profesión dada (dirección, producción, guón o género)
    '''

    if child.string == profesion:
        descendants = child.next_sibling.next_sibling.descendants

        for descendant in descendants:
            if ((descendant.name == 'span' and (descendant.attrs is None or descendant.attrs == {} or descendant.attrs == {'itemprop':'name'}))
                or descendant.name == 'a' and descendant.child is None
            ):
                if csv_row[campo_csv + str(1)] == '':
                    csv_row[campo_csv + str(1)] = descendant.string
                elif csv_row[campo_csv + str(2)] == '' and csv_row[campo_csv + str(1)] != descendant.string:
                    csv_row[campo_csv + str(2)] = descendant.string
                elif csv_row[campo_csv + str(3)] == '' and csv_row[campo_csv + str(1)] != descendant.string and csv_row[campo_csv + str(2)] != descendant.string:
                    csv_row[campo_csv + str(3)] = descendant.string
                    break
        return True
    
    return False

def get_film(filmURL):
    '''
        Recupera la informaciḉon de una película dada su URL
    '''

    csv_row = {
        'titulo': '',
        'año': '',
        'duracion': '',
        'pais': '',
        'valoracion': '',
        'votos': '',
        'direccion1': '',
        'direccion2': '',
        'direccion3': '',
        'guion1': '',
        'guion2': '',
        'guion3': '',
        'produccion1': '',
        'produccion2': '',
        'produccion3': '',
        'genero1': '',
        'genero2': '',
        'genero3': ''
    }

    page = requests.get(filmURL)
    soup = BeautifulSoup(page.content)

    for dl in soup.find_all('dl'):
        if 'class' in dl.attrs and dl.attrs['class'] == ['movie-info']:
            for child in dl.children:
                if child.name == 'dt' and child.next_sibling.next_sibling.name == 'dd':
                    if child.string == 'Título original':
                        csv_row['titulo'] = child.next_sibling.next_sibling.next_element.replace('\n', '').lstrip().rstrip()
                    if child.string == 'Año':
                        csv_row['año'] = child.next_sibling.next_sibling.string
                    if child.string == 'Duración':
                        csv_row['duracion'] = ''.join(c for c in child.next_sibling.next_sibling.string if c.isdigit())
                    if child.string == 'País':
                        csv_row['pais'] = child.next_sibling.next_sibling.contents[1][1:]

                    profesion = get_profesion(child, 'Dirección', 'direccion', csv_row)
                    if not profesion:
                        profesion = get_profesion(child, 'Guion', 'guion', csv_row)
                    if not profesion:
                        profesion = get_profesion(child, 'Productora', 'produccion', csv_row)
                    if not profesion:
                        profesion = get_profesion(child, 'Género', 'genero', csv_row)


    for div in soup.find_all('div'):
        if 'id' in div.attrs and div.attrs['id'] == 'movie-rat-avg':
            csv_row['valoracion'] = div.string.replace('\n', '').replace(',', '.').lstrip().rstrip()

    for span in soup.find_all('span'):
        if 'itemprop' in span.attrs and span.attrs['itemprop'] == 'ratingCount':
            csv_row['votos'] = span.string.replace('.','')


    write_row(csv_row)

    return None


url = "https://www.filmaffinity.com/es/ranking.php?rn=ranking_fa_movies"

def get_html():
    '''
        Recupera el html de la página de las 1000 mejores películas de la historia de filmaffinity.
        Para ello, se utiliza selenium para simular la actuación de una persona y cargar las mil películas.
        Se realiza pulsando un botón similar a un botón de "cargar más" hasta que dicho botón desaparece
    '''

    # Configuramos para que no se despligegue una ventana con el navegador (se puede eliminar esta opción para ver el proceso)
    options = Options()
    options.headless = True

    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    actions = ActionChains(driver)
    driver.maximize_window()
    driver.get(url)
    page_num = 0

    string = 'button[mode="primary"]'
    # Aceptar terminos y condiciones
    while driver.find_elements_by_css_selector(string):
        time.sleep(5)
        driver.find_element_by_css_selector(string).click()


    string = 'i[class="fas fa-chevron-down"]'
    # Pulsar el botón de "cargar más" hasta que desaparezca porque se hayan cargado las 1000
    while len(driver.find_elements_by_css_selector(string)) == 2:
        time.sleep(1)
        a = driver.find_elements_by_css_selector(string)[1]
        timer = time.time()
        
        while time.time() - timer < 10:
            move = actions.key_down(Keys.DOWN)
            move.perform()

        a.click()
        page_num += 1
        print("getting page number "+str(page_num))
    
    return driver.page_source.encode('utf-8')
    

html = get_html()
soup = BeautifulSoup(html)


# Escribimos las cabeceras del CSV
write_row({'set_header': True})
links = []

# Recorremos los links de cada película
for link in soup.find_all('a',href=True):
    # Es necesario el sleep para no hacer demasiadas peticiones seguidas y evitar un bloqueo
    time.sleep(1)
    aLink=link.get('href')
    if('https://www.filmaffinity.com/es/film' in aLink and aLink not in links):
        get_film(aLink)
        links.append(aLink)