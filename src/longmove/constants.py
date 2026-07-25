CONFIG_ENV_VAR = "LONGMOVE_CONFIG"

# Minimum rsync version longmove supports. rsync's `--info` progress framework
# and the `xfr#`/`to-chk`/`ir-chk` progress format we parse require GNU rsync
# 3.1.0, and `rsync -VV` (which we probe with) only emits JSON on 3.2.0+.
MINIMUM_RSYNC_VERSION = (3, 2, 0)
