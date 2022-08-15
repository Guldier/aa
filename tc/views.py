from genericpath import exists
import os
import io
from io import StringIO
from os import listdir
from os.path import isfile, join
from django.conf import settings
from this import d
from django.contrib import messages
from django.shortcuts import redirect, render
from django.http import HttpResponse, FileResponse, Http404
from django.core.files.storage import FileSystemStorage 
import tarfile
import os.path
import zipfile, tempfile
from wsgiref.util import FileWrapper


import pdfminer
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.layout import LAParams
from pdfminer.converter import PDFPageAggregator

from PyPDF2 import PdfFileWriter, PdfFileReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import boto3
from users.models import Profile

session = boto3.Session(
    aws_access_key_id= settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
)
ZIPFILE_NAME = 'test.zip'
pagesListLocation = list()

def main (request):
    try:
        profile = Profile.objects.get(user=request.user)
        context  = {
            'profile_view': True,
            'Active': profile.isActive,
            'uses': profile.uses
        }
        return render(request, 'tc/home.html',context)
    except:
        pass

    
    
    return render(request, 'tc/home.html')

def upload (request):
    if request.method == 'POST':
        profile = Profile.objects.get(user=request.user)
        if profile.isActive == True:
            response = HttpResponse(content_type='application/zip')
            zf = zipfile.ZipFile(response, 'w')
            uses = profile.uses
            uploded_files = request.FILES.getlist('taskcards')
            for file in uploded_files:
                ext = file.name.split('.')[1]
                if ext == 'pdf' or ext == 'PDF':
                    new_file = modify(file)
                    zf.writestr(file.name, new_file.getvalue())
                    uses = uses + 1
            profile.uses = uses
            profile.save()
            response['Content-Disposition'] = f'attachment; filename={ZIPFILE_NAME}'
            return response
        else:
            messages.warning(request,'Activate your account')
            return render(request, 'tc/upload.html')
        
    return render(request, 'tc/upload.html')

def parse_obj(lt_objs):
    locations = list()
    # loop over the object list
    for obj in lt_objs:

        # if it's a textbox, print text and location
        if isinstance(obj, pdfminer.layout.LTText):
            if "SUBTASK" in obj.get_text() or "END OF TASK" in obj.get_text():
                locations.append(obj.bbox[1])
    
        # if it's a container, recurse
        # elif isinstance(obj, pdfminer.layout.LTFigure):
        #     parse_obj(obj._objs)
    pagesListLocation.append(locations)


def modify(file):           
    existing_pdf = PdfFileReader(io.BytesIO(file.read()))
    pagesListLocation.clear()
    parser = PDFParser(file)
    document = PDFDocument(parser)

    if not document.is_extractable:
        raise PDFTextExtractionNotAllowed

    rsrcmgr = PDFResourceManager()
    device = PDFDevice(rsrcmgr)
    laparams = LAParams()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    i=0

    output = PdfFileWriter()
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    for page in PDFPage.create_pages(document):
        # read the page into a layout object
        interpreter.process_page(page)
        layout = device.get_result()
        # extract text from this object
        parse_obj(layout._objs)
        i=i+1
    
    
    for pageNum in range(len(pagesListLocation)): 
        if pagesListLocation[pageNum] != []:
            for a in pagesListLocation[pageNum]:
                can.line(0, a+10, 1000, a+10)
        can.showPage() 
    can.save()  

    #move to the beginning of the StringIO buffer
    packet.seek(0)
    # create a new PDF with Reportlab
    new_pdf = PdfFileReader(packet)

    for pageNum in range(len(pagesListLocation)):  
    # add the "watermark" (which is the new pdf) on the existing page
        page = existing_pdf.getPage(pageNum)
        page.mergePage(new_pdf.getPage(pageNum))
        output.addPage(page)
    
    temp = io.BytesIO()
    output.write(temp)
    
    return temp


def download(request):
    response = HttpResponse(content_type='application/x-gzip')
    response['Content-Disposition'] = 'attachment; filename=download.tar.gz'
    tarred = tarfile.open(fileobj=response, mode='w:gz')
    tarred.add(os.path.join(settings.MEDIA_ROOT,'New'))
    tarred.close()

    return response

def clear(request):
    path = os.path.join(settings.MEDIA_ROOT,'Uploded')
    for filename in os.listdir(path):
        os.remove(os.path.join(settings.MEDIA_ROOT,'Uploded',filename))
    
    path2 = os.path.join(settings.MEDIA_ROOT,'New')
    for filename in os.listdir(path2):
        os.remove(os.path.join(settings.MEDIA_ROOT,'New',filename))

    return redirect('main')
        
        
        

        
        
