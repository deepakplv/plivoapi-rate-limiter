from setuptools import setup, find_packages
import sys

requires = [
        'redis>=2.6.0'
        ]


setup(
    name="plivo_rate_limiter",
    version="1.0.0",
    description="Rate Limiter for Plivo API",
    author="Numbers Team",
    author_email="numbers@plivo.com",
    install_requires=requires,
    classifiers=[
        "Programming Language :: Python",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Development Status :: 5 - Production/Stable",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    packages=find_packages(),
    include_package_data=True,
    package_data={"": ['*.*']},
    zip_safe=False,
)
