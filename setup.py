from setuptools import setup

setup(
    name='nsidc_datasets',
    version='0.1.0',
    author='Andrew P. Barrett',
    author_email='andrew.barrett@colorado.edu',
    packages=["nsidc_datasets"],
    install_requires=[
        'pytest',
        'xarray',
        'numpy',
        ],
    license='license',
    description='A package containing tools to work with NSIDC data',
    long_description=open('README.md').read(),
)
