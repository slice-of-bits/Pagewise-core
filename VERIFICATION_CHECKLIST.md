# Verification Checklist for Rename

This checklist helps verify that the rename was completed successfully.

## ✅ Completed Changes

### Directory Structure
- [x] `groups/` renamed to `ponds/`
- [x] `pagewise/` renamed to `docpond/`
- [x] Git history preserved with `git mv`

### Code Files - ponds app
- [x] `ponds/models.py`: Group → Pond, GroupShare → PondShare
- [x] `ponds/schemas.py`: All schema classes renamed
- [x] `ponds/api.py`: All endpoint functions renamed
- [x] `ponds/admin.py`: Admin classes renamed
- [x] `ponds/tests.py`: Test classes and data updated
- [x] `ponds/apps.py`: App config renamed to PondsConfig

### Code Files - docpond project
- [x] `docpond/settings.py`: Updated INSTALLED_APPS, ROOT_URLCONF, WSGI_APPLICATION
- [x] `docpond/urls.py`: Updated docstring
- [x] `docpond/wsgi.py`: Updated settings module reference
- [x] `docpond/asgi.py`: Updated settings module reference
- [x] `docpond/celery.py`: Updated settings module and app name
- [x] `docpond/api.py`: Updated API title, router, and health check
- [x] `docpond/models.py`: Updated imports

### Code Files - documents app
- [x] `documents/models.py`: group → pond in foreign keys
- [x] `documents/api.py`: Updated imports and references
- [x] `documents/schemas.py`: group_sqid → pond_sqid, group_name → pond_name
- [x] `documents/tests.py`: Updated imports and test data

### Code Files - bucket app
- [x] `bucket/models.py`: Updated imports

### Code Files - root
- [x] `manage.py`: Updated DJANGO_SETTINGS_MODULE

### Configuration Files
- [x] `pyproject.toml`: Project name updated
- [x] `docker-compose.yml`: Database name updated

### Documentation
- [x] `README.md`: All references updated
- [x] `DOCLING_INTEGRATION.md`: Project name and parameters updated
- [x] `DEEPSEEK_OCR_INTEGRATION.md`: Project name and parameters updated
- [x] `RENAME_SUMMARY.md`: Comprehensive documentation created

### Database Migrations
- [x] `ponds/migrations/0002_rename_groups_to_ponds.py`: Created
- [x] `documents/migrations/0010_rename_group_to_pond.py`: Created

### Quality Checks
- [x] Python syntax validation: All files compile successfully
- [x] Code review: No issues found
- [x] Security scan: No vulnerabilities found
- [x] Import verification: No remaining old imports

## 🔄 Next Steps for Deployment

1. **Backup Database** (if deploying to existing database)
   ```bash
   pg_dump dbname > backup_before_rename.sql
   ```

2. **Run Migrations**
   ```bash
   python manage.py migrate ponds
   python manage.py migrate documents
   ```

3. **Verify Data Integrity**
   ```bash
   python manage.py shell
   >>> from ponds.models import Pond, PondShare
   >>> Pond.objects.count()  # Should match old Group count
   >>> PondShare.objects.count()  # Should match old GroupShare count
   ```

4. **Test API Endpoints**
   - `GET /api/ponds/` - List all ponds
   - `POST /api/ponds/` - Create a new pond
   - `GET /api/health` - Check health endpoint message

5. **Update Environment Variables** (if needed)
   - `AWS_STORAGE_BUCKET_NAME=docpond-documents`
   - Any custom settings referencing old names

6. **Update Client Applications**
   - API endpoints: `/api/groups/` → `/api/ponds/`
   - Request parameters: `group_sqid` → `pond_sqid`
   - Response fields: Similar updates needed

7. **Restart Services**
   ```bash
   # Django application
   python manage.py runserver
   
   # Celery workers
   celery -A docpond worker --loglevel=info
   ```

## 🚀 Testing Recommendations

### Unit Tests
```bash
python manage.py test ponds
python manage.py test documents
python manage.py test bucket
```

### Integration Tests
1. Create a pond via API
2. Create a document referencing the pond
3. Create a pond share
4. Access public share endpoint
5. Search documents by pond name
6. Upload and process a document

### Manual Testing
1. Access Django admin at `/admin/`
2. Verify Ponds section appears
3. Create/edit/delete ponds
4. Create/edit/delete pond shares
5. Verify documents still show pond relationships

## 📊 Impact Summary

- **Breaking Changes**: API endpoint URLs changed from `/api/groups/` to `/api/ponds/`
- **Database**: Seamless migration with data preservation
- **Backwards Compatibility**: Historical migrations reference old names (expected)
- **Client Updates Required**: Yes - API endpoints and parameter names changed

## ✔️ Success Criteria

All of these should be true after deployment:
- [ ] Migrations run without errors
- [ ] All existing data is accessible
- [ ] API endpoints respond correctly
- [ ] Admin interface shows ponds instead of groups
- [ ] Document uploads work with pond references
- [ ] Search functionality works with pond filtering
- [ ] Celery tasks execute successfully
- [ ] No import errors in logs
