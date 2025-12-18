@echo off
echo ====================================
echo RESETANDO PROJETO DJANGO
echo ====================================

echo 1. Parando servidor na porta 8080...
netstat -ano | findstr :8080 > nul
if %errorlevel% equ 0 (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8080') do (
        echo Matando processo PID: %%a
        taskkill /PID %%a /F > nul 2>&1
    )
)

echo 2. Deletando banco de dados antigo...
if exist db.sqlite3 (
    copy db.sqlite3 db_backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%.sqlite3
    del db.sqlite3
    echo Backup criado: db_backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%.sqlite3
)

echo 3. Limpando migrações...
if exist usuarios\migrations\*.py (
    del usuarios\migrations\0*.py
    echo. > usuarios\migrations\__init__.py
)

if exist produtos\migrations\*.py (
    del produtos\migrations\0*.py
    echo. > produtos\migrations\__init__.py
)

if exist frontend\migrations\*.py (
    del frontend\migrations\0*.py
    echo. > frontend\migrations\__init__.py
)

echo 4. Criando novas migrações...
python manage.py makemigrations

echo 5. Aplicando migrações...
python manage.py migrate

echo 6. Criando superusuário...
python manage.py createsuperuser

echo 7. Coletando arquivos estáticos...
python manage.py collectstatic --noinput

echo 8. Iniciando servidor...
echo ====================================
echo Servidor iniciando em: http://localhost:8080
echo ====================================
python manage.py runserver 8080