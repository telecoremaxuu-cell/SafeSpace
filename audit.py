import os
files = ['backend/main.py', 'backend/models.py', 'backend/database.py', 'frontend/index.html', '.env']
print('--- Т Т SAFESPACE ---')
for f in files:
    status = '✅ а месте' if os.path.exists(f) else '❌  '
    size = os.path.getsize(f) if os.path.exists(f) else 0
    print(f'{status}: {f} ({size} байт)')
