echo "Converting Python2 asyncio to Python3 asyncio."

find . -name "*.py" -type f -print|xargs sed -i '' -e 's/yield From/yield from/g'

find . -name "*.py" -type f -print|xargs sed -i '' -e 's/raise Return/return/g'

find . -name "*.py" -type f -print|xargs sed -i '' -e 's/import trollius as asyncio/import asyncio/g'

find . -name "*.py" -type f -print|xargs sed -i '' -e 's/from trollius import From, Return//g'

find . -name "setup.py" -type f -print|xargs sed -i '' -e 's/name="secret"/name="secret-python3"/g'
