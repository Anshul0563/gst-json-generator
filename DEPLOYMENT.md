# GST JSON Generator Pro - Deployment Guide

## Production Deployment Steps

### Local Development

```bash
# 1. Clone repository
git clone https://github.com/Anshul0563/gst-json-generator-pro.git
cd gst-json-generator-pro

# 2. Activate venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run tests
python3 integration_test.py
python3 test_validation.py

# 5. Start application
python3 main.py
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project
COPY . .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Create output directories
RUN mkdir -p logs output test_output

# Run application
CMD ["python3", "main.py"]
```

### Docker Compose (For future backend)

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./output:/app/output
      - ./logs:/app/logs
    environment:
      - OUTPUT_DIR=/app/output
      - LOG_FILE=/app/logs/app.log

  # For future MongoDB integration
  # mongodb:
  #   image: mongo:5.0
  #   ports:
  #     - "27017:27017"
  #   volumes:
  #     - mongodb_data:/data/db
  #   
  # volumes:
  #   mongodb_data:
```

### Linux Service (systemd)

```ini
# /etc/systemd/system/gst-generator.service
[Unit]
Description=GST JSON Generator Pro
After=network.target

[Service]
Type=simple
User=gst-user
WorkingDirectory=/home/gst-user/gst-json-generator-pro
Environment="PATH=/home/gst-user/gst-json-generator-pro/venv/bin"
ExecStart=/home/gst-user/gst-json-generator-pro/venv/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable gst-generator
sudo systemctl start gst-generator
sudo systemctl status gst-generator
```

### Render Deployment

Create `render.yaml`:
```yaml
services:
  - type: web
    name: gst-generator
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: python3 main.py
    envVars:
      - key: OUTPUT_DIR
        value: ./output
      - key: LOG_FILE
        value: ./logs/app.log
```

Push to GitHub and connect Render.

### AWS EC2 Deployment

```bash
# 1. SSH into instance
ssh -i key.pem ec2-user@your-instance-ip

# 2. Install Python
sudo yum install python3 python3-venv python3-pip -y

# 3. Clone repo
git clone https://github.com/Anshul0563/gst-json-generator-pro.git
cd gst-json-generator-pro

# 4. Create venv and install
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Run with nohup
nohup python3 main.py > app.log 2>&1 &

# 6. Monitor
tail -f app.log
```

### Railway Deployment

1. Push to GitHub
2. Connect GitHub repo to Railway
3. Add environment variables in Railway dashboard:
   ```
   OUTPUT_DIR=./output
   LOG_FILE=./logs/app.log
   ```
4. Set start command: `python3 main.py`

### DigitalOcean App Platform

1. Create new app
2. Connect GitHub repo
3. Configure environment:
   ```
   OUTPUT_DIR=/app/output
   LOG_FILE=/app/logs/app.log
   ```
4. Set build command: `pip install -r requirements.txt`
5. Set run command: `python3 main.py`

---

## Production Checklist

### Pre-Deployment
- [ ] All tests passing locally
- [ ] Update version in main.py and config.py
- [ ] Update CHANGELOG.md
- [ ] Test with real marketplace data
- [ ] Security scan (bandit, safety)
- [ ] Performance test with large files
- [ ] Documentation updated

### Configuration
- [ ] Create .env from .env.example
- [ ] Set appropriate LOG_LEVEL
- [ ] Configure OUTPUT_DIR path
- [ ] Set MAX_FILE_SIZE_MB for server
- [ ] Configure CACHE settings

### Security
- [ ] No hardcoded credentials
- [ ] HTTPS enabled (if web)
- [ ] CORS properly configured
- [ ] Input validation enabled
- [ ] Rate limiting enabled (if API)

### Monitoring
- [ ] Logging to file configured
- [ ] Error alerts setup
- [ ] Performance monitoring enabled
- [ ] Backup strategy defined
- [ ] Log rotation configured

### Maintenance
- [ ] Regular backups of output files
- [ ] Log cleanup schedule
- [ ] Dependency update schedule
- [ ] Database cleanup (if used)
- [ ] User activity audit trail

---

## Performance Optimization

### For Large Files (>100MB)

```python
# In config.json
{
  "parser": {
    "chunk_size": 10000,
    "max_rows": 500000
  },
  "output": {
    "batch_write": true,
    "batch_size": 5000
  }
}
```

### Memory Optimization

```bash
# Increase Python memory limit
python3 -X dev main.py

