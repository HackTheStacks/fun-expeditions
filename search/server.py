import csv
from flask import Flask
from flask import render_template, request, jsonify, redirect
from database import load_people, load_keywords, load_expeditions, Expedition
from collections import defaultdict

import sys
# sys.setdefaultencoding() does not exist, here!
reload(sys)  # Reload does the trick!
sys.setdefaultencoding('UTF8')

app = Flask(__name__)
app.debug = True
people = load_people()
keywords = load_keywords()
expeditions = load_expeditions()

relations = defaultdict(set)
for person in people.values():
    for link in person.links:
        relations[link].add(person)


@app.route('/')
def home():
    return render_template('home.html', people=people)


def treat(html, word1):
    word2 = word1.lower()
    word3 = word1.title()
    word4 = word1.upper()
    return html\
        .replace(word1, '<span class="highlight">{}</span>'.format(word1))\
        .replace(word2, '<span class="highlight">{}</span>'.format(word2))\
        .replace(word3, '<span class="highlight">{}</span>'.format(word3))\
        .replace(word4, '<span class="highlight">{}</span>'.format(word4))


@app.route('/people')
def search_people():
    query = request.args.get('query').lower()
    results = []
    history = set()
    for expedition in expeditions.values():
        name = expedition.name.lower()
        if query in name:
            results.append(render_template('expedition.html', expedition=expedition, links=relations.get(expedition.xeac_id, set())))
            history.add(expedition.xeac_id)
    for person in people.values():
        name = person.name.lower()
        if query in name:
            results.append(render_template('person.html', person=person, expeditions=expeditions))
            history.add(person.xeac_id)
    for keyword in keywords:
        if query in keyword.lower():
            for xeac_id in keywords[keyword]:
                if xeac_id not in history and xeac_id in people:
                    person = people[xeac_id]
                    history.add(xeac_id)
                    results.append(treat(render_template('person.html', person=person, expeditions=expeditions), keyword))
    return jsonify({"results": results})


@app.route('/expedition/new', methods=['GET'])
def add_expedition():
    return render_template("add.html")


@app.route('/expedition/new', methods=['POST'])
def add_expedition_request():
    expedition_name = request.form.get('ename')
    expedition_desc = request.form.get('desc')
    start_year = request.form.get('syear')
    end_year = request.form.get('eyear')
    fieldnote_title = request.form.get('ftitle')
    fieldnote_desc = request.form.get('fdesc')
    fieldnote_location = request.form.get('flocation')
    fieldnote_author = request.form.get('fauthor')
    expedition_hash = abs(hash((expedition_name, expedition_desc, fieldnote_title))) % 10000000
    expedition_id = 'expedition_%010d' % expedition_hash
    expedition = Expedition(expedition_id, expedition_name, expedition_desc, [], fieldnote_location,
                            '{} - {}'.format(start_year, end_year), '{}: {}'.format(fieldnote_author, fieldnote_desc))
    expeditions[expedition_id] = expedition
    with open("output/expedition_%010d.tsv" % expedition_hash, 'wb') as dst:
        writer = csv.writer(dst, delimiter='\t')
        for key in request.form.keys():
            value = request.form.get(key)
            writer.writerow((key, value))
    return redirect('/expedition/new')

if __name__ == '__main__':
    app.run()
