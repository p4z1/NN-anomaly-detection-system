## Spojazdnenie centraly
### Skúšané na:
- OS: CentOS Linux 8
- Python: 3.9.10
- Cuda: 11.6
- torch: 1.11.0

### Inštalácia
- Inštalácia centraly do virtualneho python prostredia
```bash
python3.9 -m venv app
source app/bin/activate
pip3 install -r ./centrala/requirements.txt
```
- Spustenie
```bash
export FLASK_APP=<cesta_k_zlozke>/centrala/app.py
flask run --host=0.0.0.0 --port=5000
```
