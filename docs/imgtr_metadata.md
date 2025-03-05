# imgtr_metadata: tools and query language to handle EXIF metadata

The `imgtr_metadata` provides several tools allowing to query data from the [EXIF metadata](metadata.md). It allows to bulk import/export, filter filenames satisfying some criteria and compute various cumulative statistics.

Similar to other `imgtr_*` tools the `-i` argument accepts a list of image filenames provided in a file or piped in standard input.

## `imgtr_metadata {export,import,delkey}`

The `export/import/delkey` commands manipulate the content of the metadata.

The following functionality allows to export/import metadata from a list of images.

For exporting several formats are implemented (see more details in `imgtr_metadata export --help`). For example,

```
find ... | imgtr_metadata export -o metadata -t json.gz
```

To populate EXIF data from existing dump, use

```
find ... | imgtr_metadata import -d metadata.json.gz --only_baseline
```

To delete particulate key from the EXIF data, say

```
find ... | imgtr_metadata delkey -k cells_0
```

## `imgtr_metadata {filter,hist}`

The `filter` and `hist` commands implement filtering filename and statistic accumulation. Both of this commands require an expression in the `-e` argument. The expression is formulated in terms of a query language, that implements several functions allowing to query fields in the EXIF metadata. The expression must generate `True`/`False` values for the `filter` command, allowing to accept or reject a particular file. The `hist` expects a scalar value (numerical or string), or a list. If a scalar value is given, then the `hist` computes accumulates the number of files having specific range of the `scalar` value. When the `hist` expression yields a list, the `hist` accumulates occurances of particular entries of that list over different files.

The aim for the expression query language is to be able to formulate simple one-liners. For that, the language implements several boolean and arithmetic operations, attribute access and several functions:

 - `Counter` counts stuff, just like `collections.Counter`

 - `abs`, `all`, `any`, `dict`, `filter`, `float`, `int`,`len`, `list`, `map`, `max`, `min`, `prod`, `reduce`, `round`, `str`, `sub`, `sum`, `tuple`, `type` are standard python functions

    For example, `len(cells_0)` returns the number of keys in `cells_0` field (in other words number of cells). `len(_)` return the number of fields in the EXIF metadata, where `_` points to the root of the EXIF metadata.

    `reduce := functools.reduce`, `sub := re.sub`, `prod := np.prod`

 - `cellfits` checks if a cell fits inside an image, `cellsize` computes the effective resolution of a cell

 - `in` operator checks if EXIF data contains specific key (return value True or False).

   For example, `'0_0,0' in cells_0` checks if `cells_0` dictionary has cell with key `"0_0,0"`. Calling with one quaoted argument `"cells_0" in _` checks if EXIF metadata has a field with the `cells_0` key.

 - `keys/values/items` equivalent to `.keys()` and `.values()` calls for a dictionary

 - `let` is a function that evaluates an expression within a context.

    It is useful to create variables context, for example
    ```
    let(x.TP/(x.FP + x.TP), x=eval.yolo_mclb_0)
    # the following also works
    let(x.TP/(x.FP + x.TP), y=eval, x=y.yolo_mclb_0)
    ```

 - `ncomp/nrow/ncol` returns the number of components/rows/columns for cell coordinates

   It is assumed that each cell key has the format `<component>_<row>,<col>`. Similar functionality can be achieved using the `sub`, `map` and `keys` functions.

 - `size` returns the amount of bytes it takes to store EXIF metadata.

   The return value `size(_)` returns the size of entire EXIF metadata (limit for `png` and `jpeg` is 64 kB, `_` points to the root of the EXIF data). Calling `size(cells_0)` returns amount of bytes it would take to store only the `cells_0` field.

   Note, that the following almost surely evaluates to False due to the compression:
   ```
   size(_) > sum(map(size, values(_)))
   ```
 - `unlist` equivalent to `itertools.chain` call, which unlists nested lists. Useful for combining together list of defects.

In addition, the EXIF metadata is updated with the `_imgshape` key containing the size of the image.

### Example: filter images by reconstruction error

```
% find ... | imgtr_metadata filter -e "'cells_0' in _ and cells_0_rmse > 1" | wc
100%|███████████...██| 31073/31073 [00:01<00:00, 18577.64it/s]

Errors:
    Error: cannot identify image file '...': 1
     94      94    6315
```

### Example: histogram with a number of module components

```
find ... | imgtr_metadata hist -e 'ncomp(cells_0)' -t table
100%|███████████...██| 30160/30160 [00:01<00:00, 18264.96it/s]
                  2 : 738
                  1 : 28261
    [  -1 _,   -1 _): 1161
```

