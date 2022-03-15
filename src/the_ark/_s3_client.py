# import boto.s3.connection
# import mimetypes
# import os
# import shutil
# import tempfile
# import urllib
# from urllib.parse import *
# import logging
# import io

# from boto.s3.key import Key
# from io import StringIO

# logger = logging.getLogger(__name__)

# MAX_FILE_SPLITS = 9999
# DEFAULT_FILE_SPLIT_SIZE = 6291456
# DEFAULT_MINIMUM_SPLIT_AT_SIZE = 20000000


# class S3Client(object):
#     """A client that helps user to send and get files from S3"""
#     s3_connection = None
#     bucket = None

#     def __init__(self, bucket):
#         """
#         Creates the logger and sets the bucket name that will be used throughout
#         :param
#             - bucket:   string - The name of the bucket you will be working with
#         """
#         self.bucket_name = bucket

#     def connect(self):
#         """Start the amazon connection using the system's boto.cfg file to retrieve the credentials"""
#         if self.s3_connection:
#             return

#         try:
#             # - Amazon S3 credentials will use Boto's fall back config, looks for boto.cfg then environment variables
#             self.s3_connection = boto.s3.connection.S3Connection(
#                 is_secure=False)
#             self.bucket = self.s3_connection.get_bucket(
#                 self.bucket_name, validate=False)

#         except Exception as s3_connection_exception:
#             # - Reset the variables on failure to allow a reconnect
#             self.s3_connection = None
#             self.bucket = None
#             message = "Exception while connecting to S3: {0}".format(s3_connection_exception)
#             raise S3ClientException(message)

#     def store_file(self, s3_path, file_to_store, filename, return_url=False, mime_type=None,
#                    chunk_at_size=DEFAULT_MINIMUM_SPLIT_AT_SIZE):
#         """
#         Pushes the desired file up to S3 (e.g. log file).
#         :param
#             - s3_path:          string - The S3 path to the folder in which you'd like to store the file
#             - file_to_store:    StringIO or string - The fileIO or file local file path for the file to be sent
#             - filename:         string - The name the file will have when on S3. Should include the file extension
#             - return_url:       boolean - Whether to return the path to the file on S3
#             - mime_type:        string - the mime type the file should be saved as, ex: text/html or image/png
#             - chunk_at_size:    int - the size of which the file should be split to multi-upload (default ~ 20 mb)
#         :return
#             - file_url:         string - The path to the file on S3. This is returned only is return_url is set to true
#         """
#         self.connect()

#         try:
#             s3_file = Key(self.bucket)
#             s3_file.key = self._generate_file_path(s3_path, filename)


#             # --- Set the Content type for the file being sent (so that it downloads properly)
#             # - content_type can be 'image/png', 'application/pdf', 'text/plain', etc.
#             mime_type = mimetypes.guess_type(filename) if mime_type is None else mime_type
#             s3_file.set_metadata('Content-Type', mime_type)

#             # - Check if file is a buffer or disk file and if file that is getting uploaded is greater than
#             #   chunk_at_size then upload cool multi style
#             mutli_part_upload_successful = False
#             import pdb; pdb.set_trace()
#             # if isinstance(file_to_store, str) and os.path.getsize(file_to_store) > chunk_at_size:
#             if isinstance(file_to_store, io.BytesIO):
#                 split_file_dir = None
#                 multipart_file = self.bucket.initiate_multipart_upload(key_name=s3_file.key, metadata=s3_file.metadata)

#                 try:
#                     # - Split the file and get it chunky
#                     split_file_dir = self._split_file(file_to_store)

#                     # - Upload the file parts
#                     file_count = 0
#                     for files in os.listdir(split_file_dir):
#                         file_count += 1
#                         file_part = open(os.path.join(split_file_dir, files), 'rb')
#                         multipart_file.upload_part_from_file(file_part, file_count)

#                     # - Complete the upload
#                     multipart_file.complete_upload()
#                     mutli_part_upload_successful = True
#                 except boto.s3.connection.S3ResponseError as s3_error:
#                     logger.warning("A S3 Response error was caught while attempting to chunk and upload the PDF | {}\n"
#                                    "Will now attempt to send the file as a whole...".format(s3_error))
#                     multipart_file.cancel_upload()
#                 except Exception as s3_error:
#                     logger.warning("Unexpected Error encountered an issue while chunking and uploading the PDF | {}\n"
#                                    "Will now attempt to send the file as a whole...".format(s3_error))
#                     multipart_file.cancel_upload()
#                 finally:
#                     # - Remove the folder from splitting the file
#                     if split_file_dir:
#                         shutil.rmtree(split_file_dir)

#             # - Upload the file as a whole
#             if not mutli_part_upload_successful:
#                 file_type = type(file_to_store)
#                 if file_type in [str, bytes, io.BytesIO]:
#                     # s3_file.set_contents_from_filename(file_to_store)
#                     s3_file.set_contents_from_filename(filename)
#                 else:
#                     # s3_file.set_contents_from_file(file_to_store)
#                     s3_file.set_contents_from_file(filename)
            
#             if return_url:
#                 file_key = self.bucket.get_key(s3_file.key)
#                 file_key.set_acl('public-read')
#                 file_url = file_key.generate_url(0, query_auth=False)

