# Release Checklist

## Pre-Release Verification

### Code Quality
- [ ] All tests pass locally (`pytest`)
- [ ] All tests pass in CI/CD pipeline
- [ ] No linting errors (`ruff check .`)
- [ ] Code is properly formatted (`ruff format --check .`)
- [ ] Type checking passes (`mypy services/`)
- [ ] No security issues detected (`bandit -r services/`)
- [ ] Pre-commit hooks pass (`pre-commit run --all-files`)

### Testing
- [ ] Unit tests cover new functionality
- [ ] Integration tests pass
- [ ] Schemathesis property-based tests pass
- [ ] Manual testing completed for critical paths
- [ ] Rate limiting tested with Redis
- [ ] Authentication/authorization flows verified
- [ ] Database migrations tested (up and down)

### Documentation
- [ ] CHANGELOG.md updated with release notes
- [ ] README.md reflects current features
- [ ] API documentation is up to date
- [ ] Environment variables documented
- [ ] Breaking changes clearly documented
- [ ] Migration guide provided (if needed)

### Dependencies
- [ ] All dependencies up to date (check `pyproject.toml`)
- [ ] Security vulnerabilities checked (`pip-audit` or similar)
- [ ] Dependency licenses reviewed
- [ ] Docker base images updated
- [ ] Frontend dependencies updated (`npm outdated`)

### Configuration
- [ ] Environment variables validated
- [ ] Docker Compose configuration tested
- [ ] Rate limit configurations reviewed
- [ ] Redis configuration verified
- [ ] Database connection settings confirmed
- [ ] Secrets/credentials properly managed

## Release Process

### Version Bump
- [ ] Update version in `pyproject.toml`
- [ ] Update version in relevant service configs
- [ ] Version follows semantic versioning (MAJOR.MINOR.PATCH)

### Git Operations
- [ ] All changes committed
- [ ] Working directory is clean (`git status`)
- [ ] On correct branch (usually `main`)
- [ ] Pull latest changes (`git pull origin main`)
- [ ] Create release branch (optional: `git checkout -b release/vX.Y.Z`)

### Tagging
- [ ] Create annotated tag (`git tag -a vX.Y.Z -m "Release vX.Y.Z"`)
- [ ] Push tag to remote (`git push origin vX.Y.Z`)
- [ ] Tag matches version in `pyproject.toml`

### Build & Deploy
- [ ] Docker images build successfully
- [ ] Docker images tagged with version
- [ ] Docker images pushed to registry
- [ ] Deployment to staging environment successful
- [ ] Smoke tests on staging pass
- [ ] Deployment to production environment
- [ ] Database migrations applied (if needed)
- [ ] Worker service restarted (if needed)

## Post-Release Verification

### Functional Testing
- [ ] Health endpoint responds (`/health`)
- [ ] Authentication works (login/logout)
- [ ] Core API endpoints functional
- [ ] Rate limiting enforced correctly
- [ ] Worker jobs processing correctly
- [ ] Database queries performing well
- [ ] Redis connections stable

### Monitoring
- [ ] Application logs reviewed (no critical errors)
- [ ] Performance metrics within normal range
- [ ] Error rate acceptable
- [ ] Response times acceptable
- [ ] Memory usage stable
- [ ] CPU usage stable
- [ ] Logfire/monitoring dashboards reviewed

### Communication
- [ ] Release notes published (GitHub Releases)
- [ ] Stakeholders notified
- [ ] Documentation site updated (if applicable)
- [ ] Team notified in communication channels
- [ ] Known issues documented

### Rollback Plan
- [ ] Rollback procedure documented
- [ ] Previous version Docker images available
- [ ] Database rollback scripts tested (if schema changed)
- [ ] Rollback decision criteria defined

## Post-Release Cleanup

- [ ] Close related issues on GitHub
- [ ] Update project board/kanban
- [ ] Archive release branch (if used)
- [ ] Schedule retrospective (if major release)
- [ ] Update roadmap/milestones

## Emergency Rollback Procedure

If critical issues are discovered:

1. [ ] Stop deployment immediately
2. [ ] Assess impact and severity
3. [ ] Decision: hotfix or rollback?
4. [ ] If rollback:
   - [ ] Deploy previous Docker image version
   - [ ] Revert database migrations (if needed)
   - [ ] Verify system stability
   - [ ] Communicate rollback to stakeholders
5. [ ] If hotfix:
   - [ ] Create hotfix branch from tag
   - [ ] Implement minimal fix
   - [ ] Fast-track through testing
   - [ ] Deploy hotfix
   - [ ] Create new patch version tag

## Notes

- Always perform releases during low-traffic periods
- Have at least two team members available during deployment
- Keep communication channels open during release
- Monitor systems closely for first 24 hours post-release
- Document any deviations from this checklist
