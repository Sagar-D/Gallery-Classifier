from PIL import Image
import numpy as np
import preprocessor as pre
import operator
import MySQLdb
import config

def isTrainable() :
	db = MySQLdb.connect(config.server,config.username,config.password,config.database)
	cursor = db.cursor()
	try :
		query = "Select count(*) from faces"
		cursor.execute(query)
		facetuple = cursor.fetchone()
	except MySQLdb.Error,e :
		print("*****ERROR : %d : %s" % (e.args[0], e.args[1]))
		return render_template('errorPage.html',message="Trainer Error : Could not get photo_id")

	try :
		query = "Select count(*) from dataset where face_id is NOT NULL"
		cursor.execute(query)
		tagtuple = cursor.fetchone()
	except MySQLdb.Error,e :
		print("*****ERROR : %d : %s" % (e.args[0], e.args[1]))
		return render_template('errorPage.html',message="Trainer Error : Could not get photo_id")

	faceCount = facetuple[0]
	tagCount = tagtuple[0]

	if faceCount == 0 :
		return False

	ratio = tagCount/faceCount
	print("******* ratio")
	print(ratio)
	if ratio >=3 :
		return True
	return False


def trainAlgorithm() :

	db = MySQLdb.connect(config.server,config.username,config.password,config.database)
	cursor = db.cursor()
	try :
		query = "Select id,photo_id,image_path,face_id from dataset where face_id IS NOT NULL"
		cursor.execute(query)
		tuples = cursor.fetchall()
	except MySQLdb.Error,e :
		print("*****ERROR : %d : %s" % (e.args[0], e.args[1]))
		return render_template('errorPage.html',message="Trainer Error : Could not load photos To trainer")

	print("********** Reading TestSet Photos ************")
	isFirstFace = True
	faceIdList = []
	print(len(tuples))
	for row in tuples :
		print(row[0])
		path = row[2]
		face = Image.open(path)
		face = face.resize((50,50))

		# if face is RGB colored then convert it to grey scale
		if(len(np.array(face).shape)>2) :
			face = pre.getGrayScaleImage(face)

		# get FaceRow by concatinating all the rows of the image
		faceRow = pre.getImageAsRow(np.array(face))

		faceIdList.append(row[3])
		if isFirstFace :
			isFirstFace = False
			dataMatrix = np.array([faceRow])
		else :
			dataMatrix = np.concatenate((dataMatrix,np.array([faceRow])))

	print("********** Training Algorithm ************")
	print(len(dataMatrix))
	print(len(dataMatrix[0]))
	print("********** Finding Mean Vector ************")
	meanVector = dataMatrix.mean(axis=0)
	#print(meanVector)
	for faceRow in dataMatrix :
		faceRow = faceRow - meanVector

	print("********** Finding Covariance Matrix ************")
	covMatrix = np.cov(dataMatrix,rowvar=False)
	print(len(covMatrix))
	print("********** Finding Eigen Vectors ************")
	eigenValues,eigenVectors = np.linalg.eigh(covMatrix)
	print(len(eigenValues))
	print(len(eigenVectors[0]))
	#print(covMatrix.shape)
	#print(dataMatrix.shape)

	threshold = eigenValues[0] + ( (eigenValues[len(eigenValues)-1] - eigenValues[0])/2 )
	count = 0;
	for evalue in eigenValues :
		if(evalue > threshold) :
			break
	count+=1

	print("********** Feature Vector ************")
	featureVector = [ x[2000:] for x in eigenVectors]
	#print(len(featureVector));

	print("********** Calculating new DataPoints ************")
	dataPoints = np.matmul(dataMatrix,featureVector);

	return featureVector, dataPoints, faceIdList

def classifyFace(fpath,featureVector,dataPoints,faceIdList) :
	recogFaceId = KNNClassify(fpath,featureVector,dataPoints,faceIdList)
	return recogFaceId;

def getDistance(a,b) :
	dist = np.sqrt(np.sum((a-b)**2))
	return dist

def getNeighbours(source,dataSet,faceIdList,k) :
	distance = []
	for i in range(len(dataSet)) :
		d = getDistance(source,dataSet[i])
		if d < 99999999999 :
			distance.append((faceIdList[i],d))
	distance.sort(key=operator.itemgetter(1))
	neighbours = distance
	if len(neighbours) > k :
		neighbours = neighbours[:k]
	return neighbours

def KNNClassify(fpath,featureVector,dataPoints,faceIdList) :

	print("********** Reading Test Image ************")
	print(fpath)
	ukn_face = Image.open(fpath);
	ukn_face = ukn_face.resize((50,50))

	print("********** Finding New dataPoints for Test Image ************")
	if(len(np.array(ukn_face).shape)>2) :
		ukn_face = pre.getGrayScaleImage(ukn_face)

	ukn_faceRow = pre.getImageAsRow(np.array(ukn_face))
	ukn_dataPoint = np.matmul(ukn_faceRow,featureVector)

	neighbours = getNeighbours(ukn_dataPoint,dataPoints,faceIdList,5)

	print("************* Neighbours")
	print(neighbours)

	classVote = {}
	for point in neighbours :
		value = point[0]
		if(value in classVote):
			classVote[value] += 1
		else :
			classVote[value] = 1

	print("********** ClassVote")
	print(classVote)

	maxVote = 0
	faceTag = 0
	for key in classVote :
		if(classVote[key] > maxVote) :
			maxVote = classVote[key]
			faceTag = key

	if maxVote >= 3 :
		return faceTag
	return None
