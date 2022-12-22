# Imimonogatari
A backend for querying manga rdf

## How to setup
### 1. Set up your enviroment
```
python -m venv env

env\Scripts\activate
```

### 2. Install requirements
```
pip install -r requirements.txt
```

### 4. Run the Blazegraph Server
```
java -server -Xmx4g -jar blazegraph.jar
```

### 5. Clean the database (for first timer)
Create new namespace with name `bds`, full text index checked

Go to http://localhost:9999/blazegraph/#update and Run
```
DROP ALL
```
Then load the manga.ttl
```
load <file:///universal/path/to/manga.ttl>
```

### 6. Run the server
```
uvicorn main:app --reload
```

### Note
If installing new packages please run this after
```
pip freeze > requirements.txt
```