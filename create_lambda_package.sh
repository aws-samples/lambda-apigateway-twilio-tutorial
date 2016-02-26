zip -9 lambda_function.zip lambda_function.py

# Log in to the Virtual Environment
cd ./lib/python2.7/site-packages

zip -r9 ../../../lambda_function.zip *

cd ../../../lib64/python2.7/site-packages

zip -r9 lambda_function.zip *




