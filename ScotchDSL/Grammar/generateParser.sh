wget https://www.antlr.org/download/antlr-4.9.3-complete.jar
java -jar ./antlr-4.9.3-complete.jar -Dlanguage=Python3 -no-listener -visitor functiondescription.g4
cp *.py ../Translation
