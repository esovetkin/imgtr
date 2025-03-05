#!/usr/bin/env python3

import argparse
import cv2
import numpy as np
import os
import sys

from tqdm import tqdm

from imgtr.utils.io import read_image


def _opts():
    p = argparse.ArgumentParser(
        prog = 'raw2png.py',
        formatter_class = argparse.RawTextHelpFormatter,
        description = """Generate png of the given size
        """)

    p.add_argument(
        '--ifn','-i', type=str, default='-',
        help = """path to the file containing image paths

Default: '-', i.e. read from stdin
        """)
    p.add_argument(
        '--shape','-s', type = lambda x: tuple([int(a) for a in x.split(',')]),
        help = """shape of the output images

Image resolution is kept if not provided

Example: 1024,1024
        """)
    p.add_argument(
        '--odir','-o', type=str, default='png',
        help = """path to the output directory

        """)

    return p


def _fn2png(ifn, odir, cmn, shape=None):
    img = read_image(ifn)
    m, M = np.quantile(img, (0.01,0.99))
    img = 255 * (img - m) / (M - m)
    ofn = os.path.join(odir, ifn.replace(cmn, ''))
    ofn, ext = os.path.splitext(ofn)
    ofn = ofn + '.png'

    if shape is not None:
        img = cv2.resize(img, shape)

    os.makedirs(os.path.dirname(ofn), exist_ok=True)
    cv2.imwrite(ofn, img)


if __name__ == '__main__':
    args = _opts().parse_args()

    with open(args.ifn, 'r') if '-' != args.ifn else sys.stdin as f:
        fns = [x.strip() for x in f]

    cmn = os.path.commonprefix(fns)
    for fn in tqdm(fns):
        try:
            _fn2png(fn, args.odir, cmn, shape=args.shape)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            continue
