#!/bin/sh
# Замените значения под себя перед защитой:
GROUP="bivt-sp-2"
NUMBER="1"
FIO="Ivan Ivanov"
AGE="18"
EMAIL="student@misis.edu"
PREFIX="student:${GROUP}:${NUMBER}"

redis-cli SET "${PREFIX}" "${FIO}"
redis-cli HSET "${PREFIX}:info" name "${FIO}" age "${AGE}" email "${EMAIL}"
redis-cli RPUSH "${PREFIX}:timetable" "Architecture" "Databases" "Programming"
redis-cli SADD "${PREFIX}:skills" "Docker" "Python" "Redis" "PostgreSQL"
redis-cli ZADD "${PREFIX}:tasks_w_priority" 100 "Сделать лабу 1" 150 "Сделать лабу 2" 50 "Загрузить на GitHub"

echo "\nCreated keys:"
redis-cli KEYS "student:${GROUP}:${NUMBER}*"
