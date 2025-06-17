# MinIO Migration Guide

This document outlines the migration from Google Cloud Storage (GCS) to MinIO (S3-compatible storage) for the OMI backend.

## Summary of Changes

The migration replaces Google Cloud Storage with MinIO, an S3-compatible object storage solution. This change provides better self-hosting capabilities and reduces dependency on Google Cloud services.

## Files Modified

### 1. `requirements.txt`
- **Added**: `boto3>=1.34.0` - AWS SDK for Python, used to interact with S3-compatible services

### 2. `.env.template`
- **Removed**: All `BUCKET_*` environment variables
- **Removed**: `SERVICE_ACCOUNT_JSON` (no longer needed for storage)
- **Added**: New S3/MinIO configuration variables:
  - `S3_ENDPOINT_URL`: The URL of your MinIO server (e.g., `http://localhost:9000`)
  - `S3_ACCESS_KEY_ID`: Your MinIO access key
  - `S3_SECRET_ACCESS_KEY`: Your MinIO secret key
  - `S3_BUCKET_NAME`: The name of the single bucket (e.g., `omi-data`)

### 3. `utils/other/storage.py` (Complete Rewrite)
This file was completely rewritten to use boto3 instead of google-cloud-storage:

#### Client Initialization
- **Before**: Google Cloud Storage client with service account authentication
- **After**: boto3 S3 client configured for MinIO endpoint

#### Storage Organization
- **Before**: Multiple buckets for different purposes
- **After**: Single bucket with organized prefixes:
  - `speech-profiles/` - User speech profiles and additional recordings
  - `postprocessing/` - Post-processing audio files
  - `memories-recordings/` - Conversation recordings
  - `temporal-sync/` - Temporary sync files
  - `app-logos/` - Application logos
  - `app-thumbnails/` - Application thumbnails
  - `chat-files/` - Chat file uploads

#### Function Changes
All functions were rewritten to use S3 operations:

**Upload Operations**: 
- `bucket.blob(path).upload_from_filename()` → `s3_client.upload_file()`

**Download Operations**:
- `blob.download_to_filename()` → `s3_client.download_file()`

**Existence Checks**:
- `blob.exists()` → `s3_client.head_object()` with exception handling

**Delete Operations**:
- `blob.delete()` → `s3_client.delete_object()`

**List Operations**:
- `bucket.list_blobs()` → `s3_client.list_objects_v2()`

**Signed URLs**:
- `blob.generate_signed_url()` → `s3_client.generate_presigned_url()`

#### URL Format Changes
- **Before**: `https://storage.googleapis.com/{bucket}/{path}`
- **After**: `{S3_ENDPOINT_URL}/{S3_BUCKET_NAME}/{object_key}`

## Migration Steps

### 1. Set Up MinIO Server
1. Install and configure MinIO server
2. Create a bucket (e.g., `omi-data`)
3. Create access credentials

### 2. Update Environment Configuration
Update your `.env` file with the new S3/MinIO variables:
```bash
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY_ID=your_minio_access_key
S3_SECRET_ACCESS_KEY=your_minio_secret_key
S3_BUCKET_NAME=omi-data
```

### 3. Install Dependencies
```bash
pip install boto3>=1.34.0
```

### 4. Data Migration (Optional)
If you have existing data in Google Cloud Storage, you'll need to migrate it to MinIO:
1. Download data from GCS
2. Upload to MinIO using the new folder structure
3. Update any stored URLs in your database

### 5. Update Deployment Configuration
Remove old bucket-related environment variables from your deployment scripts and add the new S3/MinIO variables.

## Key Benefits

1. **Self-Hosting**: No dependency on Google Cloud Storage
2. **S3 Compatibility**: Can easily switch to AWS S3 or other S3-compatible services
3. **Cost Control**: Better control over storage costs
4. **Simplified Configuration**: Single bucket with organized prefixes instead of multiple buckets

## Testing

After migration, test all storage-related operations:
- Speech profile uploads/downloads
- Memory recordings
- App logo/thumbnail operations
- Chat file uploads
- Signed URL generation

## Rollback Plan

If issues arise, you can rollback by:
1. Reverting the code changes
2. Restoring the old environment variables
3. Ensuring Google Cloud Storage credentials are available

## Performance Considerations

- MinIO generally offers better performance for self-hosted deployments
- Ensure adequate network bandwidth between your application and MinIO server
- Consider using MinIO clustering for high availability

## Security Notes

- Store MinIO credentials securely
- Use HTTPS for MinIO endpoints in production
- Implement proper bucket policies and access controls
- Consider encryption at rest for sensitive data
