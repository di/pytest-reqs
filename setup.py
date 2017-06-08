from setuptools import setup

__version__ = '0.0.6'

if __name__ == "__main__":
    setup(
        name='pytest-reqs',
        description='pytest plugin to check pinned requirements',
        long_description=open("README.rst").read(),
        license="MIT license",
        version=__version__,
        author='Dustin Ingram',
        author_email='github@dustingram.com',
        url='https://github.com/di/pytest-reqs',
        py_modules=['pytest_reqs'],
        entry_points={'pytest11': ['reqs = pytest_reqs']},
        install_requires=['pytest>=2.4.2'],
        tests_require=['pytest>=2.4.2', 'pretend'],
        classifiers=[
            'Framework :: Pytest',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
        ],
    )
