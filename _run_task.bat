@echo off
set SCHEDULER_TYPE=windows
set PYTHONIOENCODING=utf-8
cd /d H:\GITHUB\arXiv-Daily-Summarizer
C:\Users\root\AppData\Local\Programs\Python\Python313\python.exe -u fetch_papers.py >> H:\GITHUB\arXiv-Daily-Summarizer\_task_log.txt 2>&1
