from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    UniqueConstraint
)

from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True)

    github_id = Column(BigInteger, unique=True, nullable=False)

    name = Column(String(255), nullable=False)

    owner = Column(String(255), nullable=False)

    description = Column(Text, nullable=True)

    language = Column(String(100), nullable=True)

    default_branch = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=True)

    updated_at = Column(DateTime(timezone=True), nullable=True)


    commits = relationship(
        "Commit",
        back_populates="repository",
        cascade="all, delete-orphan"
    )

    issues = relationship(
        "Issue",
        back_populates="repository",
        cascade="all, delete-orphan"
    )

    pull_requests = relationship(
        "PullRequest",
        back_populates="repository",
        cascade="all, delete-orphan"
    )


class Commit(Base):
    __tablename__ = "commits"

    id = Column(Integer, primary_key=True)

    sha = Column(String(40), nullable=False)

    repository_id = Column(
        Integer,
        ForeignKey("repositories.id"),
        nullable=False
    )

    author_name = Column(String(255), nullable=True)

    author_login = Column(String(255), nullable=True)

    author_email = Column(String(255), nullable=True)

    message = Column(Text, nullable=True)

    committed_at = Column(DateTime(timezone=True), nullable=True)

    repository = relationship(
        "Repository",
        back_populates="commits"
    )

    __table_args__ = (
        UniqueConstraint(
            "repository_id",
            "sha",
            name="uq_repository_commit"
        ),
    )


class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True)

    github_issue_id = Column(BigInteger, nullable=False)

    repository_id = Column(
        Integer,
        ForeignKey("repositories.id"),
        nullable=False
    )

    issue_number = Column(Integer, nullable=False)

    author_login = Column(String(255), nullable=True)

    title = Column(Text, nullable=False)

    body = Column(Text, nullable=True)

    state = Column(String(50), nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=True)

    updated_at = Column(DateTime(timezone=True), nullable=True)

    closed_at = Column(DateTime(timezone=True), nullable=True)

    repository = relationship(
        "Repository",
        back_populates="issues"
    )

    comments = relationship(
        "IssueComment",
        back_populates="issue",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "repository_id",
            "issue_number",
            name="uq_repository_issue"
        ),
    )


class IssueComment(Base):
    __tablename__ = "issue_comments"

    id = Column(Integer, primary_key=True)

    github_comment_id = Column(BigInteger, unique=True, nullable=False)

    issue_id = Column(
        Integer,
        ForeignKey("issues.id"),
        nullable=False
    )

    author_login = Column(String(255), nullable=True)

    body = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=True)

    updated_at = Column(DateTime(timezone=True), nullable=True)

    issue = relationship(
        "Issue",
        back_populates="comments"
    )


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id = Column(Integer, primary_key=True)

    github_pr_id = Column(BigInteger, nullable=False)

    repository_id = Column(
        Integer,
        ForeignKey("repositories.id"),
        nullable=False
    )

    pr_number = Column(Integer, nullable=False)

    author_login = Column(String(255), nullable=True)

    title = Column(Text, nullable=False)

    body = Column(Text, nullable=True)

    state = Column(String(50), nullable=False)

    merged = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), nullable=True)

    updated_at = Column(DateTime(timezone=True), nullable=True)

    closed_at = Column(DateTime(timezone=True), nullable=True)

    merged_at = Column(DateTime(timezone=True), nullable=True)

    repository = relationship(
        "Repository",
        back_populates="pull_requests"
    )

    reviews = relationship(
        "PullRequestReview",
        back_populates="pull_request",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "repository_id",
            "pr_number",
            name="uq_repository_pr"
        ),
    )


class PullRequestReview(Base):
    __tablename__ = "pull_request_reviews"

    id = Column(Integer, primary_key=True)

    github_review_id = Column(BigInteger, unique=True, nullable=False)

    pull_request_id = Column(
        Integer,
        ForeignKey("pull_requests.id"),
        nullable=False
    )

    reviewer_login = Column(String(255), nullable=True)

    state = Column(String(50), nullable=True)

    body = Column(Text, nullable=True)

    submitted_at = Column(DateTime(timezone=True), nullable=True)

    pull_request = relationship(
        "PullRequest",
        back_populates="reviews"
    )