Number of rows and columns. For modules with only one component, the same query can be achieved with `len(cells_0)`

```
find | imgtr_metadata hist -e 'nrow(cells_0)*ncol(cells_0)' -n 100
100%|███████████...██| 30160/30160 [00:01<00:00, 16592.96it/s]
    [ 270  ,  280  ): 2
    ...
    [  90  ,  100  ): 138
    [  80  ,   90  ): 142
    [  70  ,   80  ): 21559
    [  60  ,   70  ): 5130
    [  50  ,   60  ): 460
    ...
```

### Example: histogram with the reconstruction error distribution

```
find ... | imgtr_metadata hist -e 'cells_0_rmse'
100%|███████████...██| 50665/50665 [00:02<00:00, 18673.03it/s]
    [ 101  ,  200  ): 7
    [   1  ,  100  ): 3865
    [ 901 m, 1000 m): 117
    [ 801 m,  900 m): 237
    [ 701 m,  800 m): 682
    [ 601 m,  700 m): 2011
    [ 501 m,  600 m): 3784
    [ 401 m,  500 m): 10415
    [ 301 m,  400 m): 25533
    [ 201 m,  300 m): 3955
    [ 101 m,  200 m): 1
     -1 cells_0_rmse: 54
```

`cells_0_rmse + cells_flexible_rmse` expressions are also allowed. The `-1 cells_0_rmse` indicates number of images, where query of `cells_0_rmse` failed.


### Example: show labelled images with certain number of defects

```
find ... \
    | imgtr_metadata filter -e "'yolo_mclb_0' in _ and len(yolo_mclb_0) > 10" \
    | imgtr_plotcells -k cells_0 -l yolo_mclb_0
```

### Example: walking in nested dictionaries

Another example demonstrates walking inside a nested dictionary. In this particular example, we find all images, where "ResNet50" model created more than 10 false positive detections

```
find ... | imgtr_metadata filter -e '"yolo_mclb_0" in _ and eval.ResNet50.FP > 10'
```

### Example: list all possible cell names

```
find ... | imgtr_metadata hist -e "keys(cells_0)" -t table
100%|███████████...██| 31073/31073 [00:02<00:00, 14594.71it/s]
     -1 0_0,0                                                       : 30889
     -1 0_0,1                                                       : 30889
     -1 0_0,2                                                       : 30889
     -1 0_0,3                                                       : 30889
     -1 0_0,4                                                       : 30856
     -1 0_0,5                                                       : 30784
     -1 0_0,6                                                       : 29845
     -1 0_0,7                                                       : 29844
     -1 0_0,8                                                       : 29841
     -1 0_0,9                                                       : 29827
     ...
```

### Example: count different defect types

When `hist` command is supplied with an expression that yields a vector or a list, it accumulates values over all filenames and over all entries of the expression result.

```
find ... | imgtr_metadata hist -e "values(label_cells_0)" -t table
100%|███████████...██| 31073/31073 [00:01<00:00, 20583.76it/s]
    0_crack                       : 52549
    0_dendritic_crack             : 2127
    0_typeB                       : 14203
    1_typeB                       : 3727
    0_soldering                   : 529
    0_MUSTER_1                    : 594
    2_typeB                       : 1278
    2_crack                       : 959
    1_dendritic_crack             : 999
    ...
```

### Example: reduce, filter, map and lambda functions

```
find ... | imgtr_metadata hist -e 'map(lambda x: sub(r"^[0-9\.]+_(.*)",r"\1", x),values(label_cells_0))' -t table
100%|███████████...██| 31073/31073 [00:01<00:00, 20583.76it/s]
    crack                         : 55641
    dendritic_crack               : 3367
    typeB                         : 19208
    label_cells_0                 : 6552
    soldering                     : 538
    MUSTER_1                      : 626
    typeC                         : 345
    darkCell                      : 9
    MUSTER_4                      : 245
    darkArea                      : 22
    printRear                     : 2
    chainPattern                  : 2
...
```

### Example: find modules with any cell outside the image

The following will show all images, that contain at least one cell outside the image boundary.

```
find ... | imgtr_metadata filter -e 'any(map(lambda x: not cellfits(x, _imgshape), values(cells_0)))' \
         | imgtr_plotcells -k cells_0
```

The following will show all images, that have at least 10 cells outside the image boundary.

```
find ... | imgtr_metadata filter -e 'sum(map(lambda x: not cellfits(x, _imgshape), values(cells_0))) > 10' \
         | imgtr_plotcells -k cells_0
```

### Example: distribution of confidence levels

