#!/usr/bin/env python3

import pandas as pd
import re
import tqdm

from imgtr.exifdata import load_exif
from imgtr.utils.files import list_files


def _match_shape(d, shape):
    rex = re.compile(r'(.*)_(.*),(.*)')
    shape = [tuple(a) for a in shape]
    x = pd.DataFrame([rex.match(k).groups() for k in d.keys()],
                     columns=['component','row','col']).astype(int)
    detected = [tuple(sorted((a.row.max()-a.row.min()+1,a.col.max()-a.col.min()+1))) for _, a in x.groupby('component')]

    res = {'shapeokay': int(0 == len(set(shape)-set(detected))),
           'extra': len(detected) - len(shape)}

    return res


if __name__ == '__main__':
    DN="sample_benchmark/"
    FNS=list_files(path=DN, regex=r'.*\.png')

    res = []
    for fn in tqdm.tqdm(FNS):
        data = load_exif(fn)
        item = {'fn': fn, 'type': data['_benchmark']['type']}
        keys = [k for k in data.keys() \
                if '/cells' in k and '_rmse' not in k]
        for k in keys:
            shape = _match_shape(data[k], data['_benchmark']['shape'])
            item.update({k: 1,
                         f'{k}_shapeokay': shape['shapeokay'],
                         f'{k}_extra': shape['extra']})

        keys = [k for k in data.keys() if '_rmse' in k]
        for k in keys:
            item.update({f'{k}': data[k]})
        res.append(item)

    res = pd.DataFrame(res)
    keys = [k for k in res.columns if '/cells' in k]
    for k in keys:
        if '_rmse' in k:
            continue

        res.loc[res[k].isna(),k] = 0
        res[k] = res[k].astype(int)

    res.to_csv('benchmark.csv.gz', index=None)
