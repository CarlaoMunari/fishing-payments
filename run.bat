@echo off
echo Iniciando Servidor de Pagamentos da Pesca...
call venv\Scripts\activate.bat
start http://127.0.0.1:5000
python app.py
pause
