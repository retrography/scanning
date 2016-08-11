#!/bin/sh
g++ -c -g -O3 -Wall -fPIC pilc.cpp -I. -o pilc.o
g++ -shared -g -Wl,-soname,pilc.so -o pilc.so pilc.o
