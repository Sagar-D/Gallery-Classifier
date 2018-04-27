from PIL import Image
import numpy as np

def getGrayScaleImage(image) :
	imageArray = np.array(image)
	image = np.array([[]])
	flag =1;
	for row in imageArray :
		res =[]
		for col in row :
			val = col[0]/3+col[1]/3+col[2]/3
			res.append(val)
		res = np.array([res])
		if flag ==0 :
			image = np.concatenate((image,res))
		if flag == 1 :
			image = res
			flag = 0;
	return image

def getImageAsRow(img) :
	imageRow = []
	for row in img :
		imageRow = imageRow + row.tolist()

	return imageRow
