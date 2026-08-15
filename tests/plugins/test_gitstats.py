from datetime import datetime
from unittest.mock import Mock, patch
from git import Repo, Commit
from pystonic.git.utils import (
    CommitStats,
    CommitDetail,
    lines,
    commits,
)


class TestCommitStats:
    """测试 CommitStats 模型"""

    def test_default_values(self):
        """测试默认值"""
        stats = CommitStats()
        assert stats.author == ""
        assert stats.added == 0
        assert stats.removed == 0
        assert stats.total == 0
        assert stats.commits == 0

    def test_create_with_values(self):
        """测试创建带值的实例"""
        stats = CommitStats(
            author="John Doe",
            added=100,
            removed=50,
            total=150,
            commits=5,
        )
        assert stats.author == "John Doe"
        assert stats.added == 100
        assert stats.removed == 50
        assert stats.total == 150
        assert stats.commits == 5


class TestCommitDetail:
    """测试 CommitDetail 模型"""

    def test_default_values(self):
        """测试默认值"""
        detail = CommitDetail()
        assert detail.author == ""
        assert detail.date == ""
        assert detail.message == ""
        assert detail.changes == []

    def test_from_git_commit(self):
        """测试从 Git commit 创建实例"""
        # 创建 mock commit 对象
        mock_commit = Mock(spec=Commit)
        mock_author = Mock()
        mock_author.name = "John Doe"
        mock_author.email = "john@example.com"
        mock_commit.author = mock_author
        mock_commit.authored_datetime = datetime(2024, 1, 15, 10, 30, 0)
        mock_commit.message = b"Add new feature"

        # 创建 mock diff 对象
        mock_diff = Mock()
        mock_diff.change_type = "A"
        mock_diff.a_path = "new_file.py"

        mock_commit.diff.return_value = [mock_diff]
        mock_commit.parents = []

        detail = CommitDetail.from_git_commit(mock_commit)

        assert detail.author == "John Doe"
        assert detail.date == "2024-01-15 10:30:00"
        assert detail.message == "Add new feature"
        assert detail.changes == ["A new_file.py"]

    def test_from_git_commit_with_email_fallback(self):
        """测试当作者名为空时使用邮箱"""
        mock_commit = Mock(spec=Commit)
        mock_author = Mock()
        mock_author.name = None
        mock_author.email = "john@example.com"
        mock_commit.author = mock_author
        mock_commit.authored_datetime = datetime(2024, 1, 15, 10, 30, 0)
        mock_commit.message = "Update README"
        mock_commit.diff.return_value = []
        mock_commit.parents = []

        detail = CommitDetail.from_git_commit(mock_commit)

        assert detail.author == "john@example.com"

    def test_from_git_commit_with_unknown_author(self):
        """测试当作者名和邮箱都为空时返回 Unknown"""
        mock_commit = Mock(spec=Commit)
        mock_author = Mock()
        mock_author.name = None
        mock_author.email = None
        mock_commit.author = mock_author
        mock_commit.authored_datetime = datetime(2024, 1, 15, 10, 30, 0)
        mock_commit.message = "Fix bug"
        mock_commit.diff.return_value = []
        mock_commit.parents = []

        detail = CommitDetail.from_git_commit(mock_commit)

        assert detail.author == "Unknown"

    def test_from_git_commit_with_bytes_message(self):
        """测试字节类型的消息解码"""
        mock_commit = Mock(spec=Commit)
        mock_author = Mock()
        mock_author.name = "Jane Doe"
        mock_author.email = "jane@example.com"
        mock_commit.author = mock_author
        mock_commit.authored_datetime = datetime(2024, 1, 15, 10, 30, 0)
        mock_commit.message = b"Chinese message: \xe4\xb8\xad\xe6\x96\x87"
        mock_commit.diff.return_value = []
        mock_commit.parents = []

        detail = CommitDetail.from_git_commit(mock_commit)

        assert detail.message == "Chinese message: 中文"

    def test_from_git_commit_with_string_message(self):
        """测试字符串类型的消息"""
        mock_commit = Mock(spec=Commit)
        mock_author = Mock()
        mock_author.name = "Jane Doe"
        mock_author.email = "jane@example.com"
        mock_commit.author = mock_author
        mock_commit.authored_datetime = datetime(2024, 1, 15, 10, 30, 0)
        mock_commit.message = "Regular string message"
        mock_commit.diff.return_value = []
        mock_commit.parents = []

        detail = CommitDetail.from_git_commit(mock_commit)

        assert detail.message == "Regular string message"

    def test_from_git_commit_with_parents(self):
        """测试有父 commit 的情况"""
        mock_commit = Mock(spec=Commit)
        mock_author = Mock()
        mock_author.name = "John Doe"
        mock_author.email = "john@example.com"
        mock_commit.author = mock_author
        mock_commit.authored_datetime = datetime(2024, 1, 15, 10, 30, 0)
        mock_commit.message = "Modify file"
        mock_commit.parents = [Mock()]  # 有一个父 commit

        mock_diff = Mock()
        mock_diff.change_type = "M"
        mock_diff.a_path = "existing_file.py"
        mock_commit.diff.return_value = [mock_diff]

        detail = CommitDetail.from_git_commit(mock_commit)

        assert detail.changes == ["M existing_file.py"]
        # 验证 diff 被调用时传入了父 commit
        mock_commit.diff.assert_called_once_with(mock_commit.parents[0])

    def test_from_git_commit_without_parents(self):
        """测试没有父 commit 的情况（初始提交）"""
        mock_commit = Mock(spec=Commit)
        mock_author = Mock()
        mock_author.name = "John Doe"
        mock_author.email = "john@example.com"
        mock_commit.author = mock_author
        mock_commit.authored_datetime = datetime(2024, 1, 15, 10, 30, 0)
        mock_commit.message = "Initial commit"
        mock_commit.parents = []  # 没有父 commit

        mock_diff = Mock()
        mock_diff.change_type = "A"
        mock_diff.a_path = "first_file.py"
        mock_commit.diff.return_value = [mock_diff]

        detail = CommitDetail.from_git_commit(mock_commit)

        assert detail.changes == ["A first_file.py"]
        # 验证 diff 被调用时传入 None
        mock_commit.diff.assert_called_once_with(None)


