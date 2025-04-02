import os
from typing import Match

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
        issue_body: str = issue.body

        # 提取URL
        url_pattern: str = r"(https?://[^\s]+)"
        url_match: Match[str] = re.search(url_pattern, issue_body)

        if not url_match:
            logger.error('未找到有效 URL')
            exit(0)

        file_url: str = url_match.group(0)
        logger.info(file_url)

    except Exception as e:
        logger.exception(e)
        if 'issue' in locals():
            issue.create_comment(str(e))

    finally:
        issue.edit(state='closed')