#!/bin/bash

# MySQL connection details
HOST="localhost"
PORT="3306"
USER="root"
PASSWORD="password"
DATABASE="book_toscrape"

# Connect to MySQL and create database if it does not exist
mysql -h $HOST -P $PORT -u $USER -p$PASSWORD -e "CREATE DATABASE IF NOT EXISTS $DATABASE;"
