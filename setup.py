import io
import os
import setuptools

this_directory = os.path.abspath(os.path.dirname(__file__))
with io.open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
  long_description = f.read()

setuptools.setup(
    name = "py-socket-server",
    packages = setuptools.find_packages(),
    install_requires = [
        "events",
        "websockets",
        "pyee",
        "defusedxml"
    ],
    version = "1.2.0",
    license = "MIT",
    long_description=long_description,
    long_description_content_type='text/markdown',
    description = "Node-Socket-Server python port.",
    author = "youngive",
    url = "https://github.com/youngive/py-socket-server",
    keywords = ["xmls", "ws", "wss", "python3", "rpl", "rolypolyland", "shararam", "server"],
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires='>=3.10',
)