class TestLinesFunction:
    """测试 lines 函数"""

    @patch("pystonic.plugins.gitstats.utils.Repo")
    def test_lines_basic(self, mock_repo_class):
        """测试基本的行数统计"""
        # 创建 mock repo 实例
        mock_repo = Mock(spec=Repo)
        mock_repo_class.return_value = mock_repo

        # 创建 mock commit 对象
        mock_commit1 = Mock()
        mock_author1 = Mock()
        mock_author1.name = "John Doe"
        mock_author1.email = "john@example.com"
        mock_commit1.author = mock_author1
        mock_commit1.stats.total = {
            "insertions": 100,
            "deletions": 50,
            "lines": 150,
        }

        mock_commit2 = Mock()
        mock_author2 = Mock()
        mock_author2.name = "Jane Doe"
        mock_author2.email = "jane@example.com"
        mock_commit2.author = mock_author2
        mock_commit2.stats.total = {
            "insertions": 80,
            "deletions": 20,
            "lines": 100,
        }

        mock_commit3 = Mock()
        # 同一个作者
        mock_author3 = Mock()
        mock_author3.name = "John Doe"
        mock_author3.email = "john@example.com"
        mock_commit3.author = mock_author3
        mock_commit3.stats.total = {
            "insertions": 50,
            "deletions": 30,
            "lines": 80,
        }

        mock_repo.iter_commits.return_value = [
            mock_commit1,
            mock_commit2,
            mock_commit3,
        ]

        since = datetime(2024, 1, 1)
        until = datetime(2024, 1, 31)

        result = lines(since, until)

        # 验证结果
        assert len(result) == 2  # 两个不同的作者

        # John Doe 的统计
        john_stats = next(x for x in result if x.author == "John Doe")
        assert john_stats.added == 150  # 100 + 50
        assert john_stats.removed == 80  # 50 + 30
        assert john_stats.total == 230  # 150 + 80
        assert john_stats.commits == 2

        # Jane Doe 的统计
        jane_stats = next(x for x in result if x.author == "Jane Doe")
        assert jane_stats.added == 80
        assert jane_stats.removed == 20
        assert jane_stats.total == 100
        assert jane_stats.commits == 1

        # 验证 iter_commits 被正确调用
        mock_repo.iter_commits.assert_called_once_with(since=since, until=until)

    @patch("pystonic.plugins.gitstats.utils.Repo")
    def test_lines_with_email_fallback(self, mock_repo_class):
        """测试使用邮箱作为作者名的情况"""
        mock_repo = Mock(spec=Repo)
        mock_repo_class.return_value = mock_repo

        mock_commit = Mock()
        mock_author = Mock()
        mock_author.name = None  # 名字为空
        mock_author.email = "anonymous@example.com"
        mock_commit.author = mock_author
        mock_commit.stats.total = {"insertions": 10, "deletions": 5, "lines": 15}

        mock_repo.iter_commits.return_value = [mock_commit]

        since = datetime(2024, 1, 1)
        until = datetime(2024, 1, 31)

        result = lines(since, until)

        assert len(result) == 1
        assert result[0].author == "anonymous@example.com"

    @patch("pystonic.plugins.gitstats.utils.Repo")
    def test_lines_with_unknown_author(self, mock_repo_class):
        """测试作者信息全为空的情况"""
        mock_repo = Mock(spec=Repo)
        mock_repo_class.return_value = mock_repo

        mock_commit = Mock()
        mock_author = Mock()
        mock_author.name = None
        mock_author.email = None
        mock_commit.author = mock_author
        mock_commit.stats.total = {"insertions": 5, "deletions": 3, "lines": 8}

        mock_repo.iter_commits.return_value = [mock_commit]

        since = datetime(2024, 1, 1)
        until = datetime(2024, 1, 31)

        result = lines(since, until)

        assert len(result) == 1
        assert result[0].author == "Unknown"

    @patch("pystonic.plugins.gitstats.utils.Repo")
    def test_lines_empty_repo(self, mock_repo_class):
        """测试空仓库（没有 commit）"""
        mock_repo = Mock(spec=Repo)
        mock_repo_class.return_value = mock_repo
        mock_repo.iter_commits.return_value = []

        since = datetime(2024, 1, 1)
        until = datetime(2024, 1, 31)

        result = lines(since, until)

        assert len(result) == 0


