"""
Load Citation aggregate files from S3/Minio, split them into seperate files, and write them back.
"""
import gzip
import xml.etree.ElementTree as ET
from multiprocessing import Pool
from publicdata.pubmed.citation import convert_citation_xml
from publicdata.pubmed.paper import convert_doc

import boto3
from botocore.exceptions import ProfileNotFound

s3_endpoint = 'http://barker:9000'
source_s3_bucket = 'pubmed'
cit_tmpl = 'citations/xml/{}.xml'
paper_prefix = 'papers/xml'

n_threads = 16

try:
    boto3.setup_default_session(profile_name='fundfit_dev')
except ProfileNotFound:
    # These are for the development system, barker
    boto3.setup_default_session(
        aws_access_key_id='BG49EYYSC1MTHZEKNZIR',
        aws_secret_access_key = '6VS/P+a9ra6pTQdcRH2x6M2lZrPCJpHGAjRgtLGt'
    )

s3 = boto3.resource('s3',endpoint_url=s3_endpoint,
                    config=boto3.session.Config(signature_version='s3v4'))

for paper_obj in s3.Bucket(source_s3_bucket).objects.filter(Prefix=paper_prefix):

    paper = convert_doc(paper_obj.get()['Body'].read())

    if not paper['pmid']:
        continue;

    try:
        key = cit_tmpl.format(paper['pmid'])
        o = s3.Bucket(source_s3_bucket).Object(key)
        cit = convert_citation_xml(o.get()['Body'].read())

        print(cit)
    except Exception as e:
        print(type(e), key,  e)

