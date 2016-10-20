import setuptools

setuptools.setup(
    name='wsl',
    version='0.6',
    description='Library for reading and writing WSL databases',
    long_description='Library for reading and writing WSL databases',
    url='http://jstimpfle.de/projects/wsl/main.html',
    author='Jens Stimpfle',
    author_email='jfs@jstimpfle.de',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Other Audience',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Database',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='database development administration plain-text',
    packages=['wsl'],
    install_requires=[],
    extras_require={
    },
    package_data={
    },
    data_files=[],
    entry_points={
    },
)
