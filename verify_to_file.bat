@echo off
echo ===================== > verify_results.txt
echo GIT STATUS >> verify_results.txt
echo ===================== >> verify_results.txt
git status >> verify_results.txt 2>&1
echo ===================== >> verify_results.txt
echo GIT DIFF >> verify_results.txt
echo ===================== >> verify_results.txt
git diff --stat >> verify_results.txt 2>&1
echo ===================== >> verify_results.txt
echo GIT FSCK >> verify_results.txt
echo ===================== >> verify_results.txt
git fsck >> verify_results.txt 2>&1
echo ===================== >> verify_results.txt
echo COMPILEALL >> verify_results.txt
echo ===================== >> verify_results.txt
python -m compileall -q backend >> verify_results.txt 2>&1
echo ===================== >> verify_results.txt
echo ALEMBIC CURRENT >> verify_results.txt
echo ===================== >> verify_results.txt
cd backend
alembic current >> ..\verify_results.txt 2>&1
cd ..
echo ===================== >> verify_results.txt
echo PIP CACHE PURGE >> verify_results.txt
echo ===================== >> verify_results.txt
python -m pip cache purge >> verify_results.txt 2>&1
echo ===================== >> verify_results.txt
echo NPM CACHE CLEAN >> verify_results.txt
echo ===================== >> verify_results.txt
cd frontend
call npm cache clean --force >> ..\verify_results.txt 2>&1
cd ..
echo ===================== >> verify_results.txt
echo DISK SPACE >> verify_results.txt
echo ===================== >> verify_results.txt
python -c "import shutil; print('C:', shutil.disk_usage('C:\\\\')); print('D:', shutil.disk_usage('D:\\\\'))" >> verify_results.txt 2>&1
