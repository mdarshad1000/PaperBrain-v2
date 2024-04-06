#!/bin/bash
until nc -z $1 $2; do
  echo "Waiting for $1:$2..."
  sleep 1
done
echo "$1:$2 is available"
