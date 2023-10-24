# third-place
unzip communes-20220101-shp.zip in data/iris
FD_MOBPRO_2018.csv
add matsim-conf

python -m pip install -r requirements.txt

cd equasim-java
mvn clean package -Pstandalone -DskipTests

cd ..
mkdir data/processed
cd code
python3 run.py --conf conf/Seine-Saint-Denis.yml
