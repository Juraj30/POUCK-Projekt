from flask import Flask, request, jsonify, render_template, redirect, url_for

import feedparser
import requests
import sqlite3
from flask_sqlalchemy import SQLAlchemy
from create_database import Lokacija, Posao, Industrija
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.getcwd(), 'jobs.db')
db = SQLAlchemy(app)


class Lokacija(db.Model):
    __tablename__ = 'lokacije'
    geoID = db.Column(db.Integer, primary_key=True)
    geoName = db.Column(db.String)
    geoSlug = db.Column(db.String)
    poslovi = db.relationship('Posao', back_populates='lokacija')


class Posao(db.Model):
    __tablename__ = 'poslovi'
    id = db.Column(db.Integer, primary_key=True)
    naziv = db.Column(db.String)
    opis = db.Column(db.String)
    lokacija_id = db.Column(db.Integer, db.ForeignKey('lokacije.geoID'))
    lokacija = db.relationship('Lokacija', back_populates='poslovi')
    industrija_id = db.Column(db.Integer, db.ForeignKey('industrije.industryID'))
    industrija = db.relationship('Industrija', back_populates='poslovi')
    naslov = db.Column(db.String)
    link = db.Column(db.String)
    image_url = db.Column(db.String)


class Industrija(db.Model):
    __tablename__ = 'industrije'
    industryID = db.Column(db.Integer, primary_key=True)
    industryName = db.Column(db.String)
    industrySlug = db.Column(db.String)
    poslovi = db.relationship('Posao', back_populates='industrija')


@app.route('/get_locations', methods=['GET'])
def get_locations():
    response = requests.get('https://jobicy.com/api/v2/remote-jobs?get=locations')
    locations = response.json()['locations']

    return jsonify(locations)


@app.route('/tablica_industrija', methods=['GET', 'POST'])
def tablica_industrija():
    message = None

    if request.method == 'POST':

        if not preuzmi_i_spremi_industrije():
            message = 'Podaci su već u bazi podataka.'
        else:
            message = 'Podaci su uspješno preuzeti i spremljeni u bazu podataka.'

    industries = Industrija.query.all()

    response = requests.get('https://jobicy.com/api/v2/remote-jobs?get=industries')
    if response.status_code == 200:
        industries_data = response.json().get('industries', [])
    else:
        industries_data = []

    table_html = '<table>'
    table_html += '<thead><tr><th>industryID</th><th>industryName</th><th>industrySlug</th></tr></thead>'
    table_html += '<tbody>'
    for industry in industries_data:
        table_html += '<tr>'
        table_html += '<td>{}</td>'.format(industry.get('industryID', ''))
        table_html += '<td>{}</td>'.format(industry.get('industryName', ''))
        table_html += '<td>{}</td>'.format(industry.get('industrySlug', ''))
        table_html += '</tr>'
    table_html += '</tbody></table>'

    return render_template('tablica_industrija.html', table=table_html, industries=industries, message=message)


@app.route('/tablica_lokacija', methods=['GET', 'POST'])
def tablica_lokacija():
    message = None

    if request.method == 'POST':

        if not preuzmi_i_spremi_podatke():
            message = 'Podaci su već u bazi podataka.'
        else:
            message = 'Podaci su uspješno preuzeti i spremljeni u bazu podataka.'

        if request.form.get('action') == 'add':
            geoID = request.form['geoID']
            geoName = request.form['geoName']
            geoSlug = request.form['geoSlug']
            new_location = Lokacija(geoID=geoID, geoName=geoName, geoSlug=geoSlug)
            db.session.add(new_location)
            db.session.commit()

        elif request.form.get('action') == 'update':
            location_id = request.form['location_id']
            location = Lokacija.query.get(location_id)
            location.geoID = request.form['geoID']
            location.geoName = request.form['geoName']
            location.geoSlug = request.form['geoSlug']
            db.session.commit()

        elif request.form.get('action') == 'delete':
            location_id = request.form['location_id']
            location = Lokacija.query.get(location_id)
            db.session.delete(location)
            db.session.commit()

    response = requests.get('https://jobicy.com/api/v2/remote-jobs?get=locations')
    locations_data = response.json()
    locations = locations_data.get('locations', [])

    table_html = '<table>'
    table_html += '<thead><tr><th>geoID</th><th>geoName</th><th>geoSlug</th></tr></thead>'
    table_html += '<tbody>'
    for location in locations:
        table_html += '<tr>'
        table_html += '<td>{}</td>'.format(location.get('geoID', ''))
        table_html += '<td>{}</td>'.format(location.get('geoName', ''))
        table_html += '<td>{}</td>'.format(location.get('geoSlug', ''))
        table_html += '</tr>'
    table_html += '</tbody></table>'
    locations = Lokacija.query.all()
    return render_template('tablica_lokacija.html', table_html=table_html, message=message, locations=locations)


