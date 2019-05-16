import argparse
import csv
import gzip
import os
from collections import defaultdict

parser = argparse.ArgumentParser(description='A Helper for Evaluating Indri Queries')
parser.add_argument('qresult', help='The result file from running IndriRunQuery')
parser.add_argument('-k', default=10, type=int, help='The K number for the P@K score, default=10')

ARGS = parser.parse_args()
QRELS_PATH = '/local/course/ir/data/MedEvalTK/None'

def read_results_file(file):
    result = defaultdict(list)
    with open(file) as f:
        reader = csv.DictReader(f, ['qid', '_', 'did', 'rank', 'score'], delimiter=' ')
        for row in reader:
            result[row['qid']].append(row['did'])
    return result

def read_qrel_file(qid):
    result = defaultdict(int)
    qrel_file = os.path.join(QRELS_PATH, 'N{}.txt.gz'.format(qid))
    with gzip.open(qrel_file, 'rt') as f:
        reader = csv.DictReader(f, ['document', 'qrel'], delimiter='\t')
        for row in reader:
            result[row['document']] = int(row['qrel'])
    return result

def p_at_k_score(query_results, k):
    result = defaultdict(float)
    for qid, documents in query_results.items():
        qrel = read_qrel_file(qid)
        precision = 0
        for d in documents[:k]:
            if qrel[d] > 0:
                precision += 1
        precision = precision / len(documents)
        result[qid] = precision
    return result

def map_score(query_results):
    result = 0
    query_length = len(query_results)

    for qid, doc in query_results.items():
        qrel = read_qrel_file(qid)
        rel_doc_size = len(qrel) - list(qrel.values()).count(0)
        precision = 0
        for i in range(rel_doc_size):
            rel_doc_found = 0
            total_doc_enumerated = 0
            for d in doc:
                total_doc_enumerated += 1
                if qrel[d] > 0:
                    rel_doc_found += 1
                if rel_doc_found > i:
                    # break if found the (i+1)th relevant doc
                    break
            # precision(R_ij)
            precision += float(rel_doc_found / total_doc_enumerated)
        precision /= rel_doc_size
        result += precision
    result /= query_length
    return result

def print_scores(p_at_k, map_result, k):
    print('Results for {} queries:\n'.format(len(p_at_k)))

    print('P@{} scores'.format(k))
    print('====================================')
    for qid in sorted(p_at_k.keys(), key=int):
        print('Query id {}:\tP@{}={:.3f}'.format(qid, k, p_at_k[qid]))
    print()

    print('MAP score')
    print('====================================')
    print('MAP={:.3f}'.format(map_result))

if __name__ == "__main__":
    results = read_results_file(ARGS.qresult)
    p = p_at_k_score(results, ARGS.k)
    m = map_score(results)
    print_scores(p, m, ARGS.k)
