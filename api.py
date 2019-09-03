'''
Code for a web API written by Bierley/Lanier for a web design project in CS257 May-23-2019.
Updated over the course of 3 weeks, combines flask, PSQL, CSS, HTML along with other things.
'''
import psycopg2
import json 
import flask 
from flask import render_template
import sys
import csv
import re 
from datetime import datetime 
import math
from dbconfig import database
from dbconfig import user
from dbconfig import password






app = flask.Flask(__name__)


@app.route('/stats')
def displayStats():
	'''
	displays pictures and statistics about the database
	'''
	return render_template('stats.html')

@app.route('/')
def homepage():
	'''
	Takes you to the home page where the basic search bar is. Calls helper method get_search_results.
	'''
	search = flask.request.args.get('search')

	if search is None:
		return render_template('homepage.html')
	else:
		searchResults = get_search_results(search)
		if searchResults[0] == 'No results':
			return render_template('generalsearch_error.html')
		else:
			return render_template('generalsearch.html', search=search, results=searchResults)

def get_search_results(search_input):

	'''
	Helper method that takes in the use search input and returns a list of lists to be rendered
	using a template.
	'''
	try:
		connection = psycopg2.connect(database=database, user=user, password=password)
		cursor = connection.cursor()
		search_inputs = []
		for i in range(5):
			search_inputs.append(search_input)


		query = '''SELECT * 
                   FROM ufodata
                   WHERE LOWER(ufodata.city) = LOWER(%s)
                   OR LOWER(ufodata.state) = LOWER(%s) 
                   OR LOWER(ufodata.shape) = LOWER(%s)
                   OR LOWER(ufodata.duration) LIKE LOWER(%s)
                   OR LOWER(ufodata.summary) LIKE LOWER('%%'||%s||'%%');'''

		cursor.execute(query, tuple(search_inputs))
		queryResults = []
		for row in cursor:
			queryResults.append(row)

		if len(queryResults) == 0:
			queryResults.append('No results')
		return queryResults
	except:
		return ['ERROR']


@app.route('/nearme')
def nearme():
	'''
	return a list of lists that are the 25 closest reports to the city the user input.
	'''
	city = flask.request.args.get('search')

	if city is None:
		return render_template('nearme.html')
	else:
		cities = get_nearme(city)
		if cities == ['ERROR']:
			return render_template('nearme_error.html')
		else:
			return render_template('nearmeSearch.html', city=city, cities=cities)
	
	
def get_nearme(city):

	'''
	works by getting all reports from the data base. It then calculates the distance to each city from the city
	input by the user. The 25 closest ones are then sent to the helper method coordinatesToReoprts() to find
	the full report from the city, distance tuple.
	'''

	
	try:
		connection = psycopg2.connect(database=database, user=user, password=password)
		cursor = connection.cursor()

		query = ''' SELECT *
					FROM coordinates;'''
		cursor.execute(query,)
		cityLatLon_information = []
		for row in cursor:
			cityLatLon_information.append(row)
		cityLatLon_information = cityLatLon_information[1:]

		for item in cityLatLon_information:
			if item[0].lower() == city.lower():
				full_city_info = item
				break

		distances = []
		for result in cityLatLon_information:
		 	distance_lat = (float(full_city_info[1]) - float(result[1]))**2 
		 	distance_long = (float(full_city_info[2]) - float(result[2]))**2
		 	actual_distance = math.sqrt(distance_lat + distance_long)

		 	distances.append((result[0], actual_distance))	
		distances.sort(key=lambda x: x[1])
		distances = distances[0:25]

		reportsToReturn = coordinatesToReports(distances)
		return reportsToReturn
	except:
		return ['ERROR']

def coordinatesToReports(distances):
	'''
	Helper method turns a list of lists (city, distance) into a list of reports from the same cities. 
	'''
	connection = psycopg2.connect(database=database, user=user, password=password)
	cursor = connection.cursor()

	query = ''' SELECT *
				FROM ufodata;'''
	cursor.execute(query,)
	queryResults = []
	for row in cursor:
		queryResults.append(row)

	ufoReportsToReturn = []
	for cityInformation in distances:
		for row in queryResults:
			if cityInformation[0] == row[2]:
				ufoReportsToReturn.append(row)

	ufoReportsToReturn = list(dict.fromkeys(ufoReportsToReturn))
	ufoReportsToReturn = ufoReportsToReturn[0:25]
	
	return ufoReportsToReturn

@app.route('/advancedsearch')
def advancedSearch():
	'''
	gets the user input and sends it to the helper method get_advanced_search()
	'''

	year = flask.request.args.get('year')
	if year == '':
		year = '%%'
	elif year == None:
		pass
	else:
		year = '%%'+year[-2:]

	shape = flask.request.args.get('shape')
	if shape == '':
		shape = '%%'
	city = flask.request.args.get('city')
	if city == '':
		city = '%%'
	state = flask.request.args.get('state')
	if state == '':
		state = '%%'
	duration = flask.request.args.get('duration')
	if duration == '':
		duration = '%%'
	
	if year == None and shape == None and state == None and city == None and duration == None:
		return render_template('advancedsearch.html')
	else:
		results = get_advanced_search(year, shape, city, state, duration)
		if results[0] == 'No results':
			return render_template('advancedsearch_error.html')
		else:
			return render_template('advancedsearch_results.html', results=results)


def get_advanced_search(year, shape, city, state, duration):
	'''
	return a list of lists that satisfy all search criteria. Sorts by event_time as default.
	'''
	sortOrder = 'ASC'
	sort_by = flask.request.args.get('sort_by')
	if sort_by == 'event_time':
		sortOrder = 'DESC'

	try:
		connection = psycopg2.connect(database=database, user=user, password=password)
		cursor = connection.cursor()

		#DATE NOT YET WORKING
		#date = flask.request.args.get('date', default='%%')
		
		sort_by = 'ufodata.'+sort_by

		query = ''' SELECT *
					FROM ufodata 
					WHERE ufodata.event_date LIKE %s
					AND LOWER(ufodata.shape) LIKE LOWER(%s)
					AND LOWER(ufodata.city) LIKE LOWER(%s)
					AND LOWER(ufodata.state) LIKE LOWER(%s)
					AND LOWER(ufodata.duration) LIKE LOWER(%s)'''

		sortquery = 'ORDER BY '+sort_by+' '+sortOrder+' NULLS LAST;'
		#'ORDER BY '+sort_by+' '+sortOrder+';'
		query += sortquery
		cursor.execute(query, (year, shape, city, state, duration))
		queryResults = []
		for row in cursor:
			queryResults.append(row)

		if len(queryResults) == 0:
			queryResults.append('No results')
		return queryResults
	except:
		return ['ERROR____']



if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: {0} host port'.format(sys.argv[0]))
        print('  Example: {0} perlman.mathcs.carleton.edu 5101'.format(sys.argv[0]))
        exit()
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    app.run(host=host, port=port, debug=True)
