# Imimonogatari
A backend for querying manga rdf

## How to setup
### 1. Set up your enviroment
```
python -m venv env

\env\Scripts\activate
```

### 2. Install requirements
```
pip install -r requirements.txt
```

### 3. Run the server
```
uvicorn main:app --reload
```

### Note
If installing new packages please run this after
```
pip freeze > requirements.txt
```