# Contributing Guide

## Welcome Contributors! 🎉

Thank you for your interest in contributing to the Chat with SQL system. This guide will help you understand how to contribute effectively and follow our development practices.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Coding Standards](#coding-standards)
5. [Submitting Changes](#submitting-changes)
6. [Review Process](#review-process)
7. [Release Process](#release-process)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for everyone, regardless of:

- Experience level
- Gender identity and expression
- Sexual orientation
- Disability
- Personal appearance
- Body size
- Race
- Ethnicity
- Age
- Religion
- Nationality

### Our Standards

**Positive behavior includes:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior includes:**
- Harassment, trolling, or discriminatory language
- Personal attacks or political commentary
- Public or private harassment
- Publishing private information without permission
- Any other conduct which could reasonably be considered inappropriate

### Reporting Issues

If you experience or witness unacceptable behavior, please contact us at:
- Email: conduct@company.com
- Slack: #moderation-team

## Getting Started

### 1. Fork the Repository

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/adityatiwari12/TalkwithDB.git
cd talk_to_db

# Add the original repository as upstream
git remote add upstream https://github.com/adityatiwari12/TalkwithDB.git
```

### 2. Set Up Development Environment

Follow the [Setup Guide](setup-guide.md) to get your development environment ready.

### 3. Understand the Codebase

Before making changes, spend time understanding:

- **System Architecture**: Read [System Design](../architecture/system-design.md)
- **Database Design**: Review [Database Documentation](../architecture/database-design.md)
- **Code Structure**: Explore the source code organization
- **Existing Issues**: Look at open issues and pull requests

### 4. Find Something to Work On

**Good first issues:**
- Look for issues labeled `good first issue`
- Bug fixes with clear reproduction steps
- Documentation improvements
- Test coverage improvements

**More complex issues:**
- Features marked `help wanted`
- Performance improvements
- Security enhancements
- Major architectural changes

## Development Workflow

### 1. Create a Branch

```bash
# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# Create a feature branch
git checkout -b feature/your-feature-name

# Or a bug fix branch
git checkout -b fix/issue-number-description
```

### 2. Make Your Changes

**Follow these guidelines:**

- **Small, focused commits**: Each commit should address one specific change
- **Clear commit messages**: Use the conventional commit format
- **Test your changes**: Ensure all tests pass
- **Update documentation**: Update relevant documentation

### 3. Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(api): add rate limiting endpoint

Add rate limiting to prevent API abuse and ensure fair usage.
Implements rate limiting of 100 requests per minute per IP.

Closes #123

fix(sql): handle NULL values in aggregation

Fixes SQL generation when dealing with NULL values in
aggregate functions. Adds proper COALESCE handling.

fixes #456

docs(readme): update installation instructions

Updates the README with clearer installation steps and
troubleshooting information for common issues.
```

### 4. Testing Your Changes

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/ --cov-report=html

# Run specific tests
pytest tests/unit/test_sql_validator.py

# Check code formatting
black --check src/
flake8 src/

# Run type checking
mypy src/
```

### 5. Sync Your Branch

```bash
# Before creating a pull request, sync with upstream
git fetch upstream
git rebase upstream/main

# Resolve any conflicts
# (resolve conflicts, then continue)
git add .
git rebase --continue
```

## Coding Standards

### 1. Python Code Style

We follow [PEP 8](https://pep8.org/) with these additional guidelines:

```python
# Good example
class SQLGenerator:
    """Generates SQL queries from natural language questions.
    
    This class uses Ollama LLM to convert natural language questions
    into SQL queries based on the provided database schema.
    
    Attributes:
        model_name: Name of the LLM model to use
        ollama_client: Client for communicating with Ollama
    """
    
    def __init__(self, model_name: str = "llama3.2"):
        """Initialize the SQL generator.
        
        Args:
            model_name: Name of the LLM model to use
        """
        self.model_name = model_name
        self.ollama_client = OllamaClient()
    
    def generate_sql(self, question: str, schema: List[SchemaDoc]) -> str:
        """Generate SQL query from natural language question.
        
        Args:
            question: Natural language question from user
            schema: List of relevant schema documents
            
        Returns:
            Generated SQL query string
            
        Raises:
            SQLGenerationError: If SQL generation fails
        """
        try:
            prompt = self._construct_prompt(question, schema)
            response = self.ollama_client.generate(
                model=self.model_name,
                prompt=prompt
            )
            return self._extract_sql(response)
        except Exception as e:
            raise SQLGenerationError(f"Failed to generate SQL: {e}")
```

### 2. Documentation Standards

**Docstrings:** Use Google-style docstrings

```python
def validate_sql(self, sql: str) -> ValidationResult:
    """Validate SQL query for safety and compliance.
    
    Performs multiple validation checks including:
    - SQL type validation (SELECT-only)
    - Injection pattern detection
    - System table access prevention
    - Query complexity analysis
    
    Args:
        sql: SQL query string to validate
        
    Returns:
        ValidationResult with validation status and details
        
    Example:
        >>> validator = SQLValidator()
        >>> result = validator.validate("SELECT * FROM users")
        >>> print(result.is_valid)
        True
    """
```

**Comments:** Use comments to explain complex logic

```python
# Calculate similarity score using weighted approach
# Semantic similarity (70%) + keyword overlap (30%)
semantic_score = self._calculate_semantic_similarity(question, schema)
keyword_score = self._calculate_keyword_overlap(question, schema)
similarity_score = (semantic_score * 0.7) + (keyword_score * 0.3)
```

### 3. Error Handling

**Use specific exceptions:**

```python
# Good
try:
    result = self.database.execute_query(sql)
except DatabaseConnectionError as e:
    logger.error(f"Database connection failed: {e}")
    raise ServiceUnavailableError("Database temporarily unavailable")
except SQLExecutionError as e:
    logger.error(f"SQL execution failed: {e}")
    raise ValidationError(f"Invalid SQL: {e}")

# Avoid
try:
    result = self.database.execute_query(sql)
except Exception as e:
    print(f"Error: {e}")
    raise
```

**Custom exceptions:**

```python
class ChatSQLError(Exception):
    """Base exception for Chat SQL system."""
    pass

class SQLGenerationError(ChatSQLError):
    """Raised when SQL generation fails."""
    pass

class SchemaRetrievalError(ChatSQLError):
    """Raised when schema retrieval fails."""
    pass
```

### 4. Type Hints

Use type hints for all function signatures and important variables:

```python
from typing import List, Dict, Optional, Union
from dataclasses import dataclass

@dataclass
class QueryResult:
    """Result of a database query."""
    data: List[Dict[str, Any]]
    execution_time_ms: int
    row_count: int
    success: bool
    error: Optional[str] = None

def process_question(
    question: str,
    context: Optional[Dict[str, Any]] = None
) -> QueryResult:
    """Process natural language question."""
    pass
```

### 5. Logging Standards

Use structured logging with appropriate levels:

```python
import logging
import json

logger = logging.getLogger(__name__)

def process_query(self, question: str, user_id: str) -> Dict[str, Any]:
    """Process user query with comprehensive logging."""
    
    logger.info(
        "Query processing started",
        extra={
            "user_id": user_id,
            "question": question,
            "question_length": len(question),
            "timestamp": datetime.now().isoformat()
        }
    )
    
    try:
        result = self._generate_and_execute_sql(question)
        
        logger.info(
            "Query processing completed successfully",
            extra={
                "user_id": user_id,
                "execution_time_ms": result["execution_time"],
                "result_count": len(result["data"]),
                "sql_generated": result["sql"]
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "Query processing failed",
            extra={
                "user_id": user_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "question": question
            },
            exc_info=True
        )
        raise
```

## Submitting Changes

### 1. Pull Request Process

**Before submitting:**

1. **Test thoroughly**: Ensure all tests pass
2. **Update documentation**: Update relevant docs
3. **Check formatting**: Run code formatting tools
4. **Sync with main**: Rebase on latest main branch
5. **Review your changes**: Review your own diff

### 2. Pull Request Template

```markdown
## Description
Brief description of the changes made.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] All tests pass
- [ ] Added new tests for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review of the code
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
- [ ] Performance considerations addressed

## Related Issues
Closes #123
Fixes #456

## Screenshots (if applicable)
Add screenshots for UI changes.

## Additional Notes
Any additional context or considerations.
```

### 3. Pull Request Title Format

Use the same conventional commit format for PR titles:

```
feat(api): add rate limiting endpoint
fix(sql): handle NULL values in aggregation
docs(readme): update installation instructions
```

## Review Process

### 1. Code Review Guidelines

**For Reviewers:**

- **Be constructive**: Provide helpful, specific feedback
- **Be timely**: Review PRs within 2 business days
- **Explain reasoning**: Explain why changes are needed
- **Acknowledge good work**: Recognize well-written code

**For Authors:**

- **Respond promptly**: Address feedback in a timely manner
- **Explain decisions**: Clarify design choices when asked
- **Be open to feedback**: Consider all suggestions constructively
- **Update PR**: Mark conversations as resolved when fixed

### 2. Review Criteria

**Code Quality:**
- Follows coding standards
- Clear and readable
- Well-documented
- Proper error handling

**Functionality:**
- Works as intended
- Handles edge cases
- Performance considerations
- Security implications

**Testing:**
- Adequate test coverage
- Tests are meaningful
- No test failures
- Integration tested if needed

**Documentation:**
- Updated where necessary
- Clear and accurate
- Examples provided if needed

### 3. Approval Process

- **One approval required** for minor changes
- **Two approvals required** for major changes
- **Maintainer approval required** for breaking changes
- **Security review required** for security-related changes

## Release Process

### 1. Version Management

We use [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### 2. Release Checklist

**Before release:**
- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] Version number updated
- [ ] Security review completed (if needed)

**Release process:**
1. Create release branch
2. Update version numbers
3. Update CHANGELOG
4. Tag the release
5. Deploy to production
6. Monitor for issues

### 3. CHANGELOG Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2024-02-15

### Added
- Rate limiting for API endpoints
- Support for custom SQL validation rules
- Performance monitoring dashboard

### Changed
- Improved error messages for better UX
- Updated Ollama model to latest version
- Refactored schema caching for better performance

### Fixed
- Fixed SQL generation for complex JOIN queries
- Resolved memory leak in long-running processes
- Fixed timezone handling in timestamp queries

### Security
- Enhanced SQL injection detection
- Added input sanitization for user queries
- Improved logging for security events

## [1.1.0] - 2024-01-30

### Added
- Initial release of Chat with SQL system
- Natural language to SQL conversion
- RAG-based schema retrieval
- SQL safety validation
- REST API interface
```

## Community Guidelines

### 1. Communication Channels

- **GitHub Issues**: https://github.com/adityatiwari12/TalkwithDB/issues
- **GitHub Discussions**: https://github.com/adityatiwari12/TalkwithDB/discussions

### 2. Asking for Help

When asking for help:

1. **Search first**: Check existing issues and documentation
2. **Be specific**: Provide clear details about your problem
3. **Include context**: Share relevant code and error messages
4. **Show what you tried**: Explain what you've already attempted
5. **Be patient**: Community members volunteer their time

### 3. Helping Others

Ways to contribute:

- **Answer questions**: Help in discussions and issues
- **Review PRs**: Provide code reviews
- **Write documentation**: Improve project documentation
- **Report bugs**: File detailed bug reports
- **Share ideas**: Suggest improvements and new features

## Recognition

### 1. Contributor Recognition

We recognize contributions through:

- **Contributors list**: All contributors listed in README
- **Release notes**: Contributors mentioned in changelog
- **Community highlights**: Outstanding contributors featured
- **Annual awards**: Recognition for significant contributions

### 2. Types of Contributions

All contributions are valued:

- **Code**: New features, bug fixes, performance improvements
- **Documentation**: Guides, tutorials, API docs
- **Design**: UI/UX improvements, graphics
- **Testing**: Test cases, bug reports, quality assurance
- **Community**: Support, outreach, evangelism

## Getting Help

If you need help with contributing:

1. **Read this guide**: Review the relevant sections
2. **Check existing issues**: Look for similar problems
3. **Ask in discussions**: Post questions at https://github.com/adityatiwari12/TalkwithDB/discussions
4. **Contact maintainers**: Reach out via GitHub issues
5. **Join community**: Participate in discussions and issues

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to Chat with SQL! Your contributions help make this project better for everyone. 🚀
