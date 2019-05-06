import argparse
import datetime
import os
import subprocess
import csv
import re
import json
from xml.etree import ElementTree as et

import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description='A Helper for Running Indri Queries')
parser.add_argument('number', help='The query number or identifier')
parser.add_argument('query', help='The actual query text which follows the Indri query language')
parser.add_argument('--config', '-c', default='config.json', help='The config file')

args = parser.parse_args()

def build_query_param_file(query_id, query_text, query_index):
    root = et.Element('parameters')
    index = et.Element('index')
    index.text = query_index
    root.append(index)
    query = et.SubElement(root, 'query')
    num = et.Element('number')
    num.text = query_id
    text = et.Element('text')
    text.text = query_text
    query.append(num)
    query.append(text)
    trecformat = et.Element('trecFormat')
    trecformat.text = 'true'
    root.append(trecformat)
    
    tree = et.ElementTree(root)
    now = datetime.datetime.now()
    if not os.path.exists('queries'):
        os.makedirs('queries')
    default_file = 'queries/query_' + now.strftime('%Y%m%d%H%M%S') + '.xml'
    with open(default_file, 'wb') as f:
        tree.write(f, encoding='utf-8')
    return default_file

def do_query(query_file):
    if not os.path.exists('rankings'):
        os.makedirs('rankings')
    rankings_file = 'rankings/' + os.path.basename(query_file).split('.')[0] + '.trec'
    with open(rankings_file, 'w') as f:
        subprocess.call(['IndriRunQuery', query_file], stdout=f)
    return rankings_file

def do_evaluation(rankings_file, qrel_file):
    if not os.path.exists('results'):
        os.makedirs('results')

    results_file = 'results/' + os.path.basename(rankings_file).split('.')[0] + '.txt'
    with open(results_file, 'w') as f:
        subprocess.call(['trec_eval', '-q', '-m', 'official', qrel_file, rankings_file], stdout=f)
    return results_file

def draw_plots(results_file):
    with open(results_file) as f:
        reader = csv.DictReader(f, fieldnames=['measure_name', 'query', 'value'], delimiter='\t')
        interpolated_precisions = []
        num_rel = 0
        num_rel_ret = 0
        map_value = 0
        for row in reader:
            if re.match(r'^num_ret', row['measure_name']):
                print('num_ret={}'.format(row['value']))
            elif re.match(r'^num_rel_ret', row['measure_name']):
                num_rel_ret = float(row['value'])
                print('num_rel_ret={}'.format(num_rel_ret))
            elif re.match(r'^num_rel', row['measure_name']):
                num_rel = float(row['value'])
                print('num_rel={}'.format(num_rel))
            elif re.match(r'^map', row['measure_name']):
                map_value = float(row['value'])
            elif re.match(r'^iprec_at_recall_\d\.\d{2}', row['measure_name']):
                interpolated_precisions.append(float(row['value']))
            elif re.match(r'^runid', row['measure_name']):
                break

        precison = 0
        if num_rel:
            precison = num_rel_ret / num_rel

        if interpolated_precisions:
            iprec_names = [i / 10.0 for i in range(11)]
            plt.plot(iprec_names, interpolated_precisions)
            plt.xlabel('Recall')
            plt.ylabel('Interpolated Precison')
            plt.axis([0, 1.0, 0, 1.0])
            plt.text(0.6, 0.9, 'map={}'.format(map_value))
            plt.text(0.6, 0.8,  'P={}/{}={:.3f}'.format(num_rel_ret, num_rel, precison))
            plt.show()

def read_configs():
    with open(args.config) as json_config:
        data = json.load(json_config)
    return data

if __name__ == "__main__":
    config = read_configs()
    query_params = build_query_param_file(args.number, args.query, config['index'])
    rankings = do_query(query_params)
    results = do_evaluation(rankings, config['qrel'])
    draw_plots(results)
