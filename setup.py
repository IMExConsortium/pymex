import setuptools
import os
from distutils.util import convert_path

with open("README.md", "r") as fh:
        long_description = fh.read()

pkg_dir = convert_path('pylib/pymex')
version_file = open(os.path.join(pkg_dir, 'VERSION'))
version = version_file.read().strip()

setuptools.setup(name="pymex-lukasz99",
                 packages = ['pymex'],
                 version=version,
                 author="Lukasz Salwinski",
                 author_email="lukasz@mbi.ucla.edu",
                 description="PSI-MI/IMEx Data Access",
                 long_description=long_description,
                 long_description_content_type="text/markdown",
                 url="https://github.com/IMExConsortium/pymex",
                 download_url = 'https://github.com/IMExConsortium/pymex/archive/0.0.11.tar.gz',
                 package_dir={'': 'pylib'},
                 include_package_data=True,
                 packages=setuptools.find_packages(where="pylib"),
                 classifiers=[
                         "Programming Language :: Python :: 3",
                         "License :: OSI Approved :: MIT License",
                         "Operating System :: OS Independent",
                         "Development Status :: 3 - Alpha"
                 ],
                 python_requires='>=3.5',
                 install_requires=[ "lxml>=3.5.0", "zeep>=3.4"]
)
