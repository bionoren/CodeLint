#!/bin/bash
cp bad.h-orig bad.h
cp bad.m-orig bad.m
./lint.py --all
diff bad.h good.h
diff bad.m good.m
