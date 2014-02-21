#!/usr/bin/env python
# anime.py
# an anime pre-processor
# Process files/folders so that sickbeard/nzbdrone
# can properly recognize and further process files/folders

# enter any series here that you want to be processed
# sorted by seasons

seriesList = {
	'space dandy' : 
		{
		1 : list(range(1,26))
		},
	'kill la kill' :
		{
		1 : list(range(1,24))
		},
	'attack on titan' :
		{
		1 : list(range(1, 25))
		},
	'space brothers' :
		{
		1 : list(range(1, 51)),
		2 : list(range(1, 51))
		}
	}

'''
TODO LIST:
	- change series name to custom names
	- if multiple mkv files, check sizes for non-sample
	- clean up code
	- try to break it
'''

import re
import os
import sys
import glob
import shutil
import logging
import difflib

def cleanFolderName(folder):
	''' Remove brackets, parenthesis, and information in them.'''
	return re.sub(r'(\(.*?\))|(\[.*?\])', '', folder).replace('_', ' ').strip().lower()

def getRatio(series, name):
	'''Calculate levenshtein distance and return int of distance.'''
	series = cleanFolderName(series)
	lRatio = difflib.SequenceMatcher(None, series, name).ratio()
	return int(round(lRatio * 100, 1))

def getEpisodeNum(cleanName):
	'''Get episode number from folder name. This might get shitty and ugly.
	Eventually parse seasons here and return full Season & Episode.
	e.g. instead of 06<int> return S01E06<str>'''
	try:
		return int(re.findall('\d+', cleanName)[0])
	except IndexError:
		logger.error('Unable to parse episode number from file/folder name.')
		return False

def getSeason(series, episode):
	for i in xrange(1, len(seriesList[series])+1):
		if episode in seriesList[series][i]:
			return 'S%02iE%02i' % (i, episode)

def findFolderMatches(path, seriesList):
	'''Get list of files and compares all folders to series names.
	If match is above threshold, add a dictionary to list and return the list.'''

	ratioThreshold = 70
	folders = os.listdir(path)
	found = list()

	for series in seriesList:
		for folder in folders:
			ratio = getRatio(folder, series)
			if ratio >= ratioThreshold:
				cleanFolder = cleanFolderName(folder)
				episode = getEpisodeNum(cleanFolder)
				season = getSeason(series, episode)
				found.append({
					'folder' : folder,
					'fullPath' : os.path.join(path, folder),
					'series' : series,
					'newName' : ' '.join([series, season]),
					'episode' : episode,
					'clean' : cleanFolder,
					'ratio' : ratio
					})
	return found

def processFiles(meta, src, dst):
	''' Rename all the files in the folder and then move said folder.'''
	# get (non-hidden) files
	os.chdir(meta['fullPath'])
	files = list()
	for item in os.listdir(os.getcwd()):
		if os.path.isfile(item):
			if not item.startswith('.'):
				files.append(item)

	# rename files
	for currentFile in files:
		extensionList = currentFile.split('.')
		if len(extensionList) == 3:
			extension = '.'.join(extensionList[-2:])
		else:
			extension = extensionList[-1]
		destination = '.'.join([meta['newName'], extension])
		if os.path.exists(destination):
			logger.critical('Destination file (%s) already exists.' % (destination))
			sys.exit()
		logger.info('Moving %s to %s' % (currentFile, destination))
		if not args.debug:
			os.rename(currentFile, destination)

	# process folder
	os.chdir(src)
	newPath = os.path.join(dst, meta['newName'])
	if not args.debug:
		shutil.move(meta['fullPath'], newPath)
	logger.info('Moving %s to %s' % (meta['fullPath'], newPath))

def main(src, dst):
	matches = findFolderMatches(src, seriesList)
	for i in matches:
		logger.info('%s is %s%% match for "%s".' % (i['folder'], i['ratio'], i['series']))
		processFiles(i, source, dest)

if __name__ == "__main__":
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument('-d', '--debug', help='Show information only. Do not process files.',
		action='store_true')
	args = parser.parse_args()
	# make argparse args global because I'm lazy as fuuuuuck
	globals().update(vars(args))

	# setup logging
	logging.basicConfig(level=logging.INFO)
	logger = logging.getLogger('anime')
	handler = logging.FileHandler('anime.log')
	handler.setLevel(logging.INFO)
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	handler.setFormatter(formatter)
	logger.addHandler(handler)

	source = os.path.abspath(r'/root/source/')
	dest = os.path.abspath(r'C:\destination\')
	for folder in [source, dest]:
		if not os.path.exists(folder):
			logging.critical('%s folder does not exist.' % folder)
			sys.exit()
	main(source, dest)