#                 # - Certain server side permissions might cause a x-amz-security-token parameter to be added to the url
#                 # Split the url into its pieces
#                 scheme, netloc, path, params, query, fragment = urlparse(file_url)
#                 # Check whether the x-amz-security-token parameter was appended to the url and remove it
#                 params = parse_qs(query)
#                 if 'x-amz-security-token' in params:
#                     del params['x-amz-security-token']
#                 # Rebuild the params without the x-amz-security-token
#                 query = urllib.urlencode(params)

#                 return urlunparse((scheme, netloc, path, params, query, fragment))

#         except Exception as store_file_exception:
#             message = "Exception while storing file on S3: {0}".format(store_file_exception)
#             raise S3ClientException(message)

#     def get_file(self, s3_path, file_to_get):
#         """
#         Stores the desired file locally (e.g. configuration file).
#         :param
#             - s3_path:      string - The S3 path to the folder which contains the file
#             - file_to_get:  string - The name of the file you are looking for in the folder
#         :return
#             - retrieved_file    StringIO - an IO object containing the content of the file retrieved from S3
#         """
#         self.connect()

#         try:
#             if self.verify_file(s3_path, file_to_get):
#                 retrieved_file = StringIO()
#                 s3_file = self.bucket.get_key(
#                     self._generate_file_path(s3_path, file_to_get))
#                 s3_file.get_contents_to_file(retrieved_file)
#                 return retrieved_file
#             else:
#                 raise S3ClientException("File not found in S3")

#         except Exception as get_file_exception:
#             message = "Exception while retrieving file from S3: {0}".format(get_file_exception)
#             raise S3ClientException(message)

#     def verify_file(self, s3_path, file_to_verify):
#         """
#         Verifies a file (e.g. configuration file) is on S3 and returns
#         "True" or "False".
#         :param
#             - s3_path:          string - The S3 path to the folder which contains the file
#             - file_to_verify:   string - The name of the file you are looking for in the folder
#         :return
#             - boolean:     True if .get_key returns an instance of a Key object and False if .get_key returns None:
#         """
#         self.connect()
#         try:
#             file_path = self._generate_file_path(s3_path, file_to_verify)
#             s3_file = self.bucket.get_key(file_path)
#             if s3_file:
#                 return True
#             else:
#                 return False

#         except Exception as verify_file_exception:
#             message = "Exception while verifying file on S3: {0}".format(verify_file_exception)
#             raise S3ClientException(message)

#     def _generate_file_path(self, s3_path, file_to_store):
#         """
#         Ensures that the / situation creates a proper path by removing any double slash possibilities
#         :param
#             - s3_path:       string - The path to the folder you wish to store the file in
#             - file_to_store: string - The name of the file you wish to store
#         :return
#             - string:    The concatenated version of the /folder/filename path
#         """
#         return "{0}/{1}".format(s3_path.strip("/"), file_to_store.strip("/"))

#     def get_all_filenames_in_folder(self, path_to_folder):
#         """
#         Retrieves a list of the files/keys in a folder on S3
#         :param
#             - path_to_folder:   string - The path to the folder on S3. This should start after the bucket name
#         :return
#             - key_list: list - The list of keys in the folder
#         """
#         self.connect()

#         s3_folder_path = str(path_to_folder)
#         key_list = self.bucket.list(prefix=s3_folder_path)
#         return key_list

#     def get_most_recent_file_from_s3_key_list(self, key_list):
#         """
#         Sorts through the list of files in s3 key list object and returns the most recently modified file in the list
#         :param
#             - key_list:    list - The list of files returned from a s3.bucket.list() operation
#         :return
#             - key   boto.s3.Key - The most recently modified file in the key list
#         """
#         most_recent_key = None
#         for key in key_list:
#             if not most_recent_key or key.last_modified > most_recent_key.last_modified:
#                 most_recent_key = key
#         return most_recent_key

#     def _split_file(self, from_file, file_chunk_size=DEFAULT_FILE_SPLIT_SIZE):
#         """
#         Split a given file into smaller chunks named partXXXX into a temp at a default size of ~ 6 mb. The temp
#         folder should be deleted after use.

#         WARNING: You cannot split into more than 9999 files.

#         :param
#             - from_file:        string - the file to split up
#             - file_chunk_size:  int - number of Bytes each split should contain (Should be > 5 MB for Amazon S3 minimum)
#         :return:
#             - temp_dir:         string - temp folder location of split file, use to iterate through the split files
#         """
#         if os.path.getsize(from_file) > (MAX_FILE_SPLITS * file_chunk_size):
#             raise S3ClientException("Could not split the file.\nError: Input file is too large!\n")
#         elif os.path.getsize(from_file) < DEFAULT_FILE_SPLIT_SIZE:
#             raise S3ClientException("Could not split the file.\nError: Input file is too small!\n")

#         try:
#             temp_dir = tempfile.mkdtemp()
#             part_num = 0
#             with open(from_file, 'rb') as input_file:
#                 chunk = input_file.read(file_chunk_size)
#                 while chunk:
#                     part_num += 1
#                     open(os.path.join(temp_dir, ('part%04d' % part_num)), 'wb').write(chunk)
#                     chunk = input_file.read(file_chunk_size)

#             return temp_dir
#         except Exception as e:
#             raise S3ClientException("Could not split the file.\nError: {}\n".format(e))


# class S3ClientException(Exception):
#     def __init__(self, message):
#         self.msg = message

#     def __str__(self):
#         return self.msg