def preuzmi_i_spremi_podatke():
    response = requests.get('https://jobicy.com/api/v2/remote-jobs?get=locations')
    if response.status_code == 200:
        podaci = response.json().get('locations', [])

        conn = sqlite3.connect('jobs.db')
        cursor = conn.cursor()

        for podatak in podaci:
            geoID = podatak['geoID']
            geoName = podatak['geoName']
            geoSlug = podatak['geoSlug']
            cursor.execute("SELECT * FROM lokacije WHERE geoID=?", (geoID,))
            existing_location = cursor.fetchone()
            if not existing_location:
                cursor.execute("INSERT INTO lokacije (geoID, geoName, geoSlug) VALUES (?, ?, ?)",
                               (geoID, geoName, geoSlug))

        conn.commit()
        conn.close()
        return True
    else:
        return False


@app.route('/add_location', methods=['POST'])
def add_location():
    geoID = request.form['geoID']
    geoName = request.form['geoName']
    geoSlug = request.form['geoSlug']
    new_location = Lokacija(geoID=geoID, geoName=geoName, geoSlug=geoSlug)
    db.session.add(new_location)
    db.session.commit()
    return redirect(url_for('tablica_lokacija'))


@app.route('/update_location/<int:id>', methods=['POST'])
def update_location(id):
    location = Lokacija.query.get_or_404(id)
    location.geoID = request.form['geoID']
    location.geoName = request.form['geoName']
    location.geoSlug = request.form['geoSlug']
    db.session.commit()
    return redirect(url_for('tablica_lokacija'))


@app.route('/delete_location/<int:geoID>', methods=['POST'])
def delete_location(geoID):
    location = Lokacija.query.get_or_404(geoID)
    db.session.delete(location)
    db.session.commit()
    return redirect(url_for('tablica_lokacija'))


@app.route('/update_industrija/<int:industry_id>', methods=['POST'])
def update_industrija(industry_id):
    if request.method == 'POST':
        industry = Industrija.query.get_or_404(industry_id)
        industry.industryName = request.form['industryName']
        industry.industrySlug = request.form['industrySlug']
        db.session.commit()
    return redirect(url_for('tablica_industrija'))


@app.route('/delete_industrija/<int:industry_id>', methods=['POST'])
def delete_industrija(industry_id):
    industry = Industrija.query.get_or_404(industry_id)
    db.session.delete(industry)
    db.session.commit()
    return redirect(url_for('tablica_industrija'))


@app.route('/add_industrija', methods=['POST'])
def add_industrija():
    if request.method == 'POST':
        industry = Industrija(
            industryName=request.form['industryName'],
            industrySlug=request.form['industrySlug']
        )
        db.session.add(industry)
        db.session.commit()
    return redirect(url_for('tablica_industrija'))


@app.route('/preuzmi_industrije', methods=['POST'])
def preuzmi_industrije():
    if Industrija.query.first() is not None:
        return 'Industrije već postoje u bazi podataka.'
    else:

        if not preuzmi_i_spremi_industrije():
            return 'Došlo je do greške prilikom preuzimanja i spremanja industrija.'
        else:
            return 'Industrije su uspješno preuzete i spremljene u bazu podataka.'


