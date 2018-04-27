from flask import render_template, request, send_file, url_for, redirect
import trainer
import numpy as np
import cv2
import config
import MySQLdb
import gallery

def tagFaces() :

	if request.method != 'POST' :
		return render_template('errorPage.html',message="Invalid Http Method : Use POST method to upload photos")

	db = MySQLdb.connect(config.server,config.username,config.password,config.database)
	cursor = db.cursor()

	try:
		query = 'Select id,photo_id,image_path from dataset where face_id is NULL'
		cursor.execute(query)
		tuples = cursor.fetchall()
	except :
		return render_template('errorPage.html',message="DB Error : Could not tag faces")

	for row in tuples :
		print(row[0])
		print(request.form.get(str(row[0])))
		if not request.form.get(str(row[0])) :
			continue
		name = request.form.get(str(row[0]))
		if name=="" :
			continue
		if 'ID' in name :
			faceId = name.split('-')[1].strip()
			faceId = faceId[2:]

			try:
				query = 'Update dataset set face_id = %s where id = %s'
				args = (str(faceId),row[0])
				cursor.execute(query,args)
				db.commit()
			except :
				db.rollback()
				return render_template('errorPage.html',message="DB Error : Could not tag faces")

			try:
				query = 'Insert into photo_faces (photo_id,face_id) values(%s,%s)'
				args = (str(row[1]),faceId)
				cursor.execute(query,args)
				db.commit()
			except :
				db.rollback()
				return render_template('errorPage.html',message="DB Error : Could not tag faces")
		else :

			faceId = gallery.getIncrementValue('faces');

			try:
				query = 'Insert into faces (facetag,thumbnail) values(%s,%s)'
				args = (name,row[2])
				cursor.execute(query,args)
				db.commit()
			except MySQLdb.Error,e:
				db.rollback()
				print("*****ERROR : %d : %s" % (e.args[0], e.args[1]))
				return render_template('errorPage.html',message="DB Error : Could not tag faces")

			try:
				query = 'Update dataset set face_id = %s where id = %s'
				args = (str(faceId),row[0])
				cursor.execute(query,args)
				db.commit()
			except :
				db.rollback()
				return render_template('errorPage.html',message="DB Error : Could not tag faces")

			try:
				query = 'Insert into photo_faces (photo_id,face_id) values(%s,%s)'
				args = (str(row[1]),faceId)
				cursor.execute(query,args)
				db.commit()
			except :
				db.rollback()
				return render_template('errorPage.html',message="DB Error : Could not tag faces")

	return redirect(url_for('untaggedFaces'))


def detectFaces(filePath,photoId) :
	face_cascade = cv2.CascadeClassifier(config.pathToCascades)

	img = cv2.imread(filePath)
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

	faces = face_cascade.detectMultiScale(gray, 1.4, 6)
	count=1;

	db = MySQLdb.connect(config.server,config.username,config.password,config.database)
	cursor = db.cursor()

	if len(faces) == 0 :
		return False

	for (x,y,w,h) in faces:
		cropimg = img[y:y+h,x:x+w]
		cropimgpath = "static/dataset/"+str(photoId)+"_"+str(count)+".jpg"
		cv2.imwrite(cropimgpath,cropimg)

		try:
			query = 'Insert Into dataset (photo_id,index_id,image_path) values(%s,%s,%s)'
			args = (photoId, count, cropimgpath)
			cursor.execute(query,args)
			db.commit()
		except :
			db.rollback()
			print("*****ERROR ")
		count +=1
	return True

def untaggedFaces() :

	db = MySQLdb.connect(config.server,config.username,config.password,config.database)
	cursor = db.cursor()

	try:
		query = 'Select id,image_path from dataset where face_id is NULL'
		cursor.execute(query)
		tuples = cursor.fetchall()
	except :
		return render_template('errorPage.html',message="DB Error : Could not fetch untagged photos")

	try:
		query = 'Select id,facetag from faces'
		cursor.execute(query)
		taggedFaces = cursor.fetchall()
	except :
		return render_template('errorPage.html',message="DB Error : Could not fetch untagged photos")

	return render_template('untaggedFaces.html',data=tuples,taggedFaces=taggedFaces)

def recogniseFaces(photoId) :

	db = MySQLdb.connect(config.server,config.username,config.password,config.database)
	cursor = db.cursor()

	print("EE sala cup namde")

	try:
		query = 'Select id,image_path from dataset where face_id is NULL AND photo_id = %s'
		args = (photoId,)
		cursor.execute(query,args)
		tuples = cursor.fetchall()
	except :
		return render_template('errorPage.html',message="DB Error : Could not fetch untagged photos")

	featureVector,dataPoints, faceIdList = trainer.trainAlgorithm();
	for row in tuples :
		faceId = trainer.classifyFace(row[1],featureVector,dataPoints,faceIdList)
		if faceId :
			print(photoId)
			print(faceId)
			try:
				query = 'Update dataset set face_id = %s where id = %s'
				args = (str(faceId),row[0])
				cursor.execute(query,args)
				db.commit()
			except :
				db.rollback()
				return render_template('errorPage.html',message="DB Error : Could not tag faces")

			try:
				query = 'Insert into photo_faces (photo_id,face_id) values(%s,%s)'
				args = (str(photoId),str(faceId))
				cursor.execute(query,args)
				db.commit()
			except :
				db.rollback()
				return render_template('errorPage.html',message="DB Error : Could not Update photo_faces table")
