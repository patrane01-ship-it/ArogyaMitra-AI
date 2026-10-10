@echo off
echo =====================
echo GIT STATUS
echo =====================
git status
echo =====================
echo GIT DIFF
echo =====================
git diff --stat
echo =====================
echo GIT FSCK
echo =====================
git fsck
echo =====================
echo COMPILEALL
echo =====================
python -m compileall -q backend
echo =====================
echo ALEMBIC CURRENT
echo =====================
cd backend
alembic current
cd ..
echo =====================
echo PIP CACHE PURGE
echo =====================
python -m pip cache purge
echo =====================
echo NPM CACHE CLEAN
echo =====================
cd frontend
call npm cache clean --force
cd ..
echo =====================
echo DISK SPACE
echo =====================
python -c "import shutil; print('C:', shutil.disk_usage('C:\\\\')); print('D:', shutil.disk_usage('D:\\\\'))"