def preuzmi_i_spremi_industrije():
    response = requests.get('https://jobicy.com/api/v2/remote-jobs?get=industries')
    if response.status_code == 200:
        podaci = response.json().get('industries', [])

        existing_industry = Industrija.query.filter_by(industrySlug=podaci[0]['industrySlug']).first()

        if existing_industry is None:
            for podatak in podaci:
                industryName = podatak['industryName']
                industrySlug = podatak['industrySlug']
                nova_industrija = Industrija(industryName=industryName, industrySlug=industrySlug)
                db.session.add(nova_industrija)

            db.session.commit()
            return True


        else:
            return False
    else:
        return False


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/poslovi', methods=['GET', 'POST'])
def poslovi():
    numbers = list(range(1, 51))
    locations = Lokacija.query.all()
    industries = Industrija.query.all()
    rss_feed_url = 'https://jobicy.com/?feed=job_feed'
    feed = feedparser.parse(rss_feed_url)
    rss_feed_items = []

    for entry in feed.entries:
        item = {
            'title': entry.title,
            'link': entry.link,
            'description': entry.description,
            'location': entry.job_listing_location,
            'job_type': entry.job_listing_job_type,
            'company': entry.job_listing_company,
            'image_url': entry.media_content[0]['url'] if 'media_content' in entry else None
        }
        rss_feed_items.append(item)
        existing_posao = Posao.query.filter_by(naziv=item['title'], link=item['link']).first()
        if not existing_posao:
            lokacija = Lokacija.query.filter_by(geoName=item['location']).first()
            if not lokacija:
                lokacija = Lokacija(geoName=item['location'])
                db.session.add(lokacija)

            industrija = Industrija.query.filter_by(industryName=item['company']).first()
            if not industrija:
                industrija = Industrija(industryName=item['company'])
                db.session.add(industrija)

            posao = Posao(
                naziv=item['title'],
                link=item['link'],
                opis=item['description'],
                lokacija=lokacija,
                industrija=industrija,
                naslov=item['company'],
                image_url=item['image_url']
            )

            db.session.add(posao)

    db.session.commit()
    if request.method == 'POST':
        submit_button = request.form.get('submit_button')

        if submit_button == 'Pretraži online ponudu':
            selected_location = request.form.get('location_dropdown') or request.form.get('location')
            selected_industry = request.form.get('industry_dropdown') or request.form.get('industry')
            tag = request.form.get('tag')
            selected_ads_count = request.form.get('num_ads_dropdown') or request.form.get('num_ads')
            if not selected_ads_count:
                selected_ads_count = 10

            api_url = 'https://jobicy.com/api/v2/remote-jobs'

            parameters = []

            if selected_ads_count:
                parameters.append(f'count={selected_ads_count}')

            if selected_location:
                parameters.append(f'geo={selected_location}')

            if selected_industry:
                parameters.append(f'industry={selected_industry}')

            if tag:
                parameters.append(f'tag={tag}')
            if parameters:
                api_url += '?' + '&'.join(parameters)
                response = requests.get(api_url)

                data = response.json()
                jobs = data.get('jobs', [])
                return render_template('poslovi.html', locations=locations, industries=industries,
                                       selected_location=selected_location, selected_industry=selected_industry,
                                       selected_ads_count=selected_ads_count, tag=tag, numbers=numbers, jobs=jobs,
                                       api_url=api_url)

        elif submit_button == 'Prikaži iz baze':
            poslovi = Posao.query.all()
            return render_template('poslovi.html', poslovi=poslovi, numbers=numbers, industries=industries,
                                   locations=locations, rss_feed_items=rss_feed_items)

    return render_template('poslovi.html', numbers=numbers, industries=industries, locations=locations,
                           rss_feed_items=rss_feed_items)


@app.route('/api', methods=['GET', 'POST'])
def api():
    if request.method == 'POST':
        lokacija = request.form.get('lokacija')

        lokacija_info = Lokacija.query.filter_by(geoSlug=lokacija.lower()).first()

        if lokacija_info:
            return render_template('api.html', lokacija_info=lokacija_info)

    return render_template('api.html', lokacija_info=None)


def preuzmi_i_spremi_podatke():
    if Lokacija.query.first() is None:

        response = requests.get('https://jobicy.com/api/v2/remote-jobs?get=locations')
        if response.status_code == 200:
            podaci = response.json().get('locations', [])
            for podatak in podaci:
                nova_lokacija = Lokacija(geoID=podatak['geoID'], geoName=podatak['geoName'], geoSlug=podatak['geoSlug'])
                db.session.add(nova_lokacija)
            db.session.commit()


@app.route('/preuzmi-podatke', methods=['GET'])
def preuzmi_podatke():
    if Lokacija.query.first() is not None:
        return 'Podaci već postoje u bazi podataka.'
    else:

        if not preuzmi_i_spremi_podatke():
            return 'Podaci već postoje u bazi podataka.'
        else:
            return 'Podaci su uspješno preuzeti i spremljeni u bazu podataka.'


@app.route('/preuzmi-podatke-industrije', methods=['GET'])
def preuzmi_podatke_industrije():
    if Industrija.query.first() is None:

        response = requests.get('https://jobicy.com/api/v2/remote-jobs?get=industries')
        if response.status_code == 200:
            podaci = response.json().get('industries', [])
            for podatak in podaci:
                nova_industrija = Industrija(industryName=podatak['industryName'], industrySlug=podatak['industrySlug'])
                db.session.add(nova_industrija)
            db.session.commit()
            return True
        else:
            return False
    else:
        return False


if __name__ == '__main__':
    app.run(debug=True)
