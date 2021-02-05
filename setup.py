import setuptools
import os
from distutils.util import convert_path

ldesc =[]

with open( "README.md", "r") as fh:
        long_description = fh.read()
                
pkg_dir = convert_path('pylib/pymex')
version_file = open(os.path.join(pkg_dir, 'VERSION'))
version = version_file.read().strip()

setuptools.setup( name="pymex",
                  version=version,
                  author="Pymex Support Group",
                  author_email="dip@mbi.ucla.edu",
                  description="PYMEX: PSI-MI/IMEx Data Access",
                  long_description=long_description,
                  long_description_content_type='text/markdown',
                  url="https://github.com/IMExConsortium/pymex",
                  download_url = 'https://github.com/IMExConsortium/pymex/archive/0.9.10.tar.gz',
                  package_dir={'': 'pylib'},                
                  package_data={
                          'pymex': ['mif/*.json', 'mif/*.jmif','mif/*.xsd'],
                  },
                  include_package_data=True,
                  packages=setuptools.find_packages(where="pylib",include=['pymex', 'pymex.*']),
                  classifiers=[
                          "Programming Language :: Python :: 3",
                          "License :: OSI Approved :: MIT License",
                          "Operating System :: OS Independent",
                          "Development Status :: 4 - Beta",
                          "Topic :: Scientific/Engineering :: Bio-Informatics",
                          "Intended Audience :: Science/Research"
                 ],
                 python_requires='>=3.5',
                 install_requires=[ "lxml>=3.5.0", "zeep>=3.4"]
)
