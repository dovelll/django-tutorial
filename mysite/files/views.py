from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.files.storage import DefaultStorage, default_storage, FileSystemStorage
from django.http import StreamingHttpResponse

from .forms import UploadFileForm

from filebrowser.sites import site
from filebrowser.base import FileListing, FileObject
import os

# print(site.storage.location)

# Create your views here.


def index(request):
	return HttpResponse("This is the file management page.")


def handle_uploaded_file(f):
	with open('./uploads/'+f.name, 'wb+') as destination:
		for chunk in f.chunks():
			destination.write(chunk)


def upload_file(request):
	if request.method == 'POST':
		form = UploadFileForm(request.POST, request.FILES)
		if form.is_valid():
			handle_uploaded_file(request.FILES['file'])
			return HttpResponse('upload succed!')
	else:
		form = UploadFileForm()
	return render(request, 'files/upload.html', {
			'form': form
		})


def get_Breadcrumbs(query):
	# Return a breadcrumb-style navigation bar
	breadcrumbs = []
	temp_path = ''
	if query:
		for item in os.path.split(query):
			temp_path = os.path.join(temp_path, item)
			breadcrumbs.append([item, temp_path])
	return breadcrumbs




class MyFileBrowser(object):
	# filelisting_class = FileListing

	def __init__(self, storage=default_storage):
		self.directory = os.path.abspath('uploads')
		self.storage = storage

	def file_browse(self, request):
		query = request.GET
		query_dir = query.get('dir', '')
		path = u'%s' % os.path.join(site.directory, query_dir)
		# print(site.directory)

		# Return a file list:hehe
		filelisting = FileListing(path, sorting_by='date', sorting_order='desc')
		fileobjects = []
		for filepath in filelisting.listing():
			fileobject = FileObject(os.path.join(site.directory, query_dir, filepath))
			# print(fileobject.path_relative_directory)
			fileobjects.append(fileobject)
		return render(request, 'files/index.html', {
			'query': query,
			'query_dir': query_dir,
			'filelisting': filelisting,
			'breadcrumbs': get_Breadcrumbs(query_dir),
			'fileobjects': fileobjects
			})

	def create_dir(self, request):
		
		from .forms import CreateDirForm

		query = request.GET
		query_dir = query.get('dir', '')
		# print(query_dir)
		path = u'%s' % os.path.join(self.directory, query_dir)

		if request.method == 'POST':
			form = CreateDirForm(request.POST)
			if form.is_valid():
				mkdir_path = os.path.join(path, form.cleaned_data['name'])
				os.mkdir(mkdir_path)
				# return HttpResponse('upload succed!')
			redirect_url = reverse("files:browse")
			return HttpResponseRedirect(redirect_url)
		else:
			form = CreateDirForm()

		# return HttpResponse("You can create new directory here.")
		return render(request, 'files/createdir.html', {
			'form': form,
		})

	def delete(self, request):
		"""Delete existing File/Directory."""
		print(1)
		query = request.GET
		path = u'%s' % os.path.join(self.directory, query.get('dir', ''))
		print(path)
		fileobject = FileObject(os.path.join(path, query.get('filename', '')))
		print(fileobject)
		if request.GET:
			try:
				fileobject.delete()
				print(1)
			except OSError:
				# TODO: define error-message
				pass
		redirect_url = reverse("files:browse") + '?dir=' + query.get('dir', '')
		return HttpResponseRedirect(redirect_url)

	def download(self, request):
		query = request.GET
		file_path = u'%s' % os.path.join(site.directory, query.get('dir', ''), query.get('filename', ''))

		def file_iterator(file_name, chunk_size=512):
			with open(file_name) as f:
				while True:
					c = f.read(chunk_size)
					if c:
						yield c
					else:
						break

		response = StreamingHttpResponse(file_iterator(file_path))
		response['Content-Type'] = 'application/octet-stream'
		response['Content-Disposition'] = 'attachment;filename="{0}"'.format(file_path)

		return response

	def upload(self, request):
		pass

	def detail(self, request):
		query = request.GET
		path = u'%s' % os.path.join(site.directory, query.get('dir', ''))
		fileobject = FileObject(os.path.join(path, query.get('filename', '')))

		from .forms import ChangeForm

		if request.method == 'POST':
			form = ChangeForm(request.POST)
			# print(form.cleaned_data['name'])
			if form.is_valid():
				new_name = form.cleaned_data['name']
				self.storage.move(fileobject.path, os.path.join(fileobject.head, new_name))
				# return HttpResponse('upload succed!')
			redirect_url = reverse("files:browse")+'?dir='+query.get('dir', '')
			return HttpResponseRedirect(redirect_url)
		else:
			form = ChangeForm()

		return render(request, 'files/detail.html', {
			'form': form,
			'query': query,
			'fileobject': fileobject,
			'breadcrumbs': get_Breadcrumbs(query.get('dir', ''))
		})


myFBsite = MyFileBrowser()
