import os
from typing import Match, AnyStr
from xml.dom.minidom import parseString, Document

from loguru import logger
import requests
from re import compile, Pattern

from github import Github
from github.Issue import Issue
from github.Repository import Repository
from requests import Response
from ttml.ttml import TTML

reg: Pattern[AnyStr] = compile(r'[\\/:*?"<>|]')

def process_content(content: str) -> tuple[str, str|None]:
    """示例目标处理函数"""
    dom: Document = parseString(content)
    ttml: TTML = TTML(dom)
    # 在这里添加您的自定义处理逻辑
    lrc = ttml.to_spl()
    logger.info(f"lrc: \n{lrc}")
    comment: str = f'```\n{lrc}\n```'

    title: str|None = ttml.get_full_title()
    file_name: str = reg.sub('-', title or "lrc")

    if not os.path.exists('dist'):
        os.makedirs('dist')
    with open('dist/' + file_name + '.lrc', 'w', encoding='utf-8') as file:
        file.write(lrc)

    return comment, title


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
        issue_lines: list[str] = [line for line in issue_body.splitlines() if line]

        file_url: str = issue_lines[1]
        file_response: Response = requests.get(file_url)
        file_response.raise_for_status()
        file_content: str = file_response.text

        comment, title = process_content(file_content)
        issue.create_comment('文件下载页面：' + os.environ['ARTIFACTS'])
        issue.create_comment(comment)
        if title is not None:
            issue.edit(title=f'[SPL] {title}')

    except Exception as e:
        logger.exception(e)
        if 'issue' in locals():
            issue.create_comment(str(e))

    finally:
        issue.edit(state='closed')