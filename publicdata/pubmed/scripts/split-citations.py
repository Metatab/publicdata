"""
Load Citation aggregate files from S3/Minio, split them into seperate files, and write them back.
"""
import gzip
import xml.etree.ElementTree as ET
from multiprocessing import Pool

import boto3
from botocore.exceptions import ProfileNotFound

s3_endpoint = 'http://barker:9000'
source_s3_bucket = 'pubmed'
source_prefix = '/ftp/baseline'

dest_prefix = 'citations/xml/'

n_threads = 16

try:
    boto3.setup_default_session(profile_name='fundfit_dev')
except ProfileNotFound:
    # These are for the development system, barker
    boto3.setup_default_session(
        aws_access_key_id='BG49EYYSC1MTHZEKNZIR',
        aws_secret_access_key = '6VS/P+a9ra6pTQdcRH2x6M2lZrPCJpHGAjRgtLGt'
    )

def split_file_from_key(key):

    s3 = boto3.resource('s3',endpoint_url=s3_endpoint,
                        config=boto3.session.Config(signature_version='s3v4'))

    b = s3.Bucket(source_s3_bucket)

    r = b.Object(key).get()

    print("Extracting ",key)

    gz = gzip.GzipFile(fileobj=r['Body'])
    elem = ET.fromstring(gz.read())

    for art in elem.findall('PubmedArticle'):
        pmid = art.findtext('.//PMID')

        if pmid:
            o_key = dest_prefix+'{}.xml'.format(pmid)
            print(key, pmid, o_key)

            b.put_object(Key=o_key,Body=ET.tostring(art).decode('utf8'))


s3 = boto3.resource('s3',endpoint_url=s3_endpoint,
                        config=boto3.session.Config(signature_version='s3v4'))

keys = []
for o in s3.Bucket(source_s3_bucket).objects.filter(Prefix=source_prefix):
    if o.key.endswith('.xml.gz'):
        keys.append(o.key)


with Pool(n_threads) as p:
    p.map(split_file_from_key, keys)