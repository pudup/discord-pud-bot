git pull
sleep 2
pip install -r requirements.txt --upgrade
cd tests
pytest | tee results.txt
cd ..
clear
python3 main.py