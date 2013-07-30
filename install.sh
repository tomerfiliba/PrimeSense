#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR

which pip
if [ $? -ne 0 ]; then
	echo "Installing pip"
	curl -O https://pypi.python.org/packages/source/s/setuptools/setuptools-0.9.7.tar.gz#md5=ce3bb480e4f6d71fc2fb3388f6fe8123
	tar -xzf setuptools*.tar.gz
	cd setuptools*
	sudo python setup.py install
	cd ..

	curl -O https://raw.github.com/pypa/pip/master/contrib/get-pip.py
	sudo python get-pip.py

	rm -rf setuptools*
	rm -rf get-pip.py
fi

echo "Installing nose"
sudo pip install "nose>=1.3"   || exit 1

echo "Installing srcgen"
sudo pip install "srcgen>=1.1" || exit 1

echo "Installing openni wrapper"
sudo pip install -U primesense || exit 1

cd crayola-report
sudo python setup.py install || exit 1
cd ..

