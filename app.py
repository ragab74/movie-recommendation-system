from flask import Flask, render_template, request
from flask_caching import Cache
import hashlib
import requests
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

def get_movie_recommendations(movie_name):
    recommendations = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    
    for i in range(1,4):
        url = f'https://www.imdb.com/list/ls068082370/?sort=user_rating,desc&st_dt=&mode=detail&page={i}'
        req = requests.get(url)
        html = req.text
        soup = BeautifulSoup(html, 'html.parser')
        div = soup.find('div', {'class': 'lister-list'})
        title = div.find_all('div', {'class': 'lister-item-content'})

        for t in title:
            name = t.a.string.strip().lower()
            ratio = fuzz.ratio(movie_name.lower(), name)
            
            if ratio > 70:
                movieID = t.a['href']
                movie_url = f'https://www.imdb.com{movieID}'

                req2 = requests.get(movie_url, headers=headers)
                html2 = req2.text
                soup2 = BeautifulSoup(html2, 'html.parser')
                director = soup2.find('div', {'class': 'ipc-metadata-list-item__content-container'})
                director_link = director.a['href']
                director_url = f'https://www.imdb.com/{director_link}'

                req3 = requests.get(director_url, headers=headers)
                html3 = req3.text
                soup3 = BeautifulSoup(html3, 'html.parser')
                kwn_for = soup3.find('div', {'data-testid': 'nm_flmg_kwn_for'})
                img_tags = kwn_for.find_all('img', {'class': 'ipc-image'})
                recommendName = kwn_for.find_all('a', class_='ipc-primary-image-list-card__title')

                for idx, movie_title in enumerate(recommendName):
                    filmName = movie_title.text.strip()
                    filmLink = "https://www.imdb.com" + movie_title['href']
                    
                    # Get the first image URL (you may modify this logic as needed)
                    img_url = img_tags[idx]['src'] if idx < len(img_tags) else ''
                    
                    recommendations.append({'title': filmName, 'link': filmLink, 'image': img_url})

    return recommendations[:4]

@app.route('/')
def index():
    return render_template('index.html')

def cache_key(movie_name):
    # Generate a unique cache key based on the movie name
    return 'recommendation_' + hashlib.md5(movie_name.encode()).hexdigest()

def get_cached_recommendations(movie_name):
    key = cache_key(movie_name)
    recommendations = cache.get(key)

    if recommendations is None:
        recommendations = get_movie_recommendations(movie_name)
        cache.set(key, recommendations, timeout=3600)

    return recommendations

@app.route('/recommend', methods=['POST'])
def recommend():
    if request.method == 'POST':
        movie_name = request.form['movie_name']
        recommendations = get_cached_recommendations(movie_name)
        return render_template('recommendations_dynamic.html', movie_name=movie_name, recommendations=recommendations)
    
if __name__ == '__main__':
    app.run(debug=True)
