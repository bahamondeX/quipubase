#!/bin/bash
/app/scripts/mount.sh
/app/scripts/fuse.sh
/app/scripts/load_model.sh
exec "$@"