# encoding: utf8


from setuptools import setup


setup(
    name='retrospect',
    version='0.1.3',
    description='Log with 20/20 vision',
    long_description=open('README.rst').read(),
    url='https://github.com/xtfxme/retrospect',
    author='C Anthony Risinger',
    license='BSD',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        ],
    package_data={},
    packages=[
        'retrospect',
        ],
    install_requires=[
        'byteplay',
        ],
    entry_points={},
    zip_safe=True,
    )
