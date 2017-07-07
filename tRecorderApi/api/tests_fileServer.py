from django.test import TestCase
from datetime import datetime
from views import ProjectViewSet,FileUploadView, FileStreamView
from rest_framework.test import APIClient
from rest_framework import status
#from pathlib import Path
import os


#Creating a text file to log the results of each of the tests
with open("test_log.txt", "w") as test_log:
    test_log.write("API TEST LOG\n")  #create title for test log
    sttime = datetime.now().strftime('%m/%d/%Y_%H:%M:%S') #create time stamp for test log
    test_log.write("DATE:" + sttime + "\n\n")  #print time stamp to test log
base_url = 'http://127.0.0.1:8000/api/'
my_file = 'media/dump'


#delete file from dump
#get file from dump,
#get JSON (?)
class fileServerTestCases(TestCase):
    def SetUp(self):
        """Set up environment for fileServer test suite"""
        self.client = APIClient()


    def test_fileServer_can_upload_file(self):
        """Verify that fileServer can upload file to dump folder through POST"""
        #list1 to search through dump folder
        list1 = os.listdir(my_file)
        old_count = len(list1)
        with open('en-x-demo2_ulb_mrk.zip', 'rb') as test_zip:
            response = self.client.post(base_url + 'upload/zip', {'Media type': '*/*', 'Content': test_zip}, format='multipart')
            #list2 to reinitialize the dump folder to count updates
            list2 = os.listdir(my_file)
            new_count = len(list2)
            self.assertNotEqual(old_count, new_count)
            test_log = open("test_log.txt", "a")
            test_log.write("TEST: File uploaded to file server..............................PASSED\n")
            test_log.close()


    def test_fileServer_can_get_file(self):
        """Verify that fileServer can retrieve file from dump folder through GET"""

        #get(self, request, filepath, format='mp3'):
        response = self.client.get(base_url + 'takes/1/')

    def test_upload_non_zip_file_returns_403_error(self):
        """Verify that uploading a non zip file will return a 403 FORBIDDEN code"""
        with open('DS TEST 1.docx', 'rb') as test_nonzip:
             self.response = self.client.post(base_url + 'upload/zip', {'Media type' : '*/*', 'Content' : test_nonzip}, format='multipart')
             self.assertEqual(self.response.status_code, status.HTTP_403_FORBIDDEN)
             test_log = open("test_log.txt", "a")
             test_log.write("TEST: Uploading non-ZIP File to API...............................PASSED\n")
             test_log.close()

    def test_upload_non_zip_file_returns_403_error(self):
        """Verify that uploading a zip file containing non .wav files returns 403 FORBIDDEN code"""
        with open('no_wav_files.zip', 'rb') as test_zip_nowav:
             self.response = self.client.post(base_url + 'upload/zip', {'Media type' : '*/*', 'Content' : test_zip_nowav}, format='multipart')
             self.assertEqual(self.response.status_code, status.HTTP_403_FORBIDDEN)
             test_log = open("test_log.txt", "a")
             test_log.write("TEST: Uploading ZIP File with non .wav Files to API.......................PASSED\n")
             test_log.close()







