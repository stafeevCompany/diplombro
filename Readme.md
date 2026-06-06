celery -A FitnessApp worker --loglevel=info
docker run -it --rm redis redis-cli -h host.docker.internal -p 6379 ping
docker run -d --name my-redis -p 6379:6379 redis
python manage.py runserver    