class TestCommitsFunction:
    """测试 commits 函数"""

    @patch("pystonic.plugins.gitstats.utils.Repo")
    @patch("pystonic.plugins.gitstats.utils.CommitDetail")
    def test_commits_basic(self, mock_commit_detail, mock_repo_class):
        """测试基本的 commit 列表获取"""
        # 创建 mock repo 实例
        mock_repo = Mock(spec=Repo)
        mock_repo_class.return_value = mock_repo

        # 创建 mock commit 对象
        mock_commit1 = Mock()
        mock_commit2 = Mock()
        mock_commit3 = Mock()

        mock_repo.iter_commits.return_value = [
            mock_commit1,
            mock_commit2,
            mock_commit3,
        ]

        # Mock from_git_commit 方法
        mock_detail1 = Mock()
        mock_detail2 = Mock()
        mock_detail3 = Mock()
        mock_commit_detail.from_git_commit.side_effect = [
            mock_detail1,
            mock_detail2,
            mock_detail3,
        ]

        since = datetime(2024, 1, 1)
        until = datetime(2024, 1, 31)

        result = commits(since, until)

        # 验证结果
        assert len(result) == 3
        assert result == [mock_detail1, mock_detail2, mock_detail3]

        # 验证 from_git_commit 被正确调用
        assert mock_commit_detail.from_git_commit.call_count == 3
        mock_commit_detail.from_git_commit.assert_any_call(mock_commit1)
        mock_commit_detail.from_git_commit.assert_any_call(mock_commit2)
        mock_commit_detail.from_git_commit.assert_any_call(mock_commit3)

        # 验证 iter_commits 被正确调用
        mock_repo.iter_commits.assert_called_once_with(since=since, until=until)

    @patch("pystonic.plugins.gitstats.utils.Repo")
    @patch("pystonic.plugins.gitstats.utils.CommitDetail")
    def test_commits_empty(self, mock_commit_detail, mock_repo_class):
        """测试空仓库"""
        mock_repo = Mock(spec=Repo)
        mock_repo_class.return_value = mock_repo
        mock_repo.iter_commits.return_value = []

        since = datetime(2024, 1, 1)
        until = datetime(2024, 1, 31)

        result = commits(since, until)

        assert len(result) == 0
        mock_commit_detail.from_git_commit.assert_not_called()
