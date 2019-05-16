import argparse
import itertools
import csv
import string
from xml.etree import ElementTree as ET

parser = argparse.ArgumentParser(description='A Helper for Running Indri Queries')
parser.add_argument('index', help='The index folder to be queried on')
parser.add_argument('topic', help='The topic file')
parser.add_argument(
    '--output',
    default='query_params.xml',
    help='The name for the output query parameter xml file'
)

ARGS = parser.parse_args()
QUERY_RELS = '/local/course/ir/lab3/mapping_qrels_topics.txt'

def read_topics(topic_file):
    result = None
    with open(topic_file) as f:
        tree = itertools.chain('<root>', f, '</root>')
        result = ET.fromstringlist(tree)
    return result

def build_query_params(topics_xml, query_index):
    qrels = []
    with open(QUERY_RELS) as f:
        reader = csv.DictReader(f, delimiter='\t')
        qrels = [row['qrels'] for row in reader][:50]

    root = ET.Element('parameters')
    index = ET.SubElement(root, 'index')
    index.text = query_index
    count = ET.SubElement(root, 'count')
    count.text = '100'

    translator = str.maketrans(string.punctuation, ' ' * len(string.punctuation))
    for q in qrels:
        query_node = ET.SubElement(root, 'query')
        xpath = "./TOP/[TOPNO='{}']/TITLE".format(q)
        title = topics_xml.find(xpath).text.strip()
        title = title.translate(translator)
        num = ET.Element('number')
        num.text = q
        text = ET.Element('text')
        text.text = '#combine({})'.format(title)
        query_node.append(num)
        query_node.append(text)

    trec_format = ET.SubElement(root, 'trecFormat')
    trec_format.text = 'true'
    tree = ET.ElementTree(root)
    return tree

def write_query_params(query_xml):
    with open(ARGS.output, 'wb') as f:
        query_xml.write(f, encoding='utf-8')

if __name__ == "__main__":
    topics = read_topics(ARGS.topic)
    query = build_query_params(topics, ARGS.index)
    write_query_params(query)
