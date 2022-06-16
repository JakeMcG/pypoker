import glob
import os
import shutil

NPM_DIR = 'node_modules'
STATIC_DIR = 'pypoker/static'

# list of tuples
# each tuple:
# (node package, glob to find file(s), subdirectory in destination)
DEPENDENCIES = [
    ('jquery', 'dist/jquery.min.js*', 'vendor/js'),
    ('bootstrap', 'dist/js/bootstrap.min.js*', 'vendor/js'),
    ('bootstrap', 'dist/css/bootstrap.min.css*', 'vendor/css'),
    ('pivottable', 'dist/pivot.min.js*', 'vendor/js'),
    ('pivottable', 'dist/pivot.min.css*', 'vendor/css'),
    ('jqueryui', 'jquery-ui.min.js', 'vendor/js')
]
# asterisks to include .js.map and .css.map

for (package, test, dest) in DEPENDENCIES:

    results = glob.glob(os.path.join(NPM_DIR, package, test))

    if not results:
        continue

    dest = os.path.join(STATIC_DIR, dest)
    if not os.path.isdir(dest):
        print(f"{dest} doesn't exist: creating it.")
        os.makedirs(dest)

    for file in results:
        shutil.copy(file, dest)
        print(f"Copied {file} from {package} to {dest}.")
