from flask import render_template, request, send_file, url_for, redirect
from werkzeug import secure_filename
import os
import MySQLdb
import io
import face
import config
import trainer

def initiateGallery() :
	photoIds = []
	db = MySQLdb.connect(config.server,config.username,config.password,config.database)
	cursor = db.cursor()
	try :
		query = "Select id from photos"
		cursor.execute(query)
		result = cursor.fetchall()
	except MySQLdb.Error,e :
		print("*****ERROR : %d : %s" % (e.args[0], e.args[1]))
		return render_template('errorPage.html',message="DB Error : Could not load photos")
	for row in result :
		photoIds.append(row[0])
	return render_template('gallery.html',photoIds=photoIds)

def sendPhoto(photoId) :
	photoId = int(photoId)
	print("******** id : %d",photoId)
	db = MySQLdb.connect(config.server,config.username,config.password,config.database)
	cursor = db.cursor()
	try :
		query = "Select filename from photos where id=%s"
		args = (photoId,)
		cursor.execute(query,args)
		tuples = cursor.fetchall()
	except MySQLdb.Error,e :
		print("*****ERROR : %d : %s" % (e.args[0], e.args[1]))
		return render_template('errorPage.html',message="DB Error : Could not load photos")

	fname = tuples[0][0]
	fpath = 'static/photos/'+fname
	return send_file(fpath,attachment_filename=fname)

def addPhotos() :
	return render_template('addPhotos.html')

def allowed_file(filename) :
	allowed_extensions = ['png', 'jpg', 'jpeg']
	fname = filename.rsplit('.', 1)[1].lower()

	if fname in allowed_extensions :
		return True
	else :
		return False

def uploadPhotos() :
	if request.method != 'POST' :
		return render_template('errorPage.html',message="Invalid Http Method : Use POST method to upload photos")

	if 'file' not in request.files:
		return render_template('errorPage.html',message="No File Part Found")

	filesList = request.files.getlist('file')

	if len(filesList) == 0 :
		return render_template('errorPage.html',message="No Photos Found : Select Atleast one photo to upload")

	failedList = []

	for file in filesList :

		if file and allowed_file(file.filename):
			db = MySQLdb.connect(config.server,config.username,config.password,config.database)
			cursor = db.cursor()

			try:
				query = 'SELECT AUTO_INCREMENT FROM information_schema.TABLES WHERE TABLE_SCHEMA = "gallery" AND TABLE_NAME = "photos"'
				cursor.execute(query)
				result = cursor.fetchone()
				photoId = result[0]
			except MySQLdb.Error,e :
				print("*****ERROR : %d : %s" % (e.args[0], e.args[1]))
				return render_template('errorPage.html',message="DB Error : Could not upload photo")

			fname = str(photoId) + "_" + secure_filename(file.filename)
			fpath = 'static/photos/' + fname
			file.save(fpath)

			try :
				query = "Insert into photos (filename) values (%s)"
				args = (fname,)
				cursor.execute(query,args)
				db.commit()
			except MySQLdb.Error,e :
				db.rollback()
				print("*****ERROR : %d : %s" % (e.args[0], e.args[1]))
				return render_template('errorPage.html',message="DB Error : Could not upload photo")

			isFaceFound = face.detectFaces(fpath,photoId)
			if not isFaceFound :
				return redirect(url_for('gallery'))
			if not trainer.isTrainable() :
				return redirect(url_for('untaggedFaces'))
			face.recogniseFaces(photoId)

			try:
				query = 'select id,face_id,image_path from dataset where photo_id = %s'
				args = (photoId,)
				cursor.execute(query,args)
				result = cursor.fetchall()
			except MySQLdb.Error,e :
				print("*****ERROR : %d : %s" % (e.args[0], e.args[1]))
				return render_template('errorPage.html',message="DB Error : Could not upload photo")

			data = []
			for row in result :
				print("face_id ::::::::: ")
				print(row[1])
				if row[1] :
					try:
						query = 'select facetag from faces where id = %s'
						args = (row[1],)
						cursor.execute(query,args)
						result = cursor.fetchone()
						faceTag = result[0]
					except MySQLdb.Error,e :
						print("*****ERROR : %d : %s" % (e.args[0], e.args[1]))
						return render_template('errorPage.html',message="DB Error : Could not upload photo")

				if not row[1]:
					faceTag = "No Tag"
				data.append((faceTag,row[2]))

			return render_template("detectedFaces.html",data=data)
	return redirect(url_for('gallery'))



def renderFile(fpath) :
	return send_file(fpath)

def getIncrementValue(tablename) :
	db = MySQLdb.connect(config.server,config.username,config.password,config.database)
	cursor = db.cursor()

	incId = 0
	try:
		query = 'SELECT AUTO_INCREMENT FROM information_schema.TABLES WHERE TABLE_SCHEMA = "gallery" AND TABLE_NAME = %s'
		args = (tablename,)
		cursor.execute(query,args)
		result = cursor.fetchone()
		incId = result[0]
	except MySQLdb.Error,e :
		print("*****ERROR : %d : %s" % (e.args[0], e.args[1]))
	return incId


def getPhotosOfFace(faceId) :

	db = MySQLdb.connect(config.server,config.username,config.password,config.database)
	cursor = db.cursor()

	incId = 0
	try:
		query = 'select photo_id from photo_faces where face_id = %s'
		args = (str(faceId),)
		cursor.execute(query,args)
		result = cursor.fetchall()
	except MySQLdb.Error,e :
		print("*****ERROR : %d : %s" % (e.args[0], e.args[1]))
		return render_template('errorPage.html',message="DB Error : couldnot fetch photos of face")

	photoIdList = []
	for row in result :
		photoIdList.append(str(row[0]))

	photoIdList = list(set(photoIdList))

	return render_template("photosOfFace.html",photoIdList=photoIdList)


def showFaces() :
	db = MySQLdb.connect(config.server,config.username,config.password,config.database)
	cursor = db.cursor()

	incId = 0
	try:
		query = 'select * from faces'
		cursor.execute(query)
		result = cursor.fetchall()
	except MySQLdb.Error,e :
		print("*****ERROR : %d : %s" % (e.args[0], e.args[1]))
		return render_template('errorPage.html',message="DB Error : couldnot fetch faces")

	return render_template("faces.html",data=result)
