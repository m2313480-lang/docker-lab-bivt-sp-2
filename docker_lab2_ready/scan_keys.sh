#!/bin/sh
CURSOR=0
while :; do
  OUT=$(redis-cli SCAN "$CURSOR")
  CURSOR=$(echo "$OUT" | sed -n '1p')
  KEYS=$(echo "$OUT" | sed '1d')
  for key in $KEYS; do
    type=$(redis-cli TYPE "$key")
    echo "Key: $key, Type: $type"
    case "$type" in
      string) redis-cli GET "$key";;
      hash) redis-cli HGETALL "$key";;
      list) redis-cli LRANGE "$key" 0 -1;;
      set) redis-cli SMEMBERS "$key";;
      zset) redis-cli ZRANGE "$key" 0 -1 WITHSCORES;;
    esac
  done
  [ "$CURSOR" = "0" ] && break
done
