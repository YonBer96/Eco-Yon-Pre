<<<<<<< HEAD
#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py migrate
=======
#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py migrate
>>>>>>> 230ca905f346a8beb0364862f23e59d304cfc50e
python manage.py collectstatic --noinput