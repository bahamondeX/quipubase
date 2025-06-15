#!/bin/bash
/app/scripts/mount.sh
/app/scripts/load_model.sh
exec "$@"