# Or set ulimit
ulimit -v 2097152  # 2GB
```

### Caching Strategy

```python
# Enable aggressive caching
{
  "cache": {
    "enabled": true,
    "ttl": 7200,  # 2 hours
    "max_size_mb": 500
  }
}
```

---

## Troubleshooting Production

### Memory Issues
```bash
# Monitor memory usage
top -p $(pgrep -f "python3 main.py")

# If OOM, reduce batch_size in config.json
```

### Slow Processing
```bash
# Enable DEBUG logging
export LOG_LEVEL=DEBUG
python3 main.py

# Check logs for bottlenecks
tail -100f logs/app.log | grep PERF
```

### File Access Issues
```bash
# Ensure output directory exists
mkdir -p /var/gst-generator/output
chmod 755 /var/gst-generator/output

# Update config.json
"output_dir": "/var/gst-generator/output"
```

---

## Backup & Recovery

### Backup Strategy

```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="/backups/gst-generator"
mkdir -p $BACKUP_DIR

# Backup output files
tar -czf $BACKUP_DIR/output-$(date +%Y%m%d).tar.gz output/

# Backup logs
tar -czf $BACKUP_DIR/logs-$(date +%Y%m%d).tar.gz logs/

# Backup config
cp config.json $BACKUP_DIR/config-$(date +%Y%m%d).json

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### Recovery Procedure

```bash
# Restore from backup
tar -xzf /backups/gst-generator/output-20240419.tar.gz -C /

# Restart service
sudo systemctl restart gst-generator
```

---

## Update Procedure

```bash
# 1. Stop service
sudo systemctl stop gst-generator

# 2. Backup current version
cp -r gst-json-generator-pro gst-json-generator-pro.backup

# 3. Update code
cd gst-json-generator-pro
git pull origin main

# 4. Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# 5. Run tests
python3 test_validation.py

# 6. Restart service
sudo systemctl start gst-generator

# 7. Verify
sudo systemctl status gst-generator
```

---

## Monitoring & Alerts

### Log Monitoring

```bash
# Watch logs in real-time
tail -f logs/app.log | grep ERROR

# Count errors by hour
cat logs/app.log | grep ERROR | awk '{print $1, $2}' | uniq -c
```

### Performance Monitoring

```bash
# Check processing speed
grep "PERF:" logs/app.log | tail -10

# Parse for slowness
awk '/PERF/ && $NF > 30 {print}' logs/app.log
```

### Alerting (with sendmail)

```bash
#!/bin/bash
# monitor.sh
if grep -q "ERROR" logs/app.log.new; then
    mail -s "GST Generator Error Alert" admin@example.com < logs/app.log.new
fi
```

---

## Scalability Notes

### Current Limitations
- Single-threaded processing
- In-memory file loading
- No distributed processing

### Future Improvements
1. **Multi-threading**: Process multiple files concurrently
2. **Streaming**: Process files in chunks without loading fully
3. **Queue System**: Background job queue (Celery + Redis)
4. **Database**: Store results for history and analytics
5. **API**: REST API for programmatic access
6. **Load Balancing**: Multiple instances with load balancer

---

## Security Hardening

### File Upload Validation
```python
# Validate uploaded files
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
ALLOWED_EXTENSIONS = {'.xlsx', '.xls', '.csv'}
```

### Path Traversal Prevention
```python
# Ensure files are in allowed directory
import os
file_path = os.path.abspath(user_input)
allowed_dir = os.path.abspath('./uploads')
assert file_path.startswith(allowed_dir)
```

### Input Sanitization
```python
# Sanitize GSTIN input
import re
gstin = re.sub(r'[^A-Z0-9]', '', gstin.upper())
assert len(gstin) == 15
```

---

## Compliance & Audit

### Data Retention
- Keep generated JSONs for 6 months minimum
- Archive older files after 1 year
- Comply with GST record retention (5 years)

### Audit Logging
- Log all file uploads and generations
- Track user actions (for future multi-user)
- Store GSTIN and period for each generation

### Privacy
- No sensitive data in logs
- Encrypted file storage (for future)
- Secure backup procedures

---

## Version History

### v2.0.0 (Current)
- ✅ Production ready
- ✅ All platforms tested
- ✅ Comprehensive documentation

### v1.0.0
- Initial release

---

## Support & Maintenance

For issues or questions:
- GitHub Issues: https://github.com/Anshul0563/gst-json-generator-pro/issues
- Email: anshul@example.com
- Documentation: README.md and DEBUG_REPORT.md

---

Last Updated: April 19, 2026
Production Status: Ready for Deployment ✅
