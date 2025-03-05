#!/usr/bin/env python3

import cv2
import numpy as np
import os
import pandas as pd
import re
import sys
import tqdm
import multiprocessing

from imgtr.exifdata import dump_exif
from imgtr.utils.files import list_files
from imgtr.utils.io import read_image, write_image


def _matches(fn, rex):
    return [i for i, x in enumerate(rex) if x.match(fn)]


def _fn2png(ifn, odir, data):
    img = read_image(ifn)
    m, M = np.quantile(img, (0.01,0.99))
    if (M-m) < 0.001:
        raise RuntimeError("zero image")
    img = 255 * (img - m) / (M - m)
    ofn = os.path.join(odir, ifn)
    ofn, ext = os.path.splitext(ofn)
    ofn = ofn + '.png'

    os.makedirs(os.path.dirname(ofn), exist_ok=True)
    cv2.imwrite(ofn, img)
    dump_exif(ofn, {'_benchmark': data})


def _process(x):
    try:
        _, row = x
        data = {'type': row['type'], 'shape': row['shape']}
        _fn2png(row['fn'],'sample_benchmark', data)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)


if __name__ == '__main__':
    df = pd.read_csv("sample4benchmark.csv")
    df['shape'] = df['shape'].str.split('@').apply(lambda row: tuple([tuple([int(i) for i in x.split('-')]) for x in row]))

    rex = [re.compile(x) for x in df['regex'].to_list()]
    dn = 'dst'
    fns = list_files(path=dn, regex='.*')

    res = []
    for fn in tqdm.tqdm(fns):
        m = _matches(fn, rex)
        if 1 != len(m):
            raise RuntimeError(f'length of matches = {len(m)}')
        res.append({'fn': fn,
                    'regex': df.iloc[m[0]]['regex'],
                    'type': df.iloc[m[0]]['type'],
                    'shape': df.iloc[m[0]]['shape']})
    res = pd.DataFrame(res)

    # ignore corrected images
    res = res[(~res['fn'].str.match('.*03_bilder.*'))]

    N = 500
    sample = pd.concat([x.sample(n=min(N, x.shape[0])) for _,x in res.groupby('type')])
    sample.to_csv('sample_benchmark.csv.gz', index=None)
    sample = sample.sample(frac=1)

    with multiprocessing.Pool() as p:
        list(tqdm.tqdm(p.imap(_process, sample.iterrows()), total=sample.shape[0]))
