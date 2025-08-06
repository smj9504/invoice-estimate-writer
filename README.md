## 가상환경 진입
```
venv\Scripts\activate   
```

## 서버 실행 
```
streamlit run app.py
python -m streamlit run app.py
```

## .env → secrets.toml 변환 
```
python utils/convert_env_to_secrets.py
```

### requirements.txt 
```
pip freeze > requirements.txt
```