```
find ... | imgtr_metadata hist -e 'map(lambda x: float(sub(r".*_([0-9\.]+)",r"\1",x)), values(yolo_mclb_0))'
100%|███████████...██| 31073/31073 [00:01<00:00, 18133.04it/s]
    [   0  ,  100  ): 5
    [ 900 m, 1000 m): 48719
    [ 800 m,  900 m): 3542
    [ 700 m,  800 m): 2048
    [ 600 m,  700 m): 2045
    [ 500 m,  600 m): 1656
    [ 400 m,  500 m): 1804
    [ 300 m,  400 m): 2100
    [ 200 m,  300 m): 1158
...
```

For example, the `[ 600 m,  700 m): 2045` line means there 2045 detected cells with confidence levels in the interval `[0.6,0.7)`.

The `-t quantile` can be used for approximate quantile computation (using t-digest algorithm)

```
find ... | imgtr_metadata hist -e 'map(lambda x: float(sub(r".*_([0-9\.]+)",r"\1",x)), values(yolo_mclb_0))' -t quantile
100%|███████████...██| 31073/31073 [00:01<00:00, 14819.12it/s]
      0%:    0
     10%:  570 m
     20%:  854 m
     30%:  945 m
     40%:  962 m
     50%:  968 m
     60%:  972 m
     70%:  975 m
     80%:  978 m
     90%:  980 m
    100%:  980 m
```

The following example find all images where `yolo_mclb_0` has any detections with confidence level less than 0.3.

```
find ... | imgtr_metadata filter -e 'any(map(lambda x: float(sub(r".*_([0-9\.]+)",r"\1",x)) < 0.3, values(yolo_mclb_0)))' \
         | imgtr_plotcells -k cells_0 -l yolo_mclb_0
```

### Example: distribution of defect counts for different number of images

The following shows the number of "crack" occurances in images.

```
find ... | imgtr_metadata hist -e 'Counter(map(lambda x: sub(r"^.*_(.*)$",r"\1", x), values(label_cells_0)))["crack"]' -n 100
100%|███████████...██| 31073/31073 [00:01<00:00, 19082.29it/s]
    [  60  ,   70  ): 1
    [  50  ,   60  ): 7
    [  40  ,   50  ): 15
    [  30  ,   40  ): 63
    [  20  ,   30  ): 147
    [  10  ,   20  ): 1095
    [   0  ,   10  ): 12850
    [  -1 _,   -1 _): 16894
```

where `-1` label indicates that the evaluation there failed, most probably due to the absence of the "crack" defect

```
find ... | imgtr_metadata hist -e 'sum(values(Counter(values(yolo_mclb_0))))' -n 100
100%|███████████...██| 31073/31073 [00:01<00:00, 19836.77it/s]
    [  50  ,   60  ): 3
    [  40  ,   50  ): 7
    [  30  ,   40  ): 41
    [  20  ,   30  ): 240
    [  10  ,   20  ): 1282
    [   0  ,   10  ): 29499
```

## `imgtr_metadata keys`

In principle, duplicates what can be written with `hist` queries. However, the size is computed without additonal serialization/deserialization.

```
% find ... | imgtr_metadata keys
100%|█████████ ... ███| 95689/95689 [00:06<00:00, 14062.07it/s]

Keys occurance:
    cells                                             : 95685
    cells_0_rmse                                      : 94374
    cells_flexible_rmse                               : 94374
    cells_prism_rmse                                  : 94358
    cells_rational_rmse                               : 94358
    cells_flexible                                    : 93980
    cells_prism                                       : 93961
    cells_rational                                    : 93816
    cells_0                                           : 93806
    szslabel_cells_0                                  : 42072
    label_cells_0                                     : 42072
    yolo_mclb_0                                       : 31067
    labels_szs                                        : 23501
    PCABoost_1                                        : 1252
    PCABoost_2                                        : 100

EXIF metadata volume:
    [16.0 B  , 32.0 B  ): 1
    [32.0 B  , 64.0 B  ): 1
    [64.0 B  , 128.0 B ): 6
    [128.0 B , 256.0 B ): 35
    [256.0 B , 512.0 B ): 100
    [512.0 B , 1.0 kB  ): 1003
    [1.0 kB  , 2.0 kB  ): 484
    [2.0 kB  , 4.0 kB  ): 603
    [4.0 kB  , 8.0 kB  ): 82811
    [8.0 kB  , 16.0 kB ): 10475
    [16.0 kB , 32.0 kB ): 166

Errors:
    Error: cannot identify image file
    ...
```

Also, the different between `keys` command and `hist -t table -e "keys(_)"`, is that the latter command also shows additional fields added during processing, such as `_imgshape`.
