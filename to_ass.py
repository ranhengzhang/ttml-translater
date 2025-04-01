import os

from loguru import logger
import requests
import re

from github import Github
from github.Issue import Issue
from github.Repository import Repository


def process_content(content: str):
    """示例目标处理函数"""
    print(f"处理内容长度: {len(content)} 字符")
    # 在这里添加您的自定义处理逻辑


if __name__ == '__main__':
    """处理GitHub Issue"""
    issue: Issue|None = None
    try:
        # 获取环境变量
        github_token: str = os.environ['GITHUB_TOKEN']
        repo_name: str = os.environ['GITHUB_REPOSITORY']
        issue_number: str = os.environ['ISSUE_NUMBER']

        # 初始化GitHub客户端
        g: Github = Github(github_token)
        repo: Repository = g.get_repo(repo_name)
        issue = repo.get_issue(int(issue_number))

        # 获取Issue内容
        body: str = issue.body
        logger.info(body)
    except Exception as e:
        logger.exception(e)
        if 'issue' in locals():
            issue.create_comment(str(e))