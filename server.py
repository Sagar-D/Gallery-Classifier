from flask import Flask, request, render_template, redirect, url_for
import gallery
import face
import config

app = Flask(__name__)

@app.route('/')
def authentication() :
	return redirect(url_for('gallery'))

app.add_url_rule('/gallery','gallery',gallery.initiateGallery)
app.add_url_rule('/photo/<photoId>','sendPhoto',gallery.sendPhoto)
app.add_url_rule('/addPhotos','addPhotos',gallery.addPhotos)
app.add_url_rule('/uploadPhotos','uploadPhotos',gallery.uploadPhotos,methods=['POST'])
app.add_url_rule('/untaggedFaces','untaggedFaces',face.untaggedFaces)
app.add_url_rule('/renderFile/<path:fpath>','renderFile',gallery.renderFile)
app.add_url_rule('/tagFaces','tagFaces',face.tagFaces,methods=['POST'])
app.add_url_rule('/getPhotosOfFace/<faceId>','getPhotosOfFace',gallery.getPhotosOfFace)
app.add_url_rule('/showFaces','showFaces',gallery.showFaces)

if __name__ == '__main__':
